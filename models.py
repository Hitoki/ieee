from django.contrib.auth.models import User, UserManager
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import MultipleObjectsReturned 
from django.db import connection
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from datetime import datetime
from logging import debug as log
import time
import string
import settings
import logging
import re
#from profiler import Profiler
from enum import Enum
import util

def single_row(results, message=None):
    '''
    Returns a single row from the results.  Raises an error if there is 0 or >1 rows.
    @param results: queryset.
    @param message: (Optional) Message to include in the exception if there are 0 or >1 results.
    '''
    if len(results) != 1:
        if message is None:
            raise Exception('Require 1 row, found %i.' % len(results))
        else:
            raise Exception('%s\nRequire 1 row, found %i' % (message, len(results)))
    return results[0]

def single_row_or_none(results):
    '''
    Returns a single row from the results, or None if there are 0 results.  Raises an exception if there are >1 results.
    '''
    if len(results) > 1:
        raise Exception('Require 1 row, found %d' % len(results))
    elif len(results) == 0:
        return None
    return results[0]

def list_to_choices(list):
    "Takes a list and returns a list of 2-tuples, useful for the 'choices' form field attribute."
    result = []
    for item in list:
        result.append((item, item))
    return result

# ------------------------------------------------------------------------------

class NamedTypeManager(models.Manager):
    def getFromName(self, name):
        'Looks up a NamedType that matches the given name.  Fails if none found.'
        types = self.filter(name=name)
        if len(types) != 1:
            raise Exception('Found %d %s for name "%s", looking for 1 result' % (len(types), self.__class__, name))
        return types[0]

class NamedType(models.Model):
    'A named type.  Used for named constants in the DB.'
    name = models.CharField(max_length=50)
    
    def __unicode__(self):
        return self.name
    class Meta:
        abstract = True

# ------------------------------------------------------------------------------

class NamedValueTypeManager(NamedTypeManager):
    def getFromValue(self, value):
        'Looks up a NamedType that matches the given value.  Fails if none found.'
        types = self.filter(value=value)
        return single_row(types)

class NamedValueType(NamedType):
    'A named & valued type.  Each object has a name and value.  Used for named/valued constants in the DB.'
    value = models.CharField(max_length=500)
    
    def __unicode__(self):
        return '%s (%s)' % (self.name, self.value)
    class Meta:
        abstract = True

# ------------------------------------------------------------------------------

class NodeTypeManager(NamedTypeManager):
    pass

class NodeType(NamedType):
    'The constant node types.  Can be a cluster, tag, sector, or root.'
    TAG_CLUSTER = 'tag_cluster'
    TAG = 'tag'
    SECTOR = 'sector'
    ROOT = 'root'
    
    objects = NodeTypeManager()
    
