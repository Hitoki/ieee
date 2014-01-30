from datetime import datetime
import re
import string
from django.db import models
from django.db.models import Q
from models.node_extra import get_node_extra_info
from models.resource import Resource, ResourceNodes
from models.society import NodeSocieties, Society
from models.types import NodeType, ResourceType
from models.utils import single_row, single_row_or_none


class NodeManager(models.Manager):

    def create(self, **kwargs):
        '''Creates a node.
        Automatically reformats the name using string.capwords(),
        so "some node NAME" becomes "Some Node Name".'''
        if 'name' in kwargs:
            #print 'got name'
            kwargs['name'] = string.capwords(kwargs['name'])
        return models.Manager.create(self, **kwargs)

    def create_tag(self, **kwargs):
        '''Creates a tag.
        Automatically reformats the name using string.capwords(),
        so "some node NAME" becomes "Some Node Name".'''
        if 'name' in kwargs:
            kwargs['name'] = string.capwords(kwargs['name'])
        kwargs['node_type'] = NodeType.objects.getFromName(NodeType.TAG)
        return models.Manager.create(self, **kwargs)

    def create_cluster(self, name, sector):
        '''Creates a cluster for the given sector.'''
        cluster = super(NodeManager, self).create(
            name=name,
            node_type=NodeType.objects.getFromName(NodeType.TAG_CLUSTER)
        )
        cluster.parents = [sector]
        cluster.save()
        return cluster

    def getNodesForType(self, node_type):
        'Gets all nodes of the given node type.'
        if type(node_type) is str:
            node_type = NodeType.objects.getFromName(node_type)
        return self.filter(node_type=node_type)

    def getRoot(self):
        'Gets the root node.'
        rootType = NodeType.objects.getFromName('root')
        nodes = self.filter(node_type=rootType)
        if len(nodes) != 1:
            raise Exception('Require 1 root node, found ' + str(len(nodes)))
        return nodes[0]

    def getSectors(self):
        'Gets all sectors.'
        return self.filter(node_type__name=NodeType.SECTOR)

    def get_sector_by_name(self, name):
        'Looks up a sector from its name.'
        sector_type = NodeType.objects.getFromName(NodeType.SECTOR)
        return single_row(self.filter(name=name, node_type=sector_type),
                          'Looking up sector "%s"' % name)

    #def get_sectors_from_list(self, names):
    #    'Returns a list of sectors whose names match the given list of names.'
    #    sectorType = NodeType.objects.getFromName('sector')
    #    results = self.filter(name__in=names, node_type=sectorType)
    #    if len(results) != len(names):
    #        raise Exception('Did not find matches for all sectors:\nnames: '
    #                        '%s\nresults: %s' % (names, results))
    #    return results

    def getFirstSector(self):
        'Gets the first sector.'
        return self.getSectors()[0]

    def getTags(self):
        'DEPRECATED: Use get_tags() instead.'
        return self.get_tags()

    def get_tags(self):
        "Returns all tags."
        tag_type = NodeType.objects.getFromName('tag')
        return self.filter(node_type=tag_type)

    def getTagsByName(self, name):
        'Gets all tags that have a given name.'
        tag_type = NodeType.objects.getFromName('tag')
        return self.filter(name=name, node_type=tag_type)

    #def get_tag_by_name(self, tag_name):
    #    '''Returns a single tag matching the given name, or None if not found.
    #    Fails if more than one exist.'''
    #    #print 'get_tag_by_name()'
    #    #print '  tag_name:', tag_name
    #    tag_type = NodeType.objects.getFromName('tag')
    #    return single_row_or_none(self.filter(name=tag_name,
    #                                          node_type=tag_type))

    #def get_resource_range(self, sector):
    #    "Returns the min/max amount of resources-per-tag for the given sector"
    #
    #    resource_counts = [tag.resources.count()
    #                       for tag in sector.child_nodes.all()]
    #    if len(resource_counts) == 0:
    #        min_resources = None
    #        max_resources = None
    #    else:
    #        min_resources = min(resource_counts)
    #        max_resources = max(resource_counts)
    #
    #    return (min_resources, max_resources)

    #def get_cluster_range(self, cluster):
    #    "Returns the min/max amount of sectors-per-tag for the given sector."
    #
    #    TODO: Should use tag.get_sectors() here instead?
    #    sector_counts = [tag.parents.count() for tag in sector.child_nodes.all()]
    #
    #    if len(sector_counts) == 0:
    #        min_sectors = None
    #        max_sectors = None
    #    else:
    #        min_sectors = min(sector_counts)
    #        max_sectors = max(sector_counts)
    #
    #    return (min_sectors, max_sectors)

    #def get_related_tag_range(self, sector):
    #    """
    #    Returns the min/max amount of related_tags-per-tag for the given sector
    #    """
    #
    #    related_tag_counts = [tag.related_tags.count()
    #                          for tag in sector.child_nodes.all()]
    #    if len(related_tag_counts) == 0:
    #        min_related_tags = None
    #        max_related_tags = None
    #    else:
    #        min_related_tags = min(related_tag_counts)
    #        max_related_tags = max(related_tag_counts)
    #
    #    return (min_related_tags, max_related_tags)

    def searchTagsByNameSubstring(self, substring, sector_ids=None,
                                  exclude_tag_id=None, society_id=None,
                                  exclude_society_id=None, tag_type=None):
        """
        Search for tags matching the given substring.
        Optionally limit to only the list of sectors given.
        @param substring name substring to search for.
                         Can also be * to show all tags.
        @param sector_ids optional, a list of sector ids to limit the search
                          within.
        """
        if substring.strip() == '':
            return None

        if tag_type is None:
            tag_type = NodeType.objects.getFromName(NodeType.TAG)

        if substring == '*':
            if society_id is None:
                raise Exception('If substring is "*", '
                                'then society_id must be specified')
            # Find all tags for this society
            results = self.filter(societies=society_id, node_type=tag_type)
        else:
            results = self.filter(name__icontains=substring,
                                  node_type=tag_type)

        if sector_ids is not None:
            # Filter to only the given sectors
            q = None
            for sector_id in sector_ids:
                if q is not None:
                    q = q | Q(parents=sector_id)
                else:
                    q = Q(parents=sector_id)
            results = results.filter(q).distinct()

        if exclude_tag_id is not None:
            results = results.exclude(id=exclude_tag_id)

        if exclude_society_id is not None:
            results = results.exclude(societies__id=exclude_society_id)

        return results

    #def get_sectors_for_tag(self, node):
    #    for node1 in self.filter(name=node.name):
    #        yield node1.parent

    def get_orphan_tags(self):
        "Find all tags that are not associated with any societies."

        # Get orphan tags
        tag_type = NodeType.objects.getFromName(NodeType.TAG)
        tags = self.extra(
            where=[
                """
                (SELECT COUNT(ieeetags_node_societies.id) AS num_societies
                    FROM ieeetags_node_societies
                    WHERE ieeetags_node_societies.node_id = ieeetags_node.id) = 0
                """
            ],
        ).filter(node_type=tag_type)

        # Get the TAB society's tags
        tab_society = Society.objects.getFromAbbreviation('TAB')
        if tab_society is None:
            raise Exception('Can\'t find TAB society')

        # Filter out tags with other societies
        tab_society_tags = [tag for tag in tab_society.tags.all() if tag.societies.count() == 1]

        # Combine both
        from itertools import chain
        tags = list(chain(tags, tab_society_tags))

        return tags

    def get_clusters(self):
        'Returns all clusters.'
        return self.filter(node_type=NodeType.objects.getFromName(NodeType.TAG_CLUSTER)).all()

    def get_cluster(self, clusterId):
        'Returns the give cluster.'
        return single_row_or_none(self.filter(id=clusterId, node_type__name=NodeType.TAG_CLUSTER))

    def get_cluster_by_name(self, cluster_name, sector_name):
        '''
        Looks up a cluster in a given sector.  Returns None if none found.
        @param cluster_name: The cluster's name.
        @param sector_name: The sector's name.
        '''
        return single_row_or_none(
            self.filter(
                node_type__name=NodeType.TAG_CLUSTER,
                name=cluster_name,
                parents__name=sector_name,
            )
        )

    def sort_queryset_by_score(self, queryset, ascending=True):
        """
        Returns the queryset as a list with extra columns:
            score
        """
        def sort_function(obj):
            if ascending:
                return obj.score1
            else:
                return -obj.score1
        list1 = list(queryset)
        list1.sort(key=sort_function)
        return list1

    def get_tags_and_clusters(self):
        "Returns all clusters & non-clustered tags."

        tag_type = NodeType.objects.getFromName(NodeType.TAG)
        cluster_type = NodeType.objects.getFromName(NodeType.TAG_CLUSTER)

        # Select tags & clusters.
        child_nodes = self.filter(
            Q(node_type=cluster_type.id)
            |
            Q(node_type=tag_type.id)
        )

        # Exclude clustered tags.
        child_nodes = child_nodes.\
            exclude(parents__node_type__name=NodeType.TAG_CLUSTER)

        return child_nodes

    def get_tags_non_clustered(self):
        "Returns all tags that are not clustered."
        tags = self.filter(node_type__name=NodeType.TAG)
        tags = tags.exclude(parents__node_type__name=NodeType.TAG_CLUSTER)
        return tags


