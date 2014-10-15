import logging
from django.db import models
from webapp.models.node import Node


class TaxonomyTermManager(models.Manager):
    def create_for_clusters(self, name, cluster_names, tag_ids):
        tax_term = TaxonomyTerm()
        tax_term.name = name
        tax_term.save()
        for cluster_name in cluster_names:
            try:
                cluster = TaxonomyCluster.objects.get(name=cluster_name)
                tax_term.taxonomy_clusters.add(cluster)
            except TaxonomyCluster.DoesNotExist:
                logging.debug("Cluster not found: %s" % cluster_name)

        for tag_id in tag_ids:
            try:
                tax_term.related_nodes.add(Node.objects.get(pk=tag_id))
            except Node.DoesNotExist:
                logging.debug("Node (tag) not found with id %s" % tag_id)
        tax_term.save()


class TaxonomyTerm(models.Model):
    name = models.CharField(max_length=500)
    related_terms = models.ManyToManyField('self', related_name='terms',
                                           null=True, blank=True)
    related_nodes = models.ManyToManyField('Node', related_name='nodes',
                                           blank=True)
    taxonomy_clusters = models.ManyToManyField('TaxonomyCluster',
                                               related_name='terms',
                                               blank=True)

    objects = TaxonomyTermManager()

    class Meta:
        app_label = 'webapp'
        db_table = 'ieeetags_taxonomyterm'

    def __str__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.name)

    def __repr__(self):
        return str(self)


class TaxonomyClusterManager(models.Manager):
    pass


class TaxonomyCluster(models.Model):
    name = models.CharField(max_length=500)

    class Meta:
        app_label = 'webapp'
        db_table = 'ieeetags_taxonomycluster'

    def __str__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.name)

    def __repr__(self):
        return str(self)