class NodeManager(models.Manager):
    
    def create(self, **kwargs):
        'Creates a node.  Automatically reformats the name using string.capwords(), so "some node NAME" becomes "Some Node Name".'
        if 'name' in kwargs:
            #print 'got name'
            kwargs['name'] = string.capwords(kwargs['name'])
        return models.Manager.create(self, **kwargs)
    
    def create_tag(self, **kwargs):
        'Creates a tag.  Automatically reformats the name using string.capwords(), so "some node NAME" becomes "Some Node Name".'
        if 'name' in kwargs:
            kwargs['name'] = string.capwords(kwargs['name'])
        kwargs['node_type'] = NodeType.objects.getFromName(NodeType.TAG)
        return models.Manager.create(self, **kwargs)
        
    def create_cluster(self, name, sector):
        'Creates a cluster for the given sector.'
        cluster = super(NodeManager, self).create(name=name, node_type = NodeType.objects.getFromName(NodeType.TAG_CLUSTER))
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
        return single_row(self.filter(name=name, node_type=sector_type), 'Looking up sector "%s"' % name)
    
    #def get_sectors_from_list(self, names):
    #    'Returns a list of sectors whose names match the given list of names.'
    #    sectorType = NodeType.objects.getFromName('sector')
    #    results = self.filter(name__in=names, node_type=sectorType)
    #    if len(results) != len(names):
    #        raise Exception('Did not find matches for all sectors:\nnames: %s\nresults: %s' % (names, results))
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
    #    'Returns a single tag matching the given name, or None if not found.  Fails if more than one exist.'
    #    #print 'get_tag_by_name()'
    #    #print '  tag_name:', tag_name
    #    tag_type = NodeType.objects.getFromName('tag')
    #    return single_row_or_none(self.filter(name=tag_name, node_type=tag_type))
        
    #def get_resource_range(self, sector):
    #    "Returns the min/max amount of resources-per-tag for the given sector."
    #    
    #    resource_counts = [tag.resources.count() for tag in sector.child_nodes.all()]
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
    #    "Returns the min/max amount of related_tags-per-tag for the given sector."
    #    
    #    related_tag_counts = [tag.related_tags.count() for tag in sector.child_nodes.all()]
    #    if len(related_tag_counts) == 0:
    #        min_related_tags = None
    #        max_related_tags = None
    #    else:
    #        min_related_tags = min(related_tag_counts)
    #        max_related_tags = max(related_tag_counts)
    #    
    #    return (min_related_tags, max_related_tags)
    
    def searchTagsByNameSubstring(self, substring, sector_ids=None, exclude_tag_id=None, society_id=None, exclude_society_id=None):
        """
        Search for tags matching the given substring.  Optionally limit to only the list of sectors given.
        @param substring name substring to search for.  Can also be * to show all tags.
        @param sector_ids optional, a list of sector ids to limit the search within.
        """
        if substring.strip() == '':
            return None
        tag_type = NodeType.objects.getFromName(NodeType.TAG)
        
        if substring == '*':
            if society_id is None:
                raise Exception('If substring is "*", then society_id must be specified')
            # Find all tags for this society
            results = self.filter(societies=society_id, node_type=tag_type)
        else:
            results = self.filter(name__icontains=substring, node_type=tag_type)
        
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
    

    def get_extra_info(self, queryset, order_by=None, selected_filter_ids=None):
        """
        Returns the queryset with extra columns:
            num_resources1
            num_societies1
            num_filters1
            num_selected_filters1
            num_sectors1
            num_related_tags1
            num_parents1
            score1
        """
        


        tag_node_type_id = NodeType.objects.getFromName(NodeType.TAG).id
        sector_node_type_id = NodeType.objects.getFromName(NodeType.SECTOR).id
        cluster_node_type_id = NodeType.objects.getFromName(NodeType.TAG_CLUSTER).id
        
        if selected_filter_ids is not None:
            selected_filter_ids = [str(id) for id in selected_filter_ids]
            num_selected_filters1_sql = """
                SELECT Count(*)
                FROM ieeetags_node_filters
                WHERE ieeetags_node_filters.node_id = ieeetags_node.id
                AND ieeetags_node_filters.filter_id in (%s)
            """ % ','.join(selected_filter_ids)
        else:
            num_selected_filters1_sql = 'SELECT NULL'
            
        num_resources_sql = """
            -- Count of this tag's resources.
            IFNULL(IF(ieeetags_node.node_type_id = %(tag_node_type_id)s,
                (SELECT COUNT(*)
                FROM ieeetags_resource_nodes
                WHERE ieeetags_resource_nodes.node_id = ieeetags_node.id)
            ,
                (SELECT AVG(child_resources.num_count) FROM (
                    SELECT COUNT(*) as num_count, ieeetags_resource_nodes.node_id as nodeId
                    FROM ieeetags_resource_nodes
                    GROUP BY ieeetags_resource_nodes.node_id
                ) AS child_resources WHERE nodeId = ieeetags_node.id )
            ),0)
        """ % {'tag_node_type_id': tag_node_type_id}
        
        num_societies_sql = """
            -- Count of this tag's societies
            IFNULL(IF(ieeetags_node.node_type_id = %(tag_node_type_id)s,
                (SELECT COUNT(*)
                FROM ieeetags_node_societies
                WHERE ieeetags_node_societies.node_id = ieeetags_node.id)
            ,
                (SELECT AVG(child_societies.num_count) FROM (
                    SELECT COUNT(*) as num_count, ieeetags_node_societies.node_id as nodeId
                    FROM ieeetags_node_societies
                    GROUP BY ieeetags_node_societies.node_id
                ) AS child_societies WHERE nodeId = ieeetags_node.id)
            ),0)
        """ %{'tag_node_type_id': tag_node_type_id, 'cluster_node_type_id': cluster_node_type_id, 'sector_node_type_id': sector_node_type_id}
        
        num_filters_sql = 'SELECT COUNT(*) FROM ieeetags_node_filters WHERE ieeetags_node_filters.node_id = ieeetags_node.id'
        
        num_sectors_sql = """
            -- This tag's sectors.
            IFNULL(IF(ieeetags_node.node_type_id = %(tag_node_type_id)s,
                (SELECT COUNT(*)
                FROM ieeetags_node_parents
                INNER JOIN ieeetags_node as parent
                ON ieeetags_node_parents.to_node_id = parent.id
                WHERE ieeetags_node_parents.from_node_id = ieeetags_node.id
                AND parent.node_type_id = %(sector_node_type_id)s)
            ,
                (SELECT AVG(child_sectors.num_count) FROM (
                    SELECT COUNT(*) as num_count, n.id as nodeId
                    FROM ieeetags_node n
                    CROSS JOIN ieeetags_node_parents xp
                    ON n.id = xp.from_node_id
                    AND n.node_type_id = %(sector_node_type_id)s
                    GROUP BY n.id
                ) AS child_sectors WHERE nodeId = ieeetags_node.id)
            ),0)
        """ % {'tag_node_type_id': tag_node_type_id, 'cluster_node_type_id': cluster_node_type_id, 'sector_node_type_id': sector_node_type_id}
        
        num_related_tags_sql = """
            -- Count of this tag's related tags
            IFNULL(IF(ieeetags_node.node_type_id = %(tag_node_type_id)s,
                (SELECT COUNT(*)
                FROM ieeetags_node_related_tags
                WHERE ieeetags_node_related_tags.from_node_id = ieeetags_node.id)
            ,
               -- AVG of cluster's tags related tag count.
                (SELECT AVG(child_related_tags.num_count) FROM (
                    SELECT COUNT(*) as num_count, ieeetags_node_related_tags.from_node_id AS nodeId
                    FROM ieeetags_node_related_tags
                    GROUP BY ieeetags_node_related_tags.from_node_id
                ) AS child_related_tags WHERE nodeId = ieeetags_node.id)
            ),0)
        """ % {'tag_node_type_id': tag_node_type_id, 'cluster_node_type_id': cluster_node_type_id, 'sector_node_type_id': sector_node_type_id}
        
        return queryset.extra(
            select={
                'num_resources1': num_resources_sql,
                'num_societies1': num_societies_sql,
                'num_filters1': num_filters_sql,
                'num_selected_filters1': num_selected_filters1_sql,
                'num_sectors1': num_sectors_sql,
                #'num_clusters1': 'SELECT COUNT(*) FROM ieeetags_node_parents INNER JOIN ieeetags_node as parent on ieeetags_node_parents.to_node_id = parent.id WHERE ieeetags_node_parents.from_node_id = ieeetags_node.id AND parent.node_type_id = %s' % (cluster_node_type_id),
                # TODO: Some of the related tags will be hidden (no resources, no filters, etc), so this count is off
                'num_related_tags1': num_related_tags_sql,
                'num_parents1': 'SELECT COUNT(*) FROM ieeetags_node_parents WHERE ieeetags_node_parents.from_node_id = ieeetags_node.id',
                'score1': """
                    %(num_resources_sql)s
                    +
                    %(num_sectors_sql)s
                    +
                    %(num_related_tags_sql)s
                    +
                    %(num_societies_sql)s
                    """ % {'num_resources_sql': num_resources_sql, 'num_societies_sql': num_societies_sql, 'num_sectors_sql': num_sectors_sql, 'num_related_tags_sql': num_related_tags_sql, 'cluster_node_type_id': cluster_node_type_id, 'sector_node_type_id': sector_node_type_id},
                #'filtered_num_related_tags1': """
                #    SELECT COUNT(ieeetags_node_related_tags.id) FROM ieeetags_node_related_tags WHERE ieeetags_node_related_tags.from_node_id = ieeetags_node.id
                #    """,
            },
            order_by=order_by,
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
        child_nodes = child_nodes.exclude(parents__node_type__name=NodeType.TAG_CLUSTER)
        
        return child_nodes
    
    def get_tags_non_clustered(self):
        "Returns all tags that are not clustered."
        tags = self.filter(node_type__name=NodeType.TAG)
        tags = tags.exclude(parents__node_type__name=NodeType.TAG_CLUSTER)
        return tags
    
class Node(models.Model):
    '''
    This model can represent different types of nodes (root, sector, cluter, tag).
    
    There is only one root tag.
    
    Each sector is a child of the root tag, and can contain clusters and tags.
    
    Each cluster is the child of 1 or more sectors, and contain 0 or more tags.
    
    Each tag is a child of any number of sectors and clusters.  It contains no children.
    '''
    name = models.CharField(max_length=500)
    parents = models.ManyToManyField('self', symmetrical=False, related_name='child_nodes', null=True, blank=True)
    'The parent nodes.  The type for this field can be vary depending on the type of this node.'
    node_type = models.ForeignKey(NodeType)
    'The type of node this is: root, sector, cluster, tag.'
    societies = models.ManyToManyField('Society', related_name='tags', blank=True, through='NodeSocieties')
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
    
    def name_with_sector(self):
        if self.node_type.name == NodeType.TAG:
            return '%s (%s)' % (self.name, self.sector_names())
        else:
            return self.name
    
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
        assert self.node_type.name == NodeType.SECTOR, 'get_tags_and_clusters() only works for sectors.'
        return self.child_nodes.exclude(parents__node_type__name=NodeType.TAG_CLUSTER)
    
    def cluster_update_filters(self):
        'For clusters only.  Updates this cluster\'s filters to reflect all the current filters of its child tags.'
        assert self.node_type.name == NodeType.TAG_CLUSTER, 'Node "%s" is not a cluster' % self.name
        
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
        "Returns the number of related tags that have filters/resources (ie. are not hidden)"
        
        # TODO: Not done yet
        #return self.filtered_num_related_tags1
        
        # TODO: This is very slow!
        count = 0
        
        related_tags = self.related_tags.all()
        related_tags = Node.objects.get_extra_info(related_tags)
        
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

        pat = r'(.+?\.)\s'
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
        elif 'wikipedia.org' in self.definition:
            return "wiki old"
        else:
            return "other"

    definition_type = property(_get_definition_type)
        

    def _get_wikipedia_slug(self):
        """Transform the tag name into a format used by wikipedia."""
        return self.name.replace(' ', '_')

    wikipedia_slug = property(_get_wikipedia_slug)


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
                
                # Assign all the child_node's sectors to this cluster.
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
        Returns the min/max amount of resources/sectors/related-tags per child-tag for this node.
        NOTE: self must be root, sector, or cluster.
        Ignores tags with no resources, no filters, or no societies.
        @param tags (optional) - a list of child tags to parse (for speeding up repeat queries).
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
        
        assert self.node_type.name == NodeType.ROOT or NodeType.SECTOR or self.node_type.name == NodeType.TAG_CLUSTER, 'self (%s, %s, %s) must be a sector or cluster' % (self.name, self.id, self.node_type.name)
        
        if tags is None:
            if self.node_type.name == NodeType.ROOT:
                tags = Node.objects.get_tags()
            else:
                tags = self.child_nodes
            # Filter out tags with no resources
            tags = Node.objects.get_extra_info(tags)
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

        return (min_resources, max_resources, min_sectors, max_sectors, min_related_tags, max_related_tags, min_societies, max_societies)

    def get_combined_sector_ranges(self, tags=None, show_empty_terms=False):
        """
        Returns the min/max combined score per tag for the given sector or cluster.
        NOTE: self must be a sector or cluster.
        Ignores tags with no resources, no filters, or no societies.
        @param self a sector or cluster self.
        @param tags (optional) - a list of child tags to parse (for speeding up repeat queries).
        @return a tuple (min, max).
        """
        assert self.node_type.name == NodeType.ROOT or NodeType.SECTOR or self.node_type.name == NodeType.TAG_CLUSTER, 'self (%s, %s, %s) must be a sector or cluster' % (self.name, self.id, self.node_type.name)
        if tags is None:
            if self.node_type.name == NodeType.ROOT:
                tags = Node.objects.get_tags()
            else:
                tags = self.child_nodes
            # Filter out tags with no resources
            tags = Node.objects.get_extra_info(tags)
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
        

class NodeSocietiesManager(models.Manager):
    def update_for_node(self, node, societies):
        societies_to_delete = self.filter(node=node).exclude(society__in=societies)
        societies_to_delete.delete()

        for society in societies:
            self.get_or_create(node=node, society=society)

class NodeSocieties(models.Model):
    node = models.ForeignKey('Node', related_name='node_societies')
    society = models.ForeignKey('Society', related_name='node_societies')
    date_created = models.DateTimeField(blank=True, null=True, default=None)
    is_machine_generated = models.BooleanField(default=False)

    objects = NodeSocietiesManager()
    
    class Meta:
        db_table = 'ieeetags_node_societies'
        ordering = ['node__name', 'society__name']

# ------------------------------------------------------------------------------

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
    related_terms = models.ManyToManyField('self', related_name='terms', null=True, blank=True)
    related_nodes = models.ManyToManyField('Node', related_name='nodes', blank=True)
    taxonomy_clusters = models.ManyToManyField('TaxonomyCluster', related_name='terms', blank=True)
    
    objects = TaxonomyTermManager()
    
    def __str__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.name)
    
    def __repr__(self):
        return str(self)
    
