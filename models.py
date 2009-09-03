
from django.contrib.auth.models import User, UserManager
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.db import models
from django.db.models import Q
from django.db.models import Q
from django.db.models.signals import post_save
from datetime import datetime
from logging import debug as log
import time
import string
import settings

def single_row(results, message=None):
    if len(results) != 1:
        if message is None:
            raise Exception('Require 1 row, found %i.' % len(results))
        else:
            raise Exception('%s\nRequire 1 row, found %i' % (message, len(results)))
    return results[0]

def single_row_or_none(results):
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
        types = self.filter(name=name)
        if len(types) != 1:
            raise Exception('Found %d %s for name "%s", looking for 1 result' % (len(types), self.__class__, name))
        return types[0]

class NamedType(models.Model):
    name = models.CharField(max_length=50)
    
    def __unicode__(self):
        return self.name
    class Meta:
        abstract = True

# ------------------------------------------------------------------------------

class NamedValueTypeManager(NamedTypeManager):
    def getFromValue(self, value):
        types = self.filter(value=value)
        return single_row(types)

class NamedValueType(NamedType):
    value = models.CharField(max_length=500)
    
    def __unicode__(self):
        return '%s (%s)' % (self.name, self.value)
    class Meta:
        abstract = True

# ------------------------------------------------------------------------------

class NodeTypeManager(NamedTypeManager):
    pass

class NodeType(NamedType):
    TAG_CLUSTER = 'tag_cluster'
    TAG = 'tag'
    SECTOR = 'sector'
    ROOT = 'root'
    
    objects = NodeTypeManager()
    
