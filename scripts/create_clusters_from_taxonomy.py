
# Setup django.
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import ieeetags.settings
from django.core.management import setup_environ
setup_environ(ieeetags.settings)

# ------------------------------------------------------------------------------

import time
from ieeetags.models import *
from ieeetags.util import profiler

def main():

    # Delete all clusters first.
    Node.objects.get_clusters().delete()

    cluster_type = NodeType.objects.getFromName(NodeType.TAG_CLUSTER)

    MAX = 100000
    
    # Import all taxonomy clusters.

    num_tax_clusters = TaxonomyCluster.objects.all().count()
    
    print 'Taxonomy clusters: %s' % num_tax_clusters
    
    start = time.time()
    last_update = start

    num_clusters = 0
    for i, taxonomy_cluster in enumerate(TaxonomyCluster.objects.all().order_by('name')[:MAX]):
        #print taxonomy_cluster.name
        cluster = Node()
        cluster.name = taxonomy_cluster.name
        cluster.node_type = cluster_type
        cluster.save()
        
        num_clusters += 1
        
        def _add_tag_info_to_cluster(tag, cluster):
            'This is an optimized version of Node.save().'
            
            # Assign all the tag's sectors to this cluster.
            for sector in tag.get_sectors():
                if sector not in cluster.parents.all():
                    cluster.parents.add(sector)
            
            # Assign all the tag's societies to this cluster.
            for society in tag.societies.all():
                if not NodeSocieties.objects.filter(node=cluster, society=society).exists():
                    node_societies = NodeSocieties()
                    node_societies.node = cluster
                    node_societies.society = society
                    node_societies.save()
            
            # Assign all the tag's sectors to this cluster.
            for filter in tag.filters.all():
                if filter not in cluster.filters.all():
                    cluster.filters.add(filter)
        
        tags = []
        for term in taxonomy_cluster.terms.all():
            for tag in term.related_nodes.all():
                #print '  related: %s' % tag.name
                tag.parents.add(cluster)
                tag.save()
                
                # NOTE: Use this optimized function to save time, need to save after.
                _add_tag_info_to_cluster(tag, cluster)
                
        # Save again, to pick up all the sectors/filters/etc from child-tags.
        cluster.save(add_child_info=False)
        
        if time.time() - last_update > 1:
            last_update = time.time()
            per_second = i / (last_update - start)
            print 'Cluster %s/%s\t%s/s' % (i, num_tax_clusters, per_second)
        
    elapsed = time.time() - start
    print 'Total time: %s' % elapsed
    print 'Clusters converted from taxonomy: %s' % num_clusters

    num_empty_clusters = 0

    # Remove any empty clusters.
    for cluster in Node.objects.get_clusters():
        #print '%s: %s' % (cluster.name, cluster.get_tags().count())
        if cluster.get_tags().count() == 0:
            #print '  Empty cluster: %s' % cluster.name
            cluster.delete()
            num_empty_clusters += 1

    print 'Empty(removed) clusters: %s' % num_empty_clusters

    print 'Net clusters: %s' % Node.objects.get_clusters().count()

    # Assign matching tags to clusters.

if __name__ == '__main__':
    main()