class TaxonomyClusterManager(models.Manager):
    pass

class TaxonomyCluster(models.Model):
    name = models.CharField(max_length=500)
    
    def __str__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.name)
    
    def __repr__(self):
        return str(self)

class SocietyManager(models.Manager):
    def getFromName(self, name):
        'Returns the society with the given name, or None.'
        return single_row_or_none(self.filter(name=name))
    
    def getFromAbbreviation(self, abbr):
        'Returns the society with the given abbreviation, or None.'
        return single_row_or_none(self.filter(abbreviation=abbr))
    
    def searchByNameSubstring(self, substring):
        'Returns any societies that match the search phrase.'
        if substring.strip() == '':
            return None
        return self.filter(name__icontains=substring)
    
    def getForUser(self, user):
        'Returns all societies that the given user has access to.'
        if user.get_profile().role == Profile.ROLE_ADMIN:
            return self.all()
        elif user.get_profile().role == Profile.ROLE_SOCIETY_ADMIN:
            return self.all()
        elif user.get_profile().role == Profile.ROLE_SOCIETY_MANAGER:
            return self.filter(users=user)
        else:
            raise Exception('Unknown role "%s"' % user.get_profile().role)
    
class Society(models.Model):
    name = models.CharField(max_length=500)
    abbreviation = models.CharField(max_length=20)
    url = models.CharField(blank=True,max_length=1000)
    logo_thumbnail = models.FileField(upload_to='images/sc_logos/thumbnail',blank=True)
    logo_full = models.FileField(upload_to='images/sc_logos/full',blank=True)
    
    users = models.ManyToManyField(User, related_name='societies', blank=True)
    
    objects = SocietyManager()
    
    def __unicode__(self):
        return self.name
    
    def get_tag_ranges(self, show_empty_terms=False):
        """
        Returns the min/max amount of resources/sectors/related-tags per tag for the given society.
        Ignores tags with no resources, no filters, or no societies.
        Returns a tuple:
            (min_resources,
            max_resources,
            min_sectors,
            max_sectors,
            min_related_tags,
            max_related_tags,
            min_societies,
            max_societies)
        """
        
        #log('get_tag_ranges()')
        
        # Filter out tags with no resources
        tags = Node.objects.get_extra_info(self.tags)
        
        min_resources = None
        max_resources = None
        min_sectors = None
        max_sectors = None
        min_related_tags = None
        max_related_tags = None
        min_societies = None
        max_societies = None
        
        for tag in tags:
            if (show_empty_terms and tag.is_taxonomy_term) or (tag.num_societies1 > 0 and tag.num_resources1 > 0):
            #if tag.num_resources1 > 0 and tag.num_societies1 > 0 and tag.num_filters1 > 0:
                if min_resources is None or tag.num_resources1 < min_resources:
                    min_resources = tag.num_resources1
                if max_resources is None or tag.num_resources1 > max_resources:
                    max_resources = tag.num_resources1

                if min_sectors is None or tag.num_sectors1 < min_sectors:
                    min_sectors = tag.num_sectors1
                if max_sectors is None or tag.num_sectors1 > max_sectors:
                    max_sectors = tag.num_sectors1

                if min_related_tags is None or tag.num_related_tags1 < min_related_tags:
                    min_related_tags = tag.num_related_tags1
                if max_related_tags is None or tag.num_related_tags1 > max_related_tags:
                    max_related_tags = tag.num_related_tags1

                if min_societies is None or tag.num_societies1 < min_societies:
                    min_societies = tag.num_societies1
                if max_societies is None or tag.num_societies1 > max_societies:
                    max_societies = tag.num_societies1

        #log('  min_resources: %s' % min_resources)
        #log('  max_resources: %s' % max_resources)
        #log('  min_sectors: %s' % min_sectors)
        #log('  max_sectors: %s' % max_sectors)
        #log('  min_related_tags: %s' % min_related_tags)
        #log('  max_related_tags: %s' % max_related_tags)
        #log('  min_societies: %s' % min_societies)
        #log('  max_societies: %s' % max_societies)
        
        #assert False
        
        return (min_resources, max_resources, min_sectors, max_sectors, min_related_tags, max_related_tags, min_societies, max_societies)
    
    def get_combined_ranges(self, show_empty_terms=False):
        """
        Returns the min/max combined score per tag for the given society.
        Ignores tags with no resources, no filters, or no societies.
        @return a tuple (min, max)
        """
        
        #p = Profiler('get_combined_sector_ranges()')
        
        #log('get_combined_sector_ranges()')
        
        #p.tick('get_extra_info()')
        
        # Filter out tags with no resources
        tags = Node.objects.get_extra_info(self.tags)
        
        min_score = None
        max_score = None
        
        #p.tick('start loop')
        
        for tag in tags:
            # Ignore all hidden tags
            #if (show_empty_terms and tag['is_taxonomy_term']) or (tag['num_societies1'] > 0 and tag['num_resources1'] > 0):
            if (show_empty_terms and tag.is_taxonomy_term) or (tag.num_societies1 > 0 and tag.num_resources1 > 0):
            #if tag.num_resources1 > 0 and tag.num_societies1 > 0 and tag.num_filters1 > 0:
                if min_score is None or tag.score1 < min_score:
                    min_score = tag.score1
                
                if max_score is None or tag.score1 > max_score:
                    max_score = tag.score1
        
        #log('  min_score: %s' % min_score)
        #log('  max_score: %s' % max_score)
        
        return (min_score, max_score)    
        
    class Meta:
        ordering = ['name']

