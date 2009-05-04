from django.db.models import Q
from django.contrib.auth.models import User, UserManager
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.db import models
from django.db.models.signals import post_save
import string

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
    
    def __str__(self):
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
    
    def __str__(self):
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
        if 'num_related_tags' not in kwargs:
            kwargs['num_related_tags'] = 0
        if 'num_resources' not in kwargs:
            kwargs['num_resources'] = 0
        kwargs['node_type'] = NodeType.objects.getFromName(NodeType.TAG)
        return models.Manager.create(self, **kwargs)
        
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
    
    def getSectorByName(self, name):
        sectorType = NodeType.objects.getFromName('sector')
        return single_row(self.filter(name=name, node_type=sectorType), 'Can\'t find sector "%s"' % name)
    
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
    
    def get_sector_range(self, sector):
        "Returns the min/max amount of sectors-per-tag for the given sector."
        
        sector_counts = [tag.parents.count() for tag in sector.child_nodes.all()]
        
        if len(sector_counts) == 0:
            min_sectors = None
            max_sectors = None
        else:
            min_sectors = min(sector_counts)
            max_sectors = max(sector_counts)
        
        return (min_sectors, max_sectors)
    
    def updateTagCounts(self):
        tags = self.getTags()
        for tag in tags:
            tag.num_resources = len(tag.resources.all())
            tag.save()
        return len(tags)
    
    def searchTagsByNameSubstring(self, substring, sector_ids=None, exclude_tag_id=None):
        """
        Search for tags matching the given substring.  Optionally limit to only the list of sectors given.
        @param substring name substring to search for.
        @param sector_ids optional, a list of sector ids to limit the search within.
        """
        if substring.strip() == '':
            return None
        tag_type = NodeType.objects.getFromName(NodeType.TAG)
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
    
    def get_sector_by_name(self, name):
        sector_type = NodeType.objects.getFromName(NodeType.SECTOR)
        return single_row(self.filter(name=name, node_type=sector_type), 'Looking up sector "%s"' % name)
    
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
    
class Node(models.Model):
    name = models.CharField(max_length=500)
    #parent = models.ForeignKey('Node', related_name='child_nodes', null=True, blank=True)
    parents = models.ManyToManyField('self', symmetrical=False, related_name='child_nodes', null=True, blank=True)
    node_type = models.ForeignKey(NodeType)
    societies = models.ManyToManyField('Society', related_name='tags', blank=True)
    filters = models.ManyToManyField('Filter', related_name='nodes')

    related_tags = models.ManyToManyField('self', null=True, blank=True)
    num_related_tags = models.IntegerField(null=True, blank=True)
    
    num_resources = models.IntegerField(null=True, blank=True)
    
    objects = NodeManager()
    def __str__(self):
        return self.name
    
    #def full_name(self):
    #    if self.node_type.name == NodeType.TAG:
    #        return '%s > %s' % (self.parent.name, self.name)
    #    else:
    #        return self.name
    
    def parent_names(self):
        return ', '.join([parent.name for parent in self.parents.all()])

    def name_with_sector(self):
        if self.node_type.name == NodeType.TAG:
            return '%s (%s)' % (self.name, self.parent_names())
        else:
            return self.name
        
    #def get_parents(self):
    #    return self.objects.get_sectors_for_tag(self)
        
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
        if user.is_superuser:
            return self.all()
        else:
            return self.filter(users=user)
    
class Society(models.Model):
    name = models.CharField(max_length=500)
    abbreviation = models.CharField(max_length=20)
    url = models.CharField(blank=True,max_length=1000)
    
    users = models.ManyToManyField(User, related_name='societies', blank=True)
    
    objects = SocietyManager()
    def __str__(self):
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
    keywords = models.CharField(max_length=5000, blank=True)
    
    nodes = models.ManyToManyField(Node, related_name='resources')
    societies = models.ManyToManyField(Society, related_name='resources')
    
    objects = ResourceManager()
    def __str__(self):
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
    EMERGING_TECHNOLOGIES = 'Emerging Technologies'
    FOUNDATION_TECHNOLOGIES = 'Foundation Technologies'
    HOT_TOPICS = 'Hot Topics'
    MARKET_AREAS = 'Market Areas'
    
    objects = FilterManager()
    
    def __str__(self):
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
    ROLE_SOCIETY_MANAGER = 'society_manager'
    
    ROLES = [
        ROLE_ADMIN,
        ROLE_SOCIETY_MANAGER,
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


