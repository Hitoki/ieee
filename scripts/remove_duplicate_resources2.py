
# Setup django.
import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import ieeetags.settings
from django.core.management import setup_environ
setup_environ(ieeetags.settings)

# ------------------------------------------------------------------------------

#import time
from models.resource import Resource, ResourceNodes


def main():
    from django.db import connection


    cursor = connection.cursor()
    cursor.execute('''
        SELECT pub_id, count(id) as num_duplicates, resource_type_id
        FROM ieeetags_resource
        GROUP BY pub_id, resource_type_id
        HAVING num_duplicates > 1 AND pub_id <> ''
    ''')
    
    DO_SAVE = True
    #DO_SAVE = False
    
    print 'pub_id\tnum_duplicates'
    for pub_id, num_duplicates, resource_type_id in cursor.fetchall():
        print '%s\t%s' % (pub_id, num_duplicates)
        
        resources = Resource.objects.filter(pub_id=pub_id).order_by('id')
        
        print 'id\tieee_id\tresource_type\tpub_id\tstandard_status\tconference_series\tnodes\tsocieties'
        for resource in resources:
            print '\t'.join([repr(i) for i in [resource.id, resource.ieee_id, resource.resource_type.name, resource.pub_id, resource.standard_status, resource.conference_series, resource.nodes.count(), resource.societies.count()]])
        print ''
        
        first_resource = resources[0]
        other_resources = resources[1:]
        
        #print 'len(first_resource): %s' % len(first_resource)
        #print 'len(other_resources): %s' % len(other_resources)
        
        #print 'first_resource: %s, %s, %s, %s, %s' % (first_resource.id, first_resource.pub_id, first_resource.resource_type.name, first_resource.conference_series, first_resource.pub_id)
        
        for other_resource in other_resources:
            
            #print 'other_resource: %s, %s, %s, %s, %s' % (other_resource.id, other_resource.pub_id, other_resource.resource_type.name, other_resource.conference_series, other_resource.pub_id)
            
            assert first_resource.resource_type == other_resource.resource_type, 'resource_type: %r, %r' % (first_resource.resource_type, other_resource.resource_type)
            
            if first_resource.pub_id == '':
                first_resource.pub_id = other_resource.pub_id
            elif other_resource.pub_id == '':
                other_resource.pub_id = first_resource.pub_id
            
            if first_resource.standard_status == '':
                first_resource.standard_status = other_resource.standard_status
            elif other_resource.standard_status == '':
                other_resource.standard_status = first_resource.standard_status
            
            elif first_resource.standard_status == 'published' and other_resource.standard_status == 'project':
                other_resource.standard_status = first_resource.standard_status
            elif other_resource.standard_status == 'published' and first_resource.standard_status == 'project':
                first_resource.standard_status = other_resource.standard_status
            
            elif first_resource.standard_status == 'published' and other_resource.standard_status == 'withdrawn':
                other_resource.standard_status = first_resource.standard_status
            elif other_resource.standard_status == 'published' and first_resource.standard_status == 'withdrawn':
                first_resource.standard_status = other_resource.standard_status
            
            print 'first_resource.standard_status: %r' % first_resource.standard_status
            
            assert first_resource.standard_status == other_resource.standard_status, 'standard_status: %r, %r' % (first_resource.standard_status, other_resource.standard_status)
            
            if first_resource.id not in [8653]:
                assert first_resource.conference_series == other_resource.conference_series, 'conference_series: %r, %r' % (first_resource.conference_series, other_resource.conference_series)
            
            if first_resource.pub_id not in ['2313', '2903', '2302', '7702', '2904']:
                assert first_resource.pub_id == other_resource.pub_id, 'pub_id: %r, %r' % (first_resource.pub_id, other_resource.pub_id)
            
            if DO_SAVE:
                for resource_nodes in other_resource.resource_nodes.all():
                    if not first_resource.resource_nodes.filter(node=resource_nodes.node).exists():
                        resource_node = ResourceNodes()
                        resource_node.resource = first_resource
                        resource_node.node = resource_nodes.node
                        resource_node.save()
                
                for society in other_resource.societies.all():
                    if society not in first_resource.societies.all():
                        first_resource.societies.add(society)
                
                other_resource.delete()
            
        if DO_SAVE:
            first_resource.save()
        
        print ''

if __name__ == '__main__':
    main()