# ------------------------------------------------------------------------------
    
class ResourceTypeManager(NamedTypeManager):
    pass

class ResourceType(NamedType):
    'NamedType model for each of the available resource types: conference, expert, periodical, standard.'
    objects = ResourceTypeManager()
    
    CONFERENCE = 'conference'
    EXPERT = 'expert'
    PERIODICAL = 'periodical'
    STANDARD = 'standard'

class ResourceManager(models.Manager):
    def get_conferences(self):
        'Returns all conferences.'
        resource_type = ResourceType.objects.getFromName(ResourceType.CONFERENCE)
        return self.filter(resource_type=resource_type)
        
    def get_standards(self):
        'Returns all standards.'
        resource_type = ResourceType.objects.getFromName(ResourceType.STANDARD)
        return self.filter(resource_type=resource_type)
        
    def get_periodicals(self):
        'Returns all periodicals.'
        resource_type = ResourceType.objects.getFromName(ResourceType.PERIODICAL)
        return self.filter(resource_type=resource_type)
        
    def getForNode(self, node, resourceType=None):
        '''
        Gets all resources for the given node.  Optionally filter by resource type.
        @param node: The node to search for.
        @param resourceType: (Optional) The type of resource to filter by.
        '''
        if type(resourceType) is str:
            resourceType = ResourceType.objects.getFromName(resourceType)
        if resourceType is not None:
            return self.filter(nodes=node, resource_type=resourceType)
        else:
            return self.filter(nodes=node)
    
    def getNumForNode(self, node, resourceType=None):
        '''
        Get number of resources for the given node.
        @param node: The node to search for.
        @param resourceType: (Optional) The type of resource to filter by.
        '''
        return len(self.getForNode(node, resourceType))
        
    def getForSociety(self, society, resourceType=None):
        '''
        Get all resources for the society.
        @param node: The node to search for.
        @param resourceType: (Optional) The type of resource to filter by.
        '''
        if type(resourceType) is str:
            resourceType = ResourceType.objects.getFromName(resourceType)
        if resourceType is not None:
            return self.filter(society=society, resource_type=resourceType)
        else:
            return self.filter(society=society)
    
    def getNumForSociety(self, society, resourceType=None):
        '''
        Get the number of resources for the society.
        @param node: The node to search for.
        @param resourceType: (Optional) The type of resource to filter by.
        '''
        return len(self.getForSociety(society, resourceType))
    
    def searchByNameSubstring(self, substring):
        'Return resources that match the search string.'
        if substring.strip() == '':
            return None
        return self.filter(name__icontains=substring)
    
    def get_conference_series(self):
        """
        Returns a list of all distinct conference series codes and the number of conferences in each series (ignores blank fields).
        Returns:
            [
                (conference_series, num_in_series),
                ...
            ]
        """
        conference_type = ResourceType.objects.getFromName(ResourceType.CONFERENCE)
        cursor = connection.cursor()
        cursor.execute("""
            SELECT conference_series, COUNT(id) AS num_in_series
            FROM ieeetags_resource
            WHERE conference_series <> ''
            AND resource_type_id = %s
            GROUP BY conference_series
            """, [conference_type.id])
        return cursor.fetchall()
    
    def get_current_conference_for_series(self, series):
        """
        Return the current conference for the given series.
        This defined as the next upcoming conference (>= now).
        If there is no upcoming, then use the last conference.
        """
        #print 'get_current_conference_for_series()'
        #print '  series: %s' % series
        current_year = datetime.today().year
        #print '  current_year: %s' % current_year
        resources = Resource.objects.filter(resource_type__name=ResourceType.CONFERENCE, conference_series=series, year__gte=current_year).order_by('date', 'year', 'id')
        #print '  resources.count(): %s' % resources.count()
        if resources.count():
            # Use the next future resource
            #print '  using next future'
            return resources[0]
        else:
            # Use the most-recent past resource
            #print '  using most recent'
            resources = Resource.objects.filter(resource_type__name=ResourceType.CONFERENCE, conference_series=series, year__lt=current_year).order_by('-date', '-year', '-id')
            #print '  resources.count(): %s' % resources.count()
            if resources.count():
                return resources[0]
            else:
                # Check if any resources have a NULL year
                resources = Resource.objects.filter(resource_type__name=ResourceType.CONFERENCE, conference_series=series, year=None).order_by('-date', '-year', '-id')
                if resources.count():
                    return resources[0]
                else:
                    # There are no conferences in this series
                    return None
    
    def get_non_current_conferences_for_series(self, series, current_conference=None):
        'Get all non-current conferences in the given series.'
        #print 'get_non_current_conferences_for_series()'
        #print '  series: %s' % series
        #print '  current_conference: %s' % current_conference
        if current_conference is None:
            current_conference = self.get_current_conference_for_series(series)
        #print '  current_conference: %s' % current_conference
        # Get the other conferences in the series
        return Resource.objects.filter(conference_series=series).exclude(id=current_conference.id).all()

