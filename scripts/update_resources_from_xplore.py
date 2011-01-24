# Setup django.
import os
import sys
# NOTE: These must be absolute paths, since after daemonizing the process the working directory will change.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ------------------------------------------------------------------------------

import httplib
import urllib
import urllib2
import time
import datetime
import re
import getopt
import daemonize
from sets import Set

def log(msg):
    print >>sys.stdout, msg.encode('utf-8')
    
#@transaction.commit_manually
def main(*args):
    
    logfilename = None
    pidfilename = None
    use_processcontrol = True
    use_daemon = True
    xplore_hc = 5
    use_resume = False
    
    #print 'sys.argv[1:]: %r' % sys.argv[1:]
    
    opts, args = getopt.getopt(sys.argv[1:], '', [
        'log=',
        'pid=',
        'processcontrol=',
        'daemon=',
        'xplore_hc=',
        'path=',
        'resume=',
    ])
    
    def get_bool_arg(value):
        if value.lower() == 'true' or value.lower() == 'yes' or value.lower() == '1':
            return True
        elif value.lower() == 'false' or value.lower() == 'no' or value.lower() == '0':
            return False
        else:
            return None
    
    for name, value in opts:
        if name == '--log':
            logfilename = os.path.abspath(value)
        elif name == '--pid':
            pidfilename = os.path.abspath(value)
        elif name == '--processcontrol':
            temp = get_bool_arg(value)
            if temp is not None:
                use_processcontrol = temp
            else:
                raise Exception('Unknown value for --processcontrol %r, must be "true", "false", "yes", "no", 1, or 0' % value)
        elif name == '--daemon':
            temp = get_bool_arg(value)
            if temp is not None:
                use_daemon = temp
            else:
                raise Exception('Unknown value for --daemon %r, must be "true", "false", "yes", "no", 1, or 0' % value)
        elif name == '--xplore_hc':
            try:
                xplore_hc = int(value)
            except ValueError:
                raise Exception('Unknown value for --xplore_hc %r, must be a positive integer.' % value) 
        elif name == '--path':
            # NOTE: It looks like daemons don't inherit the environment of the spawning WSGI process?
            # Add all paths in the --path arg to the current sys.path.
            paths = value.split(':')
            for path in paths:
                print 'Got path %r' % path
                if path not in sys.path:
                    sys.path.insert(0, path)
                    print 'Inserting path %r' % path
        elif name == '--resume':
            temp = get_bool_arg(value)
            if temp is not None:
                use_resume = temp
            else:
                raise Exception('Unknown value for --resume %r, must be "true", "false", "yes", "no", 1, or 0' % value)
        else:
            raise Exception('Unknown argument %r' % name)
    
    if len(args) > 0:
        raise Exception('Unknown arguments %r' % args)
    
    if use_resume and not use_processcontrol:
        raise Exception('Cannot use --resume when --processcontrol is false.')
    
    # NOTE: setup django import here, since we may have added more paths to sys.path.
    import ieeetags.settings
    from django.core.management import setup_environ
    setup_environ(ieeetags.settings)
    
    # Now our django imports.
    from ieeetags import models
    from ieeetags.models import ResourceType
    
    print 'logfilename: %r' % logfilename
    print 'use_processcontrol: %r' % use_processcontrol
    print 'pidfilename: %r' % pidfilename
    
    if logfilename is not None:
        # NOTE: Overwrites existing file.
        logfile = open(logfilename, 'w', 0)
        print >>logfile, '----------------------------------------'
    else:
        logfile = None
    
    #if pidfilename is not None:
    #    from lockfile.pidlockfile import PIDLockFile
    #    pidfile = PIDLockFile(pidfilename)
    #else:
    #    pidfile = None
    
    log('logging started.')
    
    if use_daemon:
        log('Starting daemon.')
        daemonize.daemonize(stdout=logfile, stderr=logfile, pidfilename=pidfilename, exclude_files=[logfile.fileno()])
    else:
        log('Running as non-daemon.')
    
    try:
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
                'relationships_to_periodicals_created' : 0,
                'relationships_to_conferences_created' : 0,
                'relationships_to_standards_created' : 0,
                'society_relationships_created' : 0,
                'resources_not_found' : 0
            }
            
            now = datetime.datetime.now()
                
            resSum = XploreUpdateResultsSummary
            
            log('Import Xplore Results into Resource')
            log('Started at %s' % now)
            
            resource_type = models.ResourceType.objects.getFromName('periodical')
            tag_type = models.NodeType.objects.getFromName('tag')
            
            tags = models.Node.objects.filter(node_type=tag_type).order_by('name')
            
            if use_resume:
                # Filter out all tags up to and including the last processed tag so we can resume where we left off.
                process_control = models.ProcessControl.objects.get(type=models.PROCESS_CONTROL_TYPES.XPLORE_IMPORT)
                last_processed_tag = process_control.last_processed_tag
                
                log('Resuming from tag %r.' % last_processed_tag.name)
                
                assert last_processed_tag is not None, 'Trying to resume, but last_processed_tag (%r) is None.' % last_processed_tag
                
                old_tags_count = tags.count()
                tags = tags.filter(name__gt=last_processed_tag.name)
                new_tags_count = tags.count()
                log('  Found %s tags (filtered out %s).' % (new_tags_count, old_tags_count - new_tags_count))
            
            num_tags = tags.count()
            
            last_updated = None
            last_tag = None
            society_set = None
            
            for i, tag in enumerate(tags):
                if use_processcontrol:
                    # Update the log.
                    process_control = models.ProcessControl.objects.get(type=models.PROCESS_CONTROL_TYPES.XPLORE_IMPORT)
                    
                    # Update the 'Processing...' log every 1 seconds.
                    if last_updated is None or datetime.datetime.now() - last_updated > datetime.timedelta(seconds=1):
                        process_control.log = re.sub(r'(?m)^Processing tag .+\n', '', process_control.log)
                        process_control.log += 'Processing tag %r (%s/%s).\n' % (tag.name, i, num_tags)
                        last_updated = datetime.datetime.now()
                        
                    if last_tag is not None:
                        # Record the last-updated tag name, in case we want to resume.
                        process_control.last_processed_tag = last_tag
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
                    'hc': xplore_hc,
                    # NOTE: Must UTF8 encode here, otherwise urlencode() fails with non-ASCII names.
                    'md': tag.name.encode('utf-8')
                })
                log('Calling %s' % xplore_query_url)
                try:
                    file = urllib2.urlopen(xplore_query_url)
                except (urllib2.URLError, httplib.BadStatusLine):
                    log('Could not connect to the IEEE Xplore site to perform search.')
                    resSum['xplore_connection_errors'] += 1
                    continue
                else:
                    
                    from xml.dom.minidom import parseString
                    
                    errors = []
                    
                    # Need to correctly handle UTF8 responses from urlopen() above, avoid UnicodeEncodeError.
                    encoding = file.headers['content-type'].split('charset=')[-1]
                    ucontents = unicode(file.read(), encoding)
                    dom1 = parseString(ucontents.encode('utf-8'))
                    
                    xhits = dom1.documentElement.getElementsByTagName('document')
                    distinct_issns = {}
                    distinct_conference_punumbers = {}
                    for i, xhit in enumerate(xhits):
                        xhit_title = xhit.getElementsByTagName('title')[0].firstChild.nodeValue
                        xhit_pubtype = xhit.getElementsByTagName('pubtype')[0].firstChild.nodeValue
                        
                        if xhit_pubtype == "Journals":
                            issn = xhit.getElementsByTagName('issn')
                            
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
                        elif xhit_pubtype == "Conferences":
                            punumber = xhit.getElementsByTagName('punumber')
                            
                            if not len(punumber):
                                try:
                                    log('No punumber node found in Xplore result with title "%s"' % xhit_title)
                                    resSum['xplore_hits_without_id'] += 1
                                except UnicodeEncodeError, e:
                                    log('No punumber node found in Xplore result with UNPRINTABLE TITLE. See error.')
                                    log(e)
                                    continue
                            elif not punumber[0].firstChild.nodeValue in distinct_conference_punumbers:
                                distinct_conference_punumbers[punumber[0].firstChild.nodeValue] = xhit_title
                        elif xhit_pubtype == "Standards":
                            punumber = xhit.getElementsByTagName('punumber')
                            
                            if not len(punumber):
                                try:
                                    log('No punumber node found in Xplore result with title "%s"' % xhit_title)
                                    resSum['xplore_hits_without_id'] += 1
                                except UnicodeEncodeError, e:
                                    log('No punumber node found in Xplore result with UNPRINTABLE TITLE. See error.')
                                    log(e)
                                    continue
                            elif not punumber[0].firstChild.nodeValue in distinct_standard_punumbers:
                                distinct_standar_punumbers[punumber[0].firstChild.nodeValue] = xhit_title 
                    
                    log("Found %d unique ISSNs:" % len(distinct_issns))
                    for issn, xhit_title in distinct_issns.iteritems():
                        try:
                            log('%s: "%s"' % (issn, xhit_title))
                            pass
                        except UnicodeEncodeError, e:
                            log(e)
                            continue
                        
                    log("Found %d unique PU Numbers for Conferences:" % len(distinct_conference_punumbers))
                    for punumber, xhit_title in distinct_conference_punumbers.iteritems():
                        try:
                            log('%s: "%s"' % (punumber, xhit_title))
                            pass
                        except UnicodeEncodeError, e:
                            log(e)
                            continue
                        
                    log("Found %d unique PU Numbers for Standards:" % len(distinct_standard_punumbers))
                    for punumber, xhit_title in distinct_standard_punumbers.iteritems():
                        try:
                            log('%s: "%s"' % (punumber, xhit_title))
                            pass
                        except UnicodeEncodeError, e:
                            log(e)
                            continue
                    
                    # Create a unique set of the resources' related societies    
                    society_set = Set()
                    log("Looking for matching TechNav Resources...")
                    
                    # Iterate thru PERIODICALS creating a relationship to the current tag if non-existent.
                    for issn, xhit_title in distinct_issns.iteritems():
                        try:
                            per = models.Resource.objects.get(ieee_id=issn)
                            log('%s: Found TechNav Resource titled "%s".' % (issn, per.name))
                            
                            if per in tag.resources.all():
                                log('Relationship already exists.')
                                resSum['existing_relationship_count'] += 1
                            else:
                                log('*** Creating relationship to Periodical.')
                                resSum['relationships_to_periodicals_created'] += 1
                                xref = models.ResourceNodes(
                                    node = tag,
                                    resource = per,
                                    date_created = now,
                                    is_machine_generated = True
                                )
                                xref.save()
                            
                            for society in per.societies.iterator():
                                society_set.add(society)
                                
                        except models.Resource.DoesNotExist:
                            log('%s: No TechNav Resource found.' % issn)
                            resSum['resources_not_found'] += 1\
                            
                    # Iterate thru CONFERENCES creating a relationship to the current tag if non-existent.
                    for punumber, xhit_title in distinct_conference_punumbers.iteritems():
                        try:
                            conf = models.Resource.objects.get(pub_id=punumber, resource_type__name=ResourceType.CONFERENCE)
                            log('%s: Found TechNav Resource titled "%s".' % (punumber, conf.name))
                            
                            if conf in tag.resources.all():
                                log('Relationship already exists.')
                                resSum['existing_relationship_count'] += 1
                            else:
                                log('*** Creating relationship to Conference.')
                                resSum['relationships_to_conferences_created'] += 1
                                xref = models.ResourceNodes(
                                    node = tag,
                                    resource = conf,
                                    date_created = now,
                                    is_machine_generated = True
                                )
                                xref.save()
                            
                            for society in conf.societies.iterator():
                                society_set.add(society)
                                
                        except models.Resource.DoesNotExist:
                            log('%s: No TechNav Resource found.' % punumber)
                            resSum['resources_not_found'] += 1
                            
                    # Iterate thru STANDARDS creating a relationship to the current tag if non-existent.
                    # NOTE: Yes, there is a lot of code duplication between this and the previous two blocks.
                    for punumber, xhit_title in distinct_standard_punumbers.iteritems():
                        try:
                            standard = models.Resource.objects.get(pub_id=punumber, resource_type__name=ResourceType.STANDARD)
                            log('%s: Found TechNav Resource titled "%s".' % (punumber, standard.name))
                            
                            if standard in tag.resources.all():
                                log('Relationship already exists.')
                                resSum['existing_relationship_count'] += 1
                            else:
                                log('*** Creating relationship to Standard.')
                                resSum['relationships_to_standards_created'] += 1
                                xref = models.ResourceNodes(
                                    node = tag,
                                    resource = standard,
                                    date_created = now,
                                    is_machine_generated = True
                                )
                                xref.save()
                            
                            for society in standard.societies.iterator():
                                society_set.add(society)
                                
                        except models.Resource.DoesNotExist:
                            log('%s: No TechNav Resource found.' % punumber)
                            resSum['resources_not_found'] += 1
                    
                
                # Loop thru all the unique societies and create relationships where they are missing.
                log("Found %d unique societ%s related to all resources." % (len(society_set), ('ies', 'y')[len(society_set) == 1]))
                for society in society_set:
                    log('Society: %s' % society.name)
                    if tag.societies.filter(id=society.id).count() == 0:
                        log('*** Creating relationship to Society.')
                        resSum['society_relationships_created'] += 1
                        xref = models.NodeSocieties(
                            node = tag,
                            society = society,
                            date_created = now,
                            is_machine_generated = True
                        )
                        xref.save()
                    else:
                        log('Relationship to society already exists.')
                    
                
                # TODO add finally block to close file once python is updated past 2.4
                
                last_tag = tag
                
            log('\nSummary:')
            log('Tags Processed: %d' % resSum['tags_processed'])
            
            log('Xplore Connection Errors: %d' % resSum['xplore_connection_errors'])
            log('Xplore Hits without IDs: %d' % resSum['xplore_hits_without_id'])
            log('Pre-existing Relationships: %d' % resSum['existing_relationship_count'])
            log('Relationships to Periodicals Created: %d' % resSum['relationships_to_periodicals_created'])
            log('Relationships to Conferences Created: %d' % resSum['relationships_to_conferences_created'])
            log('Xplore Hits with no Matching Technav Tag: %d' % resSum['resources_not_found'])
            
            # DEBUG: Don't really commit any changes till this script is more debugged.
            #transaction.rollback()
            
            if use_processcontrol:
                log('Updating model with exit status.')
                # Update the model to show that this has quit normally.
                process_control = models.ProcessControl.objects.get(type=models.PROCESS_CONTROL_TYPES.XPLORE_IMPORT)
                if last_tag is not None:
                    # Record the last-updated tag name, in case we want to resume.
                    process_control.last_processed_tag = last_tag
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
    
    finally:
        pass
    #return resSum

if __name__ == "__main__":
    sys.exit(main(*sys.argv))
    
