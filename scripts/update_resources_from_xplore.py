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
from ieeetags.models import *
import time
import datetime
import re

#@transaction.commit_manually
def main(*args):
    
    use_logfile = True
    use_processcontrol = True
    for arg in args[1:]:
        if arg == 'stdout':
            use_logfile = False
        elif arg == 'no_processcontrol':
            use_processcontrol = False
        else:
            raise Exception('Unrecognized argument %r' % arg)

    if use_logfile:
        # Set stdout/stderr to a logfile in the current directory.
        root = os.path.dirname(__file__)
        logfilename = os.path.join(root, 'update_resources_from_xplore_%s.txt' % datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        logfile = open(logfilename, 'w+', 0)
        sys.stdout = logfile
        sys.stderr = logfile
        
        if use_processcontrol:
            # Update the log.
            process_control = ProcessControl.objects.get(type=PROCESS_CONTROL_TYPES.XPLORE_IMPORT)
            process_control.log += 'Logging to file "%s".\n' % logfilename
            process_control.date_updated = datetime.datetime.now()
            process_control.save()
    
    try:
        if use_processcontrol:
            # Update the log.
            process_control = ProcessControl.objects.get(type=PROCESS_CONTROL_TYPES.XPLORE_IMPORT)
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
        
        print 'Import Xplore Results into Resource'
        print 'Started at %s' % now
        
        resource_type = ResourceType.objects.getFromName('periodical')
        node_type = NodeType.objects.getFromName('tag')
        
        # DEBUG:
        #tags = Node.objects.filter(node_type=node_type)[:5]
        tags = Node.objects.filter(node_type=node_type)
        
        num_tags = tags.count()
        
        last_updated = None
        
        for i, tag in enumerate(tags):
            if use_processcontrol:
                # Update the log.
                process_control = ProcessControl.objects.get(type=PROCESS_CONTROL_TYPES.XPLORE_IMPORT)
                
                # Update the 'Processing...' log every 10 seconds.
                if last_updated is None or datetime.datetime.now() - last_updated > datetime.timedelta(seconds=10):
                    process_control.log = re.sub(r'(?m)^Processing tag .+\n', '', process_control.log)
                    process_control.log += 'Processing tag %r (%s/%s).\n' % (tag.name, i, num_tags)
                    last_updated = datetime.datetime.now()
                    
                process_control.date_updated = datetime.datetime.now()
                process_control.save()
            
                if not process_control.is_alive:
                    # The database has signalled for this to quit now.
                    print 'is_alive is false, quitting.'
                    break
            
            resSum['tags_processed'] += 1
            print 'Querying Xplore for Tag: %s' % tag.name
            xplore_query_url = 'http://xploreuat.ieee.org/gateway/ipsSearch.jsp?' + urllib.urlencode({
                # Number of results
                'hc': 5,
                'md': tag.name,
                'ctype' : 'Journals'
            })
            print 'Calling %s' % xplore_query_url
            try:
                file = urllib2.urlopen(xplore_query_url)
            except (urllib2.URLError, httplib.BadStatusLine):
                print 'Could not connect to the IEEE Xplore site to perform search.'
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
                            print 'No ISSN node found in Xplore result with title "%s"' % xhit_title
                            resSum['xplore_hits_without_id'] += 1
                        except UnicodeEncodeError, e:
                            print 'No ISSN node found in Xplore result with UNPRINTABLE TITLE. See error.'
                            print e
                            continue
                    elif not issn[0].firstChild.nodeValue in distinct_issns:
                        distinct_issns[issn[0].firstChild.nodeValue] = xhit_title
                
                print "Found %d unique ISSNs:" % len(distinct_issns)
                for issn, xhit_title in distinct_issns.iteritems():
                    try:
                        print '%s: "%s"' % (
                            issn,
                            xhit_title)
                    except UnicodeEncodeError, e:
                        print e
                        continue
                print "Looking for matching TechNav Resources..."
                for issn, xhit_title in distinct_issns.iteritems():
                    try:
                        per = Resource.objects.get(ieee_id=issn)
                        print '%s: Found TechNav Resource titled "%s".' % (issn, per.name)
                        
                        if per in tag.resources.all():
                            print 'Relationship already exists.'
                            resSum['existing_relationship_count'] += 1
                        else:
                            print 'Creating relationship.'
                            resSum['relationships_created'] += 1
                            xref = ResourceNodes(
                                node = tag,
                                resource = per,
                                date_created = now,
                                is_machine_generated = True
                            )
                            xref.save()
                    except Resource.DoesNotExist:
                        print '%s: No TechNav Resource found.' % issn
                        resSum['resources_not_found'] += 1
            
            # TODO add finally block to close file once python is updated past 2.4
            
            # DEBUG:
            print 'Quitting after one tag.'
            
        print '\nSummary:'
        print 'Tags Processed: %d' % resSum['tags_processed']

        print 'Xplore Connection Errors: %d' % resSum['xplore_connection_errors']
        print 'Xplore Hits without IDs: %d' % resSum['xplore_hits_without_id']
        print 'Pre-existing Relationships: %d' % resSum['existing_relationship_count']
        print 'Relationships Created: %d' % resSum['relationships_created']
        print 'Xplore Hits with no Matching Technav Tag: %d' % resSum['resources_not_found']
        
        # DEBUG: Don't really commit any changes till this script is more debugged.
        #transaction.rollback()
        
        if use_processcontrol:
            # Update the model to show that this has quit normally.
            process_control = ProcessControl.objects.get(type=PROCESS_CONTROL_TYPES.XPLORE_IMPORT)
            process_control.status = PROCESS_CONTROL_STATUSES.COMPLETED
            process_control.log += 'Quitting.\n'
            process_control.date_updated = datetime.datetime.now()
            process_control.save()
    
    except Exception, e:
        # Catch any errors that occurred in main(), write to stdout and save to DB.
        print '*****'
        print 'Exception: %r' % e
        print 'Args: %s' % repr(e.args)
        
        import traceback
        traceback.print_exc()
        
        print '*****'
        
        try:
            if use_processcontrol:
                # Attempt to update the DB with the error-exit state.
                process_control = ProcessControl.objects.get(type=PROCESS_CONTROL_TYPES.XPLORE_IMPORT)
                process_control.status = PROCESS_CONTROL_STATUSES.DIED
                process_control.log += 'Exception: %s\n' % e
                process_control.date_updated = datetime.datetime.now()
                process_control.save()
        except Exception, e:
            pass
        
        #transaction.rollback()

    #return resSum

if __name__ == "__main__":
    sys.exit(main(*sys.argv))