class Resource(models.Model):
    STANDARD_STATUS_PROJECT = 'project'
    STANDARD_STATUS_PUBLISHED = 'published'
    STANDARD_STATUS_WITHDRAWN = 'withdrawn'
    
    STANDARD_STATUSES = [
        STANDARD_STATUS_PROJECT,
        STANDARD_STATUS_PUBLISHED,
        STANDARD_STATUS_WITHDRAWN,
    ]
    
    URL_STATUS_GOOD = 'good'
    URL_STATUS_BAD = 'bad'
    URL_STATUS_CHOICES = [
        (URL_STATUS_GOOD, 'Good'),
        (URL_STATUS_BAD, 'Bad'),
    ]
    
    resource_type = models.ForeignKey(ResourceType)
    ieee_id = models.CharField(max_length=500,blank=True, null=True)
    name = models.CharField(max_length=500)
    description = models.CharField(blank=True, max_length=5000)
    url = models.CharField(blank=True, max_length=1000)
    year = models.IntegerField(blank=True, null=True)
    standard_status = models.CharField(blank=True, max_length=100)
    priority_to_tag = models.BooleanField()
    completed = models.BooleanField()
    keywords = models.CharField(max_length=5000, blank=True)
    'This field is a text field, displayed to society managers on Edit Resource page to help them tag.  Not used in any other way.'
    conference_series = models.CharField(max_length=100, blank=True)
    'Optional.  All conferences with the same "conference_series" are grouped together as a series.'
    date = models.DateField(null=True, blank=True)
    pub_id = models.CharField(max_length=1000, blank=True)
    'Used for Conferences and Standards (optional).  Matches IEEE Xpore PubID field for matching resources during xplore import.'
    
    url_status = models.CharField(blank=True, max_length=100, choices=URL_STATUS_CHOICES)
    'Reflects the status of this URL.  Can be "good", "bad", or None (not yet checked).'
    url_date_checked = models.DateTimeField(null=True, blank=True)
    url_error = models.CharField(null=True, blank=True, max_length=1000)
    'The error (if any) that occured when checking this URL.'
    
    nodes = models.ManyToManyField(Node, related_name='resources', through='ResourceNodes')
    societies = models.ManyToManyField(Society, related_name='resources')
    
    objects = ResourceManager()
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ['resource_type__name', 'name']
        
