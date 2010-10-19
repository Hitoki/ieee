
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

if 1:

    # Delete all clusters first.
    Node.objects.get_clusters().delete()

    cluster_type = NodeType.objects.getFromName(NodeType.TAG_CLUSTER)

    MAX = 100000
    
    # Import all taxonomy clusters.

    num_tax_clusters = TaxonomyCluster.objects.all().count()
    
    print 'Taxonomy clusters: %s' % num_tax_clusters
    
    start = time.time()

    num_clusters = 0
    for i, taxonomy_cluster in enumerate(TaxonomyCluster.objects.all().order_by('name')[:MAX]):
        #print taxonomy_cluster.name
        cluster = Node()
        cluster.name = taxonomy_cluster.name
        cluster.node_type = cluster_type
        cluster.save()
        
        num_clusters += 1
        
        for term in taxonomy_cluster.terms.all():
            for tag in term.related_nodes.all():
                #print '  related: %s' % tag.name
                tag.parents.add(cluster)
                tag.save()
        
        # Save again, to pick up all the sectors/filters/etc from child-tags.
        cluster.save()
        
        if not (i % 20):
            elapsed = time.time() - start
            if elapsed > 0:
                per_second = round(i / elapsed, 1)
            else:
                per_second = i
            #print 'i: %s' % i
            #print 'elapsed: %s' % elapsed
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