class NodeManager(models.Manager):
    
    def create(self, **kwargs):
        if 'name' in kwargs:
            #print 'got name'
            kwargs['name'] = string.capwords(kwargs['name'])
        return models.Manager.create(self, **kwargs)
    
    def create_tag(self, **kwargs):
        if 'name' in kwargs:
            kwargs['name'] = string.capwords(kwargs['name'])
        kwargs['node_type'] = NodeType.objects.getFromName(NodeType.TAG)
        return models.Manager.create(self, **kwargs)
        
    def create_cluster(self, name, sector):
        cluster = super(NodeManager, self).create(name=name, node_type = NodeType.objects.getFromName(NodeType.TAG_CLUSTER))
        cluster.parents = [sector]
        cluster.save()
        return cluster
        
    def getNodesForType(self, node_type):
        if type(node_type) is str:
            node_type = NodeType.objects.getFromName(node_type)
        return self.filter(node_type=node_type)
    
    def getRoot(self):
        rootType = NodeType.objects.getFromName('root')
        nodes = self.filter(node_type=rootType)
        if len(nodes) != 1:
            raise Exception('Require 1 root node, found ' + str(len(nodes)))
        return nodes[0]
    
    def getSectors(self):
        return self.filter(node_type__name=NodeType.SECTOR)
    
    def get_sector_by_name(self, name):
        sector_type = NodeType.objects.getFromName(NodeType.SECTOR)
        return single_row(self.filter(name=name, node_type=sector_type), 'Looking up sector "%s"' % name)
    
    def get_sectors_from_list(self, names):
        'Returns a list of sectors whose names match the given list of names.'
        sectorType = NodeType.objects.getFromName('sector')
        results = self.filter(name__in=names, node_type=sectorType)
        if len(results) != len(names):
            raise Exception('Did not find matches for all sectors:\nnames: %s\nresults: %s' % (names, results))
        return results
    
    def getFirstSector(self):
        return self.getSectors()[0]
    
    # DEPRECATED: use get_tags()
    def getTags(self):
        return self.get_tags()
    
    def get_tags(self):
        "Returns all tags."
        tag_type = NodeType.objects.getFromName('tag')
        return self.filter(node_type=tag_type)
    
    #def getChildNodes(self, node):
    #    return self.filter(parent=node)
    
    def getTagsByName(self, name):
        tag_type = NodeType.objects.getFromName('tag')
        return self.filter(name=name, node_type=tag_type)
    
    #def getTagByName(self, sector, tagName):
    #    tag_type = NodeType.objects.getFromName('tag')
    #    return single_row_or_none(self.filter(name=tagName, parent=sector, node_type=tag_type))
    
    def get_tag_by_name(self, tag_name):
        #print 'get_tag_by_name()'
        #print '  tag_name:', tag_name
        tag_type = NodeType.objects.getFromName('tag')
        return single_row_or_none(self.filter(name=tag_name, node_type=tag_type))
        
    def getRandomTag(self):
        tag_type = NodeType.objects.getFromName('tag')
        return self.filter(node_type=tag_type).order_by('?')[0]
    
    #def get_random_related_tags(self, tag, count):
    #    tag_type = NodeType.objects.getFromName('tag')
    #    return self.filter(node_type=tag_type,parent=tag.parent).exclude(id=tag.id).order_by('?')[:count]
    
    def getFilteredNodes(self, nodeId, filterIds, sort):
        return []
    
    #def getRelatedSectors(self, tag):
    #    # Get all related sectors (including the given tag's sector)
    #    relatedSectors = self.filter(node_type__name=NodeType.SECTOR, child_nodes__name=tag.name)#.exclude(id=tag.parent.id)
    #    #print '  relatedSectors:', relatedSectors
    #    #print '  len(relatedSectors):', len(relatedSectors)
    #    return relatedSectors
    
    def get_resource_range(self, sector):
        "Returns the min/max amount of resources-per-tag for the given sector."

        
        resource_counts = [tag.resources.count() for tag in sector.child_nodes.all()]
        if len(resource_counts) == 0:
            min_resources = None
            max_resources = None
        else:
            min_resources = min(resource_counts)
            max_resources = max(resource_counts)
        
        return (min_resources, max_resources)

    def get_sector_ranges(self, node):
        """
        Returns the min/max amount of resources/sectors/related-tags per tag for the given sector or cluster.
        NOTE: node must be a sector or cluster.
        Ignores tags with no resources, no filters, or no societies.
        Returns a tuple:
            (min_resources,
            max_resources,
            min_sectors,
            max_sectors,
            min_related_tags,
            max_related_tags)
        """
        
        log('get_sector_ranges()')
        
        assert node.node_type.name == NodeType.SECTOR or node.node_type.name == NodeType.TAG_CLUSTER, 'node (%s, %s, %s) must be a sector or cluster' % (node.name, node.id, node.node_type.name)
        
        tags = node.child_nodes
        
        # Filter out tags with no resources
        tags = self.get_extra_info(tags)
        
        min_resources = None
        max_resources = None
        min_sectors = None
        max_sectors = None
        min_related_tags = None
        max_related_tags = None
        
        for tag in tags:
            if tag.num_resources1 > 0 and tag.num_societies1 > 0 and tag.num_filters1 > 0:
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

        log('  min_resources: %s' % min_resources)
        log('  max_resources: %s' % max_resources)
        log('  min_sectors: %s' % min_sectors)
        log('  max_sectors: %s' % max_sectors)
        log('  min_related_tags: %s' % min_related_tags)
        log('  max_related_tags: %s' % max_related_tags)
        
        return (min_resources, max_resources, min_sectors, max_sectors, min_related_tags, max_related_tags)
    
    def get_combined_sector_ranges(self, node):
        """
        Returns the min/max amount of resources/sectors/related-tags per tag for the given sector or cluster.
        NOTE: node must be a sector or cluster.
        Ignores tags with no resources, no filters, or no societies.
        
        This only returns the min and max, since it reflectse combined scores.
        
        Returns a tuple:
            (min, max)
        """
        
        log('get_combined_sector_ranges()')
        
        assert node.node_type.name == NodeType.SECTOR or node.node_type.name == NodeType.TAG_CLUSTER, 'node (%s, %s, %s) must be a sector or cluster' % (node.name, node.id, node.node_type.name)
        
        tags = node.child_nodes
        
        # Filter out tags with no resources
        tags = self.get_extra_info(tags)
        
        min_score = None
        max_score = None
        
        for tag in tags:
            # Ignore all hidden tags
            if tag.num_resources1 > 0 and tag.num_societies1 > 0 and tag.num_filters1 > 0:
                
                score = tag.get_score()
                log('    score: %s' % score)
                
                if min_score is None or score < min_score:
                    min_score = score
                
                if max_score is None or score > max_score:
                    max_score = score

        log('  min_score: %s' % min_score)
        log('  max_score: %s' % max_score)
        
        return (min_score, max_score)
    
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
    
    def get_related_tag_range(self, sector):
        "Returns the min/max amount of related_tags-per-tag for the given sector."
        
        related_tag_counts = [tag.related_tags.count() for tag in sector.child_nodes.all()]
        if len(related_tag_counts) == 0:
            min_related_tags = None
            max_related_tags = None
        else:
            min_related_tags = min(related_tag_counts)
            max_related_tags = max(related_tag_counts)
        
        return (min_related_tags, max_related_tags)
    
    def searchTagsByNameSubstring(self, substring, sector_ids=None, exclude_tag_id=None, society_id=None):
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
        return self.filter(node_type=NodeType.objects.getFromName(NodeType.TAG_CLUSTER)).all()
    
    def get_cluster(self, clusterId):
        return single_row_or_none(self.filter(id=clusterId, node_type__name=NodeType.TAG_CLUSTER))
    
    def get_cluster_by_name(self, cluster_name, sector_name):
        return single_row_or_none(
            self.filter(
                node_type__name=NodeType.TAG_CLUSTER,
                name=cluster_name,
                parents__name=sector_name,
            )
        )
    
    def add_tag_to_cluster(self, cluster, tag):
        cluster.child_nodes.add(tag)
        for filter in tag.filters.all():
            cluster.filters.add(filter)
        cluster.save()
    
    def remove_tag_from_cluster(self, cluster, tag):
        cluster.child_nodes.remove(tag)
        # Update the list of filters for this cluster
        cluster.filters.clear()
        for tag in cluster.get_tags():
            for filter in tag.filters.all():
                cluster.filters.add(filter)
        cluster.save()
    
    def get_extra_info(self, queryset, order_by=None):
        """
        Returns the queryset with extra columns:
            num_resources1
            num_societies1
            num_filters1
            num_sectors1
            num_related_tags1
            num_parents1
        """
        sector_node_type_id = NodeType.objects.getFromName(NodeType.SECTOR).id
        cluster_node_type_id = NodeType.objects.getFromName(NodeType.TAG_CLUSTER).id
        return queryset.extra(
            select={
                'num_resources1': 'SELECT COUNT(*) FROM ieeetags_resource_nodes WHERE ieeetags_resource_nodes.node_id = ieeetags_node.id',
                'num_societies1': 'SELECT COUNT(*) FROM ieeetags_node_societies WHERE ieeetags_node_societies.node_id = ieeetags_node.id',
                'num_filters1': 'SELECT COUNT(*) FROM ieeetags_node_filters WHERE ieeetags_node_filters.node_id = ieeetags_node.id',
                'num_sectors1': 'SELECT COUNT(*) FROM ieeetags_node_parents INNER JOIN ieeetags_node as parent on ieeetags_node_parents.to_node_id = parent.id WHERE ieeetags_node_parents.from_node_id = ieeetags_node.id AND parent.node_type_id = %s' % (sector_node_type_id),
                #'num_clusters1': 'SELECT COUNT(*) FROM ieeetags_node_parents INNER JOIN ieeetags_node as parent on ieeetags_node_parents.to_node_id = parent.id WHERE ieeetags_node_parents.from_node_id = ieeetags_node.id AND parent.node_type_id = %s' % (cluster_node_type_id),
                # TODO: Some of the related tags will be hidden (no resources, no filters, etc), so this count is off
                'num_related_tags1': 'SELECT COUNT(*) FROM ieeetags_node_related_tags WHERE ieeetags_node_related_tags.from_node_id = ieeetags_node.id',
                'num_parents1': 'SELECT COUNT(*) FROM ieeetags_node_parents WHERE ieeetags_node_parents.from_node_id = ieeetags_node.id',
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
                return obj.get_score()
            else:
                return -obj.get_score()
        list1 = list(queryset)
        list1.sort(key=sort_function)        
        return list1
    
class Node(models.Model):
    name = models.CharField(max_length=500)
    #parent = models.ForeignKey('Node', related_name='child_nodes', null=True, blank=True)
    parents = models.ManyToManyField('self', symmetrical=False, related_name='child_nodes', null=True, blank=True)
    node_type = models.ForeignKey(NodeType)
    societies = models.ManyToManyField('Society', related_name='tags', blank=True)
    filters = models.ManyToManyField('Filter', related_name='nodes')

    related_tags = models.ManyToManyField('self', null=True, blank=True)
    
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
    
    def get_full_cluster_name(self):
        assert self.node_type.name == NodeType.TAG_CLUSTER, 'Node "%s" is not a cluster' % self.name
        return '%s (%s)' % (self.name, self.get_sector().name)
    
    def get_sectors(self):
        return self.parents.filter(node_type__name=NodeType.SECTOR)
    
    def get_parent_clusters(self):
        return self.parents.filter(node_type__name=NodeType.TAG_CLUSTER)
    
    def get_child_clusters(self):
        return self.child_nodes.filter(node_type__name=NodeType.TAG_CLUSTER)
    
    def get_tags(self):
        "Returns all tags for this node."
        return self.child_nodes.filter(node_type__name=NodeType.TAG)
    
    def get_tags_non_clustered(self):
        "Returns all tags that are not clustered for this node."
        #print 'get_tags_non_clustered()'
        tags = self.child_nodes.filter(node_type__name=NodeType.TAG)
        #print '  tags.count(): %s' % tags.count()
        tags = tags.exclude(parents__node_type__name=NodeType.TAG_CLUSTER)
        #print '  tags.count(): %s' % tags.count()
        return tags
    
    def get_tags_and_clusters(self):
        "Returns any clusters and non-clustered child tags."
        assert self.node_type.name == NodeType.SECTOR, 'get_tags_and_clusters() only works for sectors.'
        return self.child_nodes.exclude(parents__node_type__name=NodeType.TAG_CLUSTER)
    
    def get_sector(self):
        "Only valid for clusters.  Gets a cluster's parent sector, ensuring that there is exactly 1 parent."
        assert self.node_type.name == NodeType.TAG_CLUSTER, 'Node "%s" is not a cluster' % self.name
        assert self.parents.count() == 1, 'Node "%s" has %s parents' % (self.name, self.parents.count())
        return self.parents.all()[0]
    
    def cluster_update_filters(self):
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
        count = 0
        for related_tag in self.related_tags.all():
            if related_tag.filters.count() > 0 and related_tag.resources.count() > 0:
                count += 1
        return count
    
    def get_score(self):
        """
        Returns the combined popularity score for this tag.
        NOTE: This node must have been called with get_extra_info() for this function to work.
        """
        if self.node_type.name == NodeType.TAG:
            # Tag
            return self.num_resources1 + self.num_sectors1 + self.num_related_tags1
        elif self.node_type.name == NodeType.TAG_CLUSTER:
            # Cluster
            return self.num_resources1 + self.num_sectors1
        else:
            raise Exception('Unknown node type "%s"' % self.node_type.name)
        
    class Meta:
        ordering = ['name']

# ------------------------------------------------------------------------------

class SocietyManager(models.Manager):
    def getRandom(self):
        return self.all().order_by('?')[0]
    
    def getFromName(self, name):
        return single_row_or_none(self.filter(name=name))
    
    def getFromAbbreviation(self, abbr):
        return single_row_or_none(self.filter(abbreviation=abbr))
    
    def searchByNameSubstring(self, substring):
        if substring.strip() == '':
            return None
        return self.filter(name__icontains=substring)
    
    def getForUser(self, user):
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
    
    users = models.ManyToManyField(User, related_name='societies', blank=True)
    
    objects = SocietyManager()
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

# ------------------------------------------------------------------------------
    
class ResourceTypeManager(NamedTypeManager):
    pass

class ResourceType(NamedType):
    objects = ResourceTypeManager()
    
    CONFERENCE = 'conference'
    EXPERT = 'expert'
    PERIODICAL = 'periodical'
    STANDARD = 'standard'

class ResourceManager(models.Manager):
    def get_conferences(self):
        resource_type = ResourceType.objects.getFromName(ResourceType.CONFERENCE)
        return self.filter(resource_type=resource_type)
        
    def get_standards(self):
        resource_type = ResourceType.objects.getFromName(ResourceType.STANDARD)
        return self.filter(resource_type=resource_type)
        
    def get_periodicals(self):
        resource_type = ResourceType.objects.getFromName(ResourceType.PERIODICAL)
        return self.filter(resource_type=resource_type)
        
    def getForNode(self, node, resourceType=None):
        if type(resourceType) is str:
            resourceType = ResourceType.objects.getFromName(resourceType)
        if resourceType is not None:
            return self.filter(nodes=node, resource_type=resourceType)
        else:
            return self.filter(nodes=node)
    
    def getNumForNode(self, node, resourceType=None):
        return len(self.getForNode(node, resourceType))
        
    def getForSociety(self, society, resourceType=None):
        if type(resourceType) is str:
            resourceType = ResourceType.objects.getFromName(resourceType)
        if resourceType is not None:
            return self.filter(society=society, resource_type=resourceType)
        else:
            return self.filter(society=society)
    
    def getNumForSociety(self, society, resourceType=None):
        return len(self.getForSociety(society, resourceType))
    
    def searchByNameSubstring(self, substring):
        if substring.strip() == '':
            return None
        return self.filter(name__icontains=substring)
    
    #def get_random(self, count):
    #    return self.all().order_by('?')[:count]

class Resource(models.Model):
    STANDARD_STATUS_PROJECT = 'project'
    STANDARD_STATUS_PUBLISHED = 'published'
    STANDARD_STATUS_WITHDRAWN = 'withdrawn'
    
    STANDARD_STATUSES = [
        STANDARD_STATUS_PROJECT,
        STANDARD_STATUS_PUBLISHED,
        STANDARD_STATUS_WITHDRAWN,
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
    
    nodes = models.ManyToManyField(Node, related_name='resources')
    societies = models.ManyToManyField(Society, related_name='resources')
    
    objects = ResourceManager()
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ['resource_type__name', 'name']

# ------------------------------------------------------------------------------

class FilterManager(NamedValueTypeManager):
    def getRandom(self):
        return single_row_or_none(self.order_by('?')[:1])
    
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
    
    def user_can_edit_society(self, user, society): 
        if user.is_superuser:
            return True
        elif society in user.societies.all():
            # If user is associated with the society, allow editing
            return True
        else:
            return self._user_has_permission(user, Permission.USER_CAN_EDIT_SOCIETY, society)
    
    def user_can_edit_society_name(self, user, society):
        if user.is_superuser:
            return True
        else:
            return False
    
    def _user_has_permission(self, user, permission_type, object):
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
    "Automatically creates a profile for each newly created user."
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

# ------------------------------------------------------------------------------