class ResourceNodes(models.Model):
    resource = models.ForeignKey(Resource, related_name='resource_nodes')
    node = models.ForeignKey(Node, related_name='resource_nodes')
    date_created = models.DateTimeField(blank=True, null=True, default=None)
    is_machine_generated = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'ieeetags_resource_nodes'
        ordering = ['node__name', 'resource__name']

# ------------------------------------------------------------------------------

class FilterManager(NamedValueTypeManager):
    def get_from_name_list(self, names):
        'Returns a list of filters whose names match the given list of names.'
        results = self.filter(name__in=names)
        if len(results) != len(names):
            raise Exception('Did not find matches for all filters:\nnames: %s\nresults: %s' % (names, results))
        return results

class Filter(NamedValueType):
    EMERGING_TECHNOLOGIES = 'emerging_technologies'
    FOUNDATION_TECHNOLOGIES = 'foundation_technologies'
    HOT_TOPICS = 'hot_topics'
    MARKET_AREAS = 'market_areas'
    
    FILTERS = [
        EMERGING_TECHNOLOGIES,
        FOUNDATION_TECHNOLOGIES,
        HOT_TOPICS,
        MARKET_AREAS,
    ]
    
    objects = FilterManager()
    
    def __unicode__(self):
        return self.name

# ------------------------------------------------------------------------------
  
