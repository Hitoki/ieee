# Setup django.
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import ieeetags.settings
from django.core.management import setup_environ
setup_environ(ieeetags.settings)

# ------------------------------------------------------------------------------

import httplib
import urllib
import urllib2
#from django.db import transaction
from ieeetags import models
import time
import datetime
import re
import daemon
import getopt

def log(msg):
    print >>sys.stdout, msg.encode('utf-8')
    
#@transaction.commit_manually
def main(*args):
    
    logfilename = None
    pidfilename = None
    use_processcontrol = True
    
    opts, args = getopt.getopt(sys.argv[1:], '', [
        'log=',
        'pid=',
        'processcontrol=',
    ])
    
    for name, value in opts:
        if name == '--log':
            logfilename = os.path.abspath(value)
        elif name == '--pid':
            pidfilename = os.path.abspath(value)
        elif name == '--processcontrol':
            if value.lower() == 'yes' or value.lower() == '1':
                use_processcontrol = True
            elif value.lower() == 'no' or value.lower() == '0':
                use_processcontrol = False
            else:
                raise Exception('Unknown value for --processcontrol %r, must be "yes", "no", 1, or 0' % value)
        else:
            raise Exception('Unknown argument %r' % name)
        
    if len(args) > 0:
        raise Exception('Unknown arguments %r' % args)
    
    print 'logfilename: %r' % logfilename
    print 'use_processcontrol: %r' % use_processcontrol
    print 'pidfilename: %r' % pidfilename
    
    if logfilename is not None:
        logfile = open(logfilename, 'w+', 0)
    else:
        logfile = None
    
    if pidfilename is not None:
        from lockfile.pidlockfile import PIDLockFile
        
        pidfile = PIDLockFile(pidfilename)
    else:
        pidfile = None
    
    log('logging started.')
    
    log('Starting daemon.')
    
    #if True:
    with daemon.DaemonContext(stdout=logfile, stderr=logfile, pidfile=pidfile):
        try:
            if use_processcontrol:
                # Update the log.
                process_control = models.ProcessControl.objects.get(type=models.PROCESS_CONTROL_TYPES.XPLORE_IMPORT)
                process_control.log += 'Started.\n'
                process_control.date_updated = datetime.datetime.now()
                process_control.save()
            
            XploreUpdateResultsSummary = {
                'tags_processed' : 0,
                'xplore_connection_errors' : 0,
                'xplore_hits_without_id' : 0,
                'existing_relationship_count' : 0,
                'relationships_created' : 0,
                'resources_not_found' : 0
            }
            
            now = datetime.datetime.now()
                
            resSum = XploreUpdateResultsSummary
            
            log('Import Xplore Results into Resource')
            log('Started at %s' % now)
            
            resource_type = models.ResourceType.objects.getFromName('periodical')
            node_type = models.NodeType.objects.getFromName('tag')
            
            # DEBUG:
            #tags = models.Node.objects.filter(node_type=node_type)[:5]
            tags = models.Node.objects.filter(node_type=node_type)
            
            num_tags = tags.count()
            
            last_updated = None
            
            for i, tag in enumerate(tags):
                if use_processcontrol:
                    # Update the log.
                    process_control = models.ProcessControl.objects.get(type=models.PROCESS_CONTROL_TYPES.XPLORE_IMPORT)
                    
                    # Update the 'Processing...' log every 10 seconds.
                    if last_updated is None or datetime.datetime.now() - last_updated > datetime.timedelta(seconds=10):
                        process_control.log = re.sub(r'(?m)^Processing tag .+\n', '', process_control.log)
                        process_control.log += 'Processing tag %r (%s/%s).\n' % (tag.name, i, num_tags)
                        last_updated = datetime.datetime.now()
                        
                    process_control.date_updated = datetime.datetime.now()
                    process_control.save()
                
                    if not process_control.is_alive:
                        # The database has signalled for this to quit now.
                        log('is_alive is false, quitting.')
                        break
                
                resSum['tags_processed'] += 1
                log('Querying Xplore for Tag: %s' % tag.name)
                xplore_query_url = 'http://xploreuat.ieee.org/gateway/ipsSearch.jsp?' + urllib.urlencode({
                    # Number of results
                    'hc': 5,
                    'md': tag.name,
                    'ctype' : 'Journals'
                })
                log('Calling %s' % xplore_query_url)
                try:
                    file = urllib2.urlopen(xplore_query_url)
                except (urllib2.URLError, httplib.BadStatusLine):
                    log('Could not connect to the IEEE Xplore site to perform search.')
                    resSum['xplore_connection_errors'] += 1
                    continue
                else:
                    from xml.dom.minidom import parse
                    errors = []
                    dom1 = parse(file)
                    xhits = dom1.documentElement.getElementsByTagName('document')
                    distinct_issns = {}
                    for i, xhit in enumerate(xhits):
                        issn = xhit.getElementsByTagName('issn')
                        xhit_title = xhit.getElementsByTagName('title')[0].firstChild.nodeValue
                        if not len(issn):
                            try:
                                log('No ISSN node found in Xplore result with title "%s"' % xhit_title)
                                resSum['xplore_hits_without_id'] += 1
                            except UnicodeEncodeError, e:
                                log('No ISSN node found in Xplore result with UNPRINTABLE TITLE. See error.')
                                log(e)
                                continue
                        elif not issn[0].firstChild.nodeValue in distinct_issns:
                            distinct_issns[issn[0].firstChild.nodeValue] = xhit_title
                    
                    log("Found %d unique ISSNs:" % len(distinct_issns))
                    for issn, xhit_title in distinct_issns.iteritems():
                        try:
                            log('%s: "%s"' % (issn, xhit_title))
                        except UnicodeEncodeError, e:
                            log(e)
                            continue
                    log("Looking for matching TechNav Resources...")
                    for issn, xhit_title in distinct_issns.iteritems():
                        try:
                            per = models.Resource.objects.get(ieee_id=issn)
                            log('%s: Found TechNav Resource titled "%s".' % (issn, per.name))
                            
                            if per in tag.resources.all():
                                log('Relationship already exists.')
                                resSum['existing_relationship_count'] += 1
                            else:
                                log('Creating relationship.')
                                resSum['relationships_created'] += 1
                                xref = ResourceNodes(
                                    node = tag,
                                    resource = per,
                                    date_created = now,
                                    is_machine_generated = True
                                )
                                xref.save()
                        except models.Resource.DoesNotExist:
                            log('%s: No TechNav Resource found.' % issn)
                            resSum['resources_not_found'] += 1
                
                # TODO add finally block to close file once python is updated past 2.4
                
                # DEBUG:
                #log('Quitting after one tag.')
                #break
                
            log('\nSummary:')
            log('Tags Processed: %d' % resSum['tags_processed'])
            
            log('Xplore Connection Errors: %d' % resSum['xplore_connection_errors'])
            log('Xplore Hits without IDs: %d' % resSum['xplore_hits_without_id'])
            log('Pre-existing Relationships: %d' % resSum['existing_relationship_count'])
            log('Relationships Created: %d' % resSum['relationships_created'])
            log('Xplore Hits with no Matching Technav Tag: %d' % resSum['resources_not_found'])
            
            # DEBUG: Don't really commit any changes till this script is more debugged.
            #transaction.rollback()
            
            if use_processcontrol:
                log('Updating model with exit status.')
                # Update the model to show that this has quit normally.
                process_control = models.ProcessControl.objects.get(type=models.PROCESS_CONTROL_TYPES.XPLORE_IMPORT)
                process_control.log += 'Quitting.\n'
                process_control.date_updated = datetime.datetime.now()
                process_control.save()
        
        except Exception, e:
            # Catch any errors that occurred in main(), write to stdout and save to DB.
            log('*****')
            log('Exception: %r' % e)
            log('Args: %s' % repr(e.args))
            
            import traceback
            traceback.print_exc()
            
            log('*****')
            
            try:
                if use_processcontrol:
                    # Attempt to update the DB with the error-exit state.
                    process_control = models.ProcessControl.objects.get(type=models.PROCESS_CONTROL_TYPES.XPLORE_IMPORT)
                    process_control.log += 'Exception: %s\n' % e
                    process_control.date_updated = datetime.datetime.now()
                    process_control.save()
            except Exception, e:
                pass
            
            #transaction.rollback()
        
        log('Done.')
        log('')
        log('')

    #return resSum

if __name__ == "__main__":
    sys.exit(main(*sys.argv))
    