class Node(models.Model):
    '''
    This model can represent different types of nodes
    (root, sector, cluter, tag).

    There is only one root tag.

    Each sector is a child of the root tag, and can contain clusters and tags.

    Each cluster is the child of 1 or more sectors, and contain 0 or more tags.

    Each tag is a child of any number of sectors and clusters.
    It contains no children.
    '''
    is_active = models.BooleanField(blank=False,default=True)
    name = models.CharField(max_length=500)
    parents = models.ManyToManyField('self', symmetrical=False,
                                     related_name='child_nodes',
                                     null=True, blank=True)
    'The parent nodes.  ' \
    'The type for this field can be vary depending on the type of this node.'
    node_type = models.ForeignKey(NodeType)
    'The type of node this is: root, sector, cluster, tag.'
    societies = models.ManyToManyField('Society', related_name='tags',
                                       blank=True, through='NodeSocieties')
    filters = models.ManyToManyField('Filter', related_name='nodes')
    related_tags = models.ManyToManyField('self', null=True, blank=True)

    is_taxonomy_term = models.BooleanField(default=False)
    'Marks tags that have originated from the IEEE taxonomy.'

    high_potency = models.BooleanField(default=False)

    definition = models.CharField(blank=True, null=True, max_length=2000)
    definition_source = models.CharField(blank=True, null=True, max_length=50)
    definition_updated_when =models.DateTimeField(blank=True, null=True)

    objects = NodeManager()

    def __unicode__(self):
        return self.name

    def sector_names(self):
        return ', '.join([sector.name for sector in self.get_sectors()])

    def parent_cluster_names(self):
        return ', '.join([cluster.name for cluster in self.get_parent_clusters()])

    def get_sectors(self):
        'Returns all parent sectors for this node.'
        return self.parents.filter(node_type__name=NodeType.SECTOR)

    def get_parent_clusters(self):
        'Returns all parent clusters for this node (for tags).'
        return self.parents.filter(node_type__name=NodeType.TAG_CLUSTER)

    def get_child_clusters(self):
        'Returns all child clusters for this node (for sectors).'
        return self.child_nodes.filter(node_type__name=NodeType.TAG_CLUSTER)

    def get_tags(self):
        "Returns all child tags for this node."
        return self.child_nodes.filter(node_type__name=NodeType.TAG)

    def get_tags_non_clustered(self):
        "Returns all child tags that are not clustered for this node."
        tags = self.child_nodes.filter(node_type__name=NodeType.TAG)
        tags = tags.exclude(parents__node_type__name=NodeType.TAG_CLUSTER)
        return tags

    def get_tags_and_clusters(self):
        "Returns any child clusters and non-clustered child tags."
        assert self.node_type.name == NodeType.SECTOR, \
            'get_tags_and_clusters() only works for sectors.'
        return self.child_nodes.\
            exclude(parents__node_type__name=NodeType.TAG_CLUSTER)

    def cluster_update_filters(self):
        '''For clusters only.
        Updates this cluster\'s filters to reflect all the current filters
        of its child tags.'''
        assert self.node_type.name == NodeType.TAG_CLUSTER, \
            'Node "%s" is not a cluster' % self.name

        # Remove any filters that no longer apply
        for filter in self.filters.all():
            exists = False
            for tag in self.child_nodes.all():
                if filter in tag.filters.all():
                    exists = True
            if exists == False:
                self.filters.remove(filter)

        # Add any new filters
        for tag in self.child_nodes.all():
            for filter in tag.filters.all():
                if filter not in self.filters.all():
                    self.filters.add(filter)

    def get_filtered_related_tag_count(self):
        """Returns the number of related tags that have filters/resources
        (ie. are not hidden)"""

        # TODO: Not done yet
        #return self.filtered_num_related_tags1

        # TODO: This is very slow!
        count = 0

        related_tags = self.related_tags.all()
        related_tags = get_node_extra_info(related_tags)

        for related_tag in related_tags:
            if related_tag.num_filters1 > 0 and related_tag.num_resources1 > 0:
                count += 1
        return count

    def get_resource_count(self):
        return ResourceNodes.objects.filter(node=self).count()

    resource_count = property(get_resource_count)

    def _get_short_definition(self):
        """Returns the first sentence for old/new wikipedia definitions."""
        if not self.definition_type.startswith('wiki'):
            return self.definition

        # Match up to the first period followed by a space that
        # isn't part of i.e. or e.g.
        pat = r'(.+?(?<![(i\.e)|(e\.g)])\.)\s'
        matches = re.search(pat, self.definition)
        if matches:
            short_def = matches.groups()[0]
            if self.definition_type == 'wiki old':
                # Add back the embedded source string that just got removed.
                short_def = '%s %s' % (short_def, '(www.wikipedia.org)')
            return short_def
        else:
            return self.definition

    short_definition = property(_get_short_definition)

    def _get_definition_link(self):
        if self.definition_source == 'dbpedia.org':
            return "(From <a href='https://wikipedia.org/wiki/%s'>Wikipedia.org</a>)" % self.wikipedia_slug
        else:
            return ''

    definition_link = property(_get_definition_link)

    def _get_definition_type(self):
        if self.definition_source == 'dbpedia.org':
            return "wiki new"
        elif 'wikipedia.org' in self.definition.lower():
            return "wiki old"
        else:
            return "other"

    definition_type = property(_get_definition_type)


    def _get_wikipedia_slug(self):
        """Transform the tag name into a format used by wikipedia."""
        return self.name.replace(' ', '_')

    wikipedia_slug = property(_get_wikipedia_slug)

    def _get_closest_conference(self):
        """Returns the single closest upcoming conference related to the tag"""
        if self.node_type.name == NodeType.TAG:
            # return self.filter(nodes=node,
            #                    resource_type=ResourceType.CONFERENCE)
            try:
                return Resource.objects.\
                    getForNode(self, resourceType=ResourceType.CONFERENCE).\
                    filter(year__gte=datetime.today().year).\
                    order_by('date', 'year', 'id')[0]
            except IndexError:
                return None
            #datetime.date.today()
        else:
            raise Exception('Node is not a tag')

    closest_conference = property(_get_closest_conference)

    def _get_single_periodical(self):
        """Returns single periodical related to the tag"""
        if self.node_type.name == NodeType.TAG:
            return Resource.objects.\
                getForNode(self, resourceType=ResourceType.PERIODICAL)[0]
        else:
            raise Exception('Node is not a tag')

    single_periodical = property(_get_single_periodical)

    def _get_societies_related_to_child(self):
        #import ipdb; ipdb.set_trace()
        return NodeSocieties.objects.filter(
            node__id__in=self.child_nodes.values_list('id')
        ).values_list('society__id')

    societies_related_to_child = property(_get_societies_related_to_child)

    def save(self, add_child_info=True, *args, **kwargs):
        cluster_type = NodeType.objects.getFromName(NodeType.TAG_CLUSTER)
        #print 'Node.save()'
        #print '  self.node_type: %r' % self.node_type
        #print '  cluster_type: %r' % cluster_type
        if self.node_type == cluster_type:
            # If this is a cluster, customize the saving process.

            if self.id is None:
                # Save the new cluster so we can use the relationship fields.
                super(Node, self).save(*args, **kwargs)

            if add_child_info:
                # Assign all the child_node's sectors to this cluster.
                sectors = []
                for child_node in self.child_nodes.all():
                    for sector in child_node.get_sectors():
                        if sector not in sectors:
                            sectors.append(sector)
                self.parents = sectors

                # Assign all the child_node's societies to this cluster.
                societies = []
                for child_node in self.child_nodes.all():
                    for society in child_node.societies.all():
                        if not NodeSocieties.objects.filter(node=self, society=society).exists():
                            node_societies = NodeSocieties()
                            node_societies.node = self
                            node_societies.society = society
                            node_societies.save()

                # Assign all the child_node's filters to this cluster.
                filters = []
                for child_node in self.child_nodes.all():
                    for filter in child_node.filters.all():
                        if filter not in filters:
                            filters.append(filter)
                self.filters = filters

        super(Node, self).save(*args, **kwargs)

        #print '  self.societies.all(): %r' % self.societies.all()

    def get_sector_ranges(self, tags=None, show_empty_terms=False):
        """
        Returns the min/max amount of resources/sectors/related-tags
        per child-tag for this node.
        NOTE: self must be root, sector, or cluster.
        Ignores tags with no resources, no filters, or no societies.
        @param tags (optional) - a list of child tags to parse
                    (for speeding up repeat queries).
        @return a tuple:
            (min_resources,
            max_resources,
            min_sectors,
            max_sectors,
            min_related_tags,
            max_related_tags,
            min_societies,
            max_societies)
        """

        assert self.node_type.name == NodeType.ROOT or NodeType.SECTOR or \
               self.node_type.name == NodeType.TAG_CLUSTER, \
            'self (%s, %s, %s) must be a sector or cluster' % \
            (self.name, self.id, self.node_type.name)

        if tags is None:
            if self.node_type.name == NodeType.ROOT:
                tags = Node.objects.get_tags()
            else:
                tags = self.child_nodes
            # Filter out tags with no resources
            tags = get_node_extra_info(tags)
            tags = tags.values(
                #'num_filters1',
                'num_related_tags1',
                'num_resources1',
                'num_sectors1',
                'num_societies1',
                'is_taxonomy_term',
            )

        min_resources = None
        max_resources = None
        min_sectors = None
        max_sectors = None
        min_related_tags = None
        max_related_tags = None
        min_societies = None
        max_societies = None

        for tag in tags:
            # Ignore all hidden tags

            if (show_empty_terms and tag['is_taxonomy_term']) or (tag['num_societies1'] > 0 and tag['num_resources1'] > 0):
                if min_resources is None or tag['num_resources1'] < min_resources:
                    min_resources = tag['num_resources1']
                if max_resources is None or tag['num_resources1'] > max_resources:
                    max_resources = tag['num_resources1']

                if min_sectors is None or tag['num_sectors1'] < min_sectors:
                    min_sectors = tag['num_sectors1']
                if max_sectors is None or tag['num_sectors1'] > max_sectors:
                    max_sectors = tag['num_sectors1']

                if min_related_tags is None or tag['num_related_tags1'] < min_related_tags:
                    min_related_tags = tag['num_related_tags1']
                if max_related_tags is None or tag['num_related_tags1'] > max_related_tags:
                    max_related_tags = tag['num_related_tags1']

                if min_societies is None or tag['num_societies1'] < min_societies:
                    min_societies = tag['num_societies1']
                if max_societies is None or tag['num_societies1'] > max_societies:
                    max_societies = tag['num_societies1']

        return (min_resources, max_resources, min_sectors, max_sectors,
                min_related_tags, max_related_tags, min_societies,
                max_societies)

    def get_combined_sector_ranges(self, tags=None, show_empty_terms=False):
        """
        Returns the min/max combined score per tag for the given sector
        or cluster.
        NOTE: self must be a sector or cluster.
        Ignores tags with no resources, no filters, or no societies.
        @param self a sector or cluster self.
        @param tags (optional) - a list of child tags to parse
                    (for speeding up repeat queries).
        @return a tuple (min, max).
        """
        assert self.node_type.name == NodeType.ROOT or NodeType.SECTOR or self.node_type.name == NodeType.TAG_CLUSTER, 'self (%s, %s, %s) must be a sector or cluster' % (self.name, self.id, self.node_type.name)
        if tags is None:
            if self.node_type.name == NodeType.ROOT:
                tags = Node.objects.get_tags()
            else:
                tags = self.child_nodes
            # Filter out tags with no resources
            tags = get_node_extra_info(tags)
            tags = tags.values(
                'num_resources1',
                'num_societies1',
                'score1',
                'is_taxonomy_term',
            )

        min_score = None
        max_score = None

        for tag in tags:
            # Ignore all hidden tags
            if (show_empty_terms and tag['is_taxonomy_term']) or (tag['num_societies1'] > 0 and tag['num_resources1'] > 0):
                if min_score is None or tag['score1'] < min_score:
                    min_score = tag['score1']
                if max_score is None or tag['score1'] > max_score:
                    max_score = tag['score1']

        print 'min_score: %r' % min_score
        print 'max_score: %r' % max_score
        return (min_score, max_score)

    class Meta:
        ordering = ['name']