class PermissionManager(models.Manager):
    'This object stores all permission-related functions.  All new permission checks should go here.'
    
    def user_can_edit_society(self, user, society): 
        'Checks if a user can edit a society.'
        if user.is_superuser:
            return True
        elif society in user.societies.all():
            # If user is associated with the society, allow editing
            return True
        else:
            return self._user_has_permission(user, Permission.USER_CAN_EDIT_SOCIETY, society)
    
    def user_can_edit_society_name(self, user, society):
        'Only superusers (admins) can edit a society name.'
        if user.is_superuser:
            return True
        else:
            return False
    
    def _user_has_permission(self, user, permission_type, object):
        'Generic helper function to check if the user has the a certain permission for an object.'
        object_type = ContentType.objects.get_for_model(object)
        results = self.filter(user=user, object_id=object.id, object_type=object_type, permission_type=permission_type)
        return len(results) > 0

class Permission(models.Model):
    USER_CAN_EDIT_SOCIETY = 'user_can_edit_society'
    
    user = models.ForeignKey(User, related_name='permissions')
    object_type = models.ForeignKey(ContentType, related_name='permissions')
    object_id = models.PositiveIntegerField()
    object = generic.GenericForeignKey('object_type', 'object_id')    
    permission_type = models.CharField(max_length=1000)
    
    objects = PermissionManager()

# ------------------------------------------------------------------------------

class Profile(models.Model):
    'A user\'s profile.  By default, a profile is created whenever a user is created.'
    ROLE_ADMIN = 'admin'
    ROLE_SOCIETY_ADMIN = 'society_admin'
    ROLE_SOCIETY_MANAGER = 'society_manager'
    ROLE_END_USER = 'end_user'
    
    ROLES = [
        ROLE_ADMIN,
        ROLE_SOCIETY_ADMIN,
        ROLE_SOCIETY_MANAGER,
        ROLE_END_USER,
    ]
    
    user = models.ForeignKey(User, unique=True)
    role = models.CharField(choices=list_to_choices(ROLES), max_length=1000)
    reset_key = models.CharField(max_length=1000, null=True)
    last_login_time = models.DateTimeField(blank=True, null=True)
    last_logout_time = models.DateTimeField(blank=True, null=True)
    copied_resource = models.ForeignKey(Resource, related_name='copied_users', null=True, blank=True)
    'This stores the source resource for copy & pasting tags.'

# ------------------------------------------------------------------------------

class UserManager:
    @staticmethod
    def get_admins():
        return User.objects.filter(profile__role=Profile.ROLE_ADMIN)
    
    @staticmethod
    def get_society_managers():
        return User.objects.filter(profile__role=Profile.ROLE_SOCIETY_MANAGER)
    
    @staticmethod
    def get_end_users():
        return User.objects.filter(profile__role=Profile.ROLE_END_USER)
    
    @staticmethod
    def get_users_by_login_date():
        "Return users ordered by their last login time."
        return User.objects.filter(profile__last_login_time__isnull=False).order_by('-profile__last_login_time')

# ------------------------------------------------------------------------------

def _create_profile_for_user(sender, instance, signal, created, *args, **kwargs):
    "Automatically creates a profile for each newly created user.  Uses signals to detect user creation."
    if created:
        profile = Profile(user=instance)
        profile.save()

post_save.connect(_create_profile_for_user, sender=User)

def get_user_from_username(username):
    return single_row_or_none(User.objects.filter(username=username))

def get_user_from_email(email):
    return single_row_or_none(User.objects.filter(email=email))

# ------------------------------------------------------------------------------

class FailedLoginLogManager(models.Manager):
    
    def check_if_disabled(self, username, ip):
        "Return True if a given username or ip has been disabled."
        #log('check_if_disabled()')
        #log('  username: %s' % username)
        #log('  ip: %s' % ip)
        ##log('  FailedLoginLog.DISABLE_ACCOUNT_TIME: %s' % FailedLoginLog.DISABLE_ACCOUNT_TIME)
        before = datetime.fromtimestamp(time.time() - FailedLoginLog.DISABLE_ACCOUNT_TIME)
        #log('  before: %s' % before)
        ##log('  datetime.now(): %s' % datetime.now())
        if username is not None:
            num = self.filter(
                Q(username=username) | Q(ip=ip),
                disabled=True,
                date_created__gt=before,
            ).count()
            #log('  num: %s' % num)
            return num > 0
        else:
            num = self.filter(
                ip=ip,
                disabled=True,
                date_created__gt=before,
            ).count()
            #log('  num: %s' % num)
            return num > 0
    
    def add_and_check_if_disabled(self, username, ip):
        "Records a bad login and checks if the max has been reached.  Returns True if user is under the limit, and False if user is over the limit."
        self._add_failed_login(username, ip)
        return self.check_if_disabled(username, ip)
    
    def _add_failed_login(self, username, ip):
        "Adds a bad login entry and disables an account if necessary."
        
        #log('_add_failed_login()')
        #log('  username: %s' % username)
        #log('  ip: %s' % ip)
        
        # Check if there have been too many bad logins (including this one)
        before = datetime.fromtimestamp(time.time() - FailedLoginLog.FAILED_LOGINS_TIME)
        num_failed_logins = self.filter(
            Q(username=username) | Q(ip=ip),
            date_created__gt = before,
        ).count()
        #log('  num_failed_logins: %s' % num_failed_logins)
        
        if num_failed_logins >= FailedLoginLog.FAILED_LOGINS_MAX - 1:
            disabled = True
        else:
            disabled = False
            
        #log('  disabled: %s' % disabled)
        
        # Add a log entry for this failed entry
        log = self.create(
            username = username,
            ip = ip,
            disabled = disabled,
        )
        log.save()
        
        return disabled
        
