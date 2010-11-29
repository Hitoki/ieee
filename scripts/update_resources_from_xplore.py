# Setup django.
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import ieeetags.settings
from django.core.management import setup_environ
setup_environ(ieeetags.settings)

# ------------------------------------------------------------------------------

import urllib
import urllib2
from django.db import transaction
from ieeetags.models import *

@transaction.commit_manually
def main(*args):

    XploreUpdateResultsSummary = {
        'tags_processed' : 0,
        'xplore_connection_errors' : 0,
        'xplore_hits_without_id' : 0,
        'existing_relationship_count' : 0,
        'relationships_created' : 0,
        'resources_not_found' : 0
    }
    
    import logging.handlers
    
    now = datetime.now()
        
    resSum = XploreUpdateResultsSummary
    
    log_dirname = os.path.join(os.path.dirname(settings.LOG_FILENAME), 'xplore_imports')
    if not os.path.exists(log_dirname):
        os.makedirs(log_dirname)
    
    log_filename = 'xplore_resource_import_log_%s.txt' % now.strftime('%Y%m%d%H%M%S')
    log_filename = os.path.join(log_dirname, log_filename)
    xplore_logger = open(log_filename, 'ab')
    
    xplore_logger.write('Import Xplore Results into Resource' + os.linesep)
    xplore_logger.write('Started at %s' % now + os.linesep)
    
    resource_type = ResourceType.objects.getFromName('periodical')
    node_type = NodeType.objects.getFromName('tag')
    tags = Node.objects.filter(node_type=node_type)[:5]
    for tag in tags:
        resSum['tags_processed'] += 1
        xplore_logger.write('Querying Xplore for Tag: %s' % tag.name + os.linesep)
        xplore_query_url = 'http://xploreuat.ieee.org/gateway/ipsSearch.jsp?' + urllib.urlencode({
            # Number of results
            'hc': 5,
            'md': tag.name,
            'ctype' : 'Journals'
        })
        xplore_logger.write('Calling %s' % xplore_query_url + os.linesep)
        try:
            file = urllib2.urlopen(xplore_query_url)
        except urllib2.URLError:
            xplore_logger.write('Could not connect to the IEEE Xplore site to perform search.')
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
                    xplore_logger.write('No ISSN node found in Xplore result with title "%s"' % xhit_title + os.linesep)
                    resSum['xplore_hits_without_id'] += 1
                elif not issn[0].firstChild.nodeValue in distinct_issns:
                    distinct_issns[issn[0].firstChild.nodeValue] = xhit_title
            
            xplore_logger.write("Found %d unique ISSNs:" % len(distinct_issns) + os.linesep)
            for issn, xhit_title in distinct_issns.iteritems():
                xplore_logger.write('%s: "%s"' % (
                    issn,
                    xhit_title) + os.linesep
                )
            xplore_logger.write("Looking for matching TechNav Resources..." + os.linesep)
            for issn, xhit_title in distinct_issns.iteritems():
                try:
                    per = Resource.objects.get(ieee_id=issn)
                    xplore_logger.write('%s: Found TechNav Resource titled "%s".' % (issn, per.name) + os.linesep)

                    if per in tag.resources.all():
                        xplore_logger.write('Relationship already exists.' + os.linesep)
                        resSum['existing_relationship_count'] += 1
                    else:
                        xplore_logger.write('Creating relationship.' + os.linesep)
                        resSum['relationships_created'] += 1
                        xref = ResourceNodes(
                            node = tag,
                            resource = per,
                            date_created = now,
                            is_machine_generated = True
                        )
                        xref.save()
                except Resource.DoesNotExist:
                    xplore_logger.write('%s: No TechNav Resource found.' % issn + os.linesep)
                    resSum['resources_not_found'] += 1
        # TODO add finally block to close file once python is updated past 2.4
        
    xplore_logger.write('\nSummary:' + os.linesep)
    xplore_logger.write('Tags Processed: %d' % resSum['tags_processed'] + os.linesep)

    xplore_logger.write('Xplore Connection Errors: %d' % resSum['xplore_connection_errors'] + os.linesep)
    xplore_logger.write('Xplore Hits without IDs: %d' % resSum['xplore_hits_without_id'] + os.linesep)
    xplore_logger.write('Pre-existing Relationships: %d' % resSum['existing_relationship_count'] + os.linesep)
    xplore_logger.write('Relationships Created: %d' % resSum['relationships_created'] + os.linesep)
    xplore_logger.write('Xplore Hits with no Matching Technav Tag: %d' % resSum['resources_not_found'] + os.linesep)
    xplore_logger.close()
    transaction.rollback()
    
    return resSum

if __name__ == "__main__":
    sys.exit(main(*sys.argv))