class FailedLoginLog(models.Model):
    'Keeps track of past failed logins.  Suspends future logins for a certain time if there are too many failed logins.'
    
    # This is the number of seconds in the past to check for bad logins
    FAILED_LOGINS_TIME = 10 * 60
    # The number of minutes to disable an account for
    DISABLE_ACCOUNT_TIME = 10 * 60
    # Max number of bad logins within the FAILED_LOGIN_TIME above
    FAILED_LOGINS_MAX = 10
    
    username = models.CharField(max_length=30)
    ip = models.CharField(max_length=16)
    disabled = models.BooleanField()
    date_created = models.DateTimeField(auto_now_add=True)
    
    objects = FailedLoginLogManager()

class UrlCheckerLog(models.Model):
    'Keeps track of the current URL-checking thread\'s status.'
    date_started = models.DateTimeField(auto_now_add=True)
    date_ended = models.DateTimeField(blank=True, null=True)
    date_updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=1000)

# ------------------------------------------------------------------------------

class ProfileLog(models.Model):
    'Debugging class, used to keep track of profiling pages.'
    url = models.CharField(max_length=1000)
    elapsed_time = models.FloatField()
    user_agent = models.CharField(max_length=1000)
    category = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    def short_user_agent(self):
        short_user_agent1 = self.user_agent
        import re
        match = re.search(r'Chrome/([\d.]+)', self.user_agent)
        if match:
            short_user_agent1 = 'Chrome %s' % (match.group(1))
        else:
            match = re.search(r'Safari/([\d.]+)', self.user_agent)
            if match:
                short_user_agent1 = 'Safari %s' % (match.group(1))
            else:
                match = re.search(r'Firefox/([\d.]+)', self.user_agent)
                if match:
                    short_user_agent1 = 'Firefox %s' % (match.group(1))
                else:
                    match = re.search(r'MSIE ([\d.]+)', self.user_agent)
                    if match:
                        short_user_agent1 = 'MSIE %s' % (match.group(1))
        return short_user_agent1
        
    def __str__(self):
        return '<%s: %s, %s, %s>' % (self.__class__.__name__, self.url, self.elapsed_time, self.short_user_agent())

PROCESS_CONTROL_TYPES = Enum(
    'XPLORE_IMPORT',
)

class ProcessControl(models.Model):
    'Controls and stores information for a long-running process.'
    
    'The type (ie. name) of process.  Should only be one per name at any given time.'
    type = models.CharField(max_length=100, choices=util.make_choices(PROCESS_CONTROL_TYPES))
    'Log messages output by the process (stored in this DB field only).'
    log = models.CharField(max_length=1000, blank=True)
    'Filename for the logfile written by the process.'
    log_filename = models.CharField(max_length=1000, blank=True, default='')
    'Signal the process to quit.'
    is_alive = models.BooleanField(default=True)
    'Process will update periodically to the current time.'
    date_updated = models.DateTimeField(null=True, blank=True)
    
    # Process-type specific fields.
    'This is updated the most-recently processed tag by the Xplore Import script, allows resuming.'
    last_processed_tag = models.ForeignKey(Node, null=True, blank=True, default=None)

    date_created = models.DateTimeField(auto_now_add=True)

def urlencode_sorted(d):
    import urllib
    result = []
    for name in sorted(d.keys()):
        result.append((name, d[name]))
    return urllib.urlencode(result)

class CacheManager(models.Manager):
    def get(self, name, params):
        if type(params) is dict:
            params = urlencode_sorted(params)
        try:
            return super(CacheManager, self).get(name=name, params=params)
        except Cache.DoesNotExist:
            return None
        except MultipleObjectsReturned:
            idtosave = super(CacheManager, self).filter(name=name, params=params).order_by('-id')[0:1][0].id
            super(CacheManager, self).filter(name=name, params=params).exclude(id=idtosave).delete()
            return super(CacheManager, self).get(id=idtosave)
             
    def set(self, name, params, content):
        if type(params) is dict:
            params = urlencode_sorted(params)
        cache = self.get(name, params)
        if not cache:
            cache = Cache()
            cache.name = name
            cache.params = params
        cache.content = content
        cache.save()
        return cache
    
    def delete(self, name, params=None):
        if type(params) is dict:
            params = urlencode_sorted(params)
        if params is None:
            caches = self.filter(name=name)
            caches.delete()
        else:
            cache = self.get(name, params)
            if cache:
                cache.delete()
    
class Cache(models.Model):
    name = models.CharField(max_length=100)
    params = models.CharField(max_length=1000, blank=True)
    content = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    
    objects = CacheManager()
    
    def __str__(self):
        return '<Cache: %s, %s, %s>' % (self.name, self.params, len(self.content))
