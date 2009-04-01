
from django.contrib.auth.models import User
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
        if 'num_related_sectors' not in kwargs:
            kwargs['num_related_sectors'] = 0
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
        return single_row(self.filter(name=name, node_type=sectorType))
    
    def getFirstSector(self):
        return self.getSectors()[0]
    
    def getTags(self):
        tag_type = NodeType.objects.getFromName('tag')
        return self.filter(node_type=tag_type)
    
    def getChildNodes(self, node):
        return self.filter(parent=node)
    
    def getTagsByName(self, name):
        tag_type = NodeType.objects.getFromName('tag')
        return self.filter(name=name, node_type=tag_type)
    
    def getTagByName(self, sector, tagName):
        tag_type = NodeType.objects.getFromName('tag')
        return single_row_or_none(self.filter(name=tagName, parent=sector, node_type=tag_type))
        
    def getRandomTag(self):
        tag_type = NodeType.objects.getFromName('tag')
        return self.filter(node_type=tag_type).order_by('?')[0]
    
    def get_random_related_tags(self, tag, count):
        tag_type = NodeType.objects.getFromName('tag')
        return self.filter(node_type=tag_type,parent=tag.parent).exclude(id=tag.id).order_by('?')[:count]
    
    def getFilteredNodes(self, nodeId, filterIds, sort):
        return []
    
    def getRelatedSectors(self, tag):
        # Get all related sectors (including the given tag's sector)
        relatedSectors = self.filter(node_type__name=NodeType.SECTOR, child_nodes__name=tag.name)#.exclude(id=tag.parent.id)
        #print '  relatedSectors:', relatedSectors
        #print '  len(relatedSectors):', len(relatedSectors)
        return relatedSectors
    
    # Returns the min/max amount of resources-per-tag for the given sector
    def getResourceRange(self, sector):
        sql = """
            SELECT MIN(num_resources) AS min, MAX(num_resources) AS max
            FROM ieeetags_node
            WHERE parent_id = %s
            """
        cursor = connection.cursor()
        cursor.execute(sql, [sector.id])
        return cursor.fetchall()[0]
    
    def getRelatedSectorRange(self, sector):
        sql = """
            SELECT MIN(num_related_sectors) AS min, MAX(num_related_sectors) AS max
            FROM ieeetags_node
            WHERE parent_id = %s
            """
        cursor = connection.cursor()
        cursor.execute(sql, [sector.id])
        return cursor.fetchall()[0]
    
    def updateTagCounts(self):
        tags = self.getTags()
        for tag in tags:
            tag.num_resources = len(tag.resources.all())
            tag.num_related_sectors = len(self.getRelatedSectors(tag))
            tag.save()
        return len(tags)
    
    def searchTagsByNameSubstring(self, substring):
        if substring.strip() == '':
            return None
        tag_type = NodeType.objects.getFromName(NodeType.TAG)
        return self.filter(name__icontains=substring, node_type=tag_type)
    
    def get_sector_by_name(self, name):
        sector_type = NodeType.objects.getFromName(NodeType.SECTOR)
        return single_row(self.filter(name=name, node_type=sector_type), 'Looking up sector "%s"' % name)
    
    def get_sectors_for_tag(self, node):
        for node1 in self.filter(name=node.name):
            yield node1.parent
    
class Node(models.Model):
    name = models.CharField(max_length=500)
    parent = models.ForeignKey('Node', related_name='child_nodes', null=True, blank=True)
    node_type = models.ForeignKey(NodeType)
    societies = models.ManyToManyField('Society', related_name='tags', blank=True)
    filters = models.ManyToManyField('Filter', related_name='nodes')

    related_tags = models.ManyToManyField('Node', blank=True)
    num_related_tags = models.IntegerField(null=True, blank=True)
    
    num_resources = models.IntegerField(null=True, blank=True)
    
    related_sectors = models.ManyToManyField('Node', blank=True, null=True)
    num_related_sectors = models.IntegerField(null=True, blank=True)
    
    objects = NodeManager()
    def __str__(self):
        if self.node_type.name == NodeType.TAG:
            return '%s (%s)' % (self.name, self.parent.name)
        else:
            return self.name
    
    #def full_name(self):
    #    if self.node_type.name == NodeType.TAG:
    #        return '%s > %s' % (self.parent.name, self.name)
    #    else:
    #        return self.name

    def name_with_sector(self):
        if self.node_type.name == NodeType.TAG:
            return '%s (%s)' % (self.name, self.parent.name)
        else:
            return self.name
        
    def get_parents(self):
        return self.objects.get_sectors_for_tag(self)
        
    class Meta:
        ordering = ['name', 'parent__name']

# ------------------------------------------------------------------------------

class SocietyManager(models.Manager):
    def getRandom(self):
        return self.all().order_by('?')[0]
    
    def getFromName(self, name):
        return single_row_or_none(self.filter(name=name))
    
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
    def getConferences(self):
        resourceType = ResourceType.getForName('conference')
        return self.filter(resource_type=resourceType)
        
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
    STANDARD_STATUS_STANDARD = 'standard'
    
    resource_type = models.ForeignKey(ResourceType)
    ieee_id = models.CharField(max_length=500,blank=True, null=True)
    name = models.CharField(max_length=500)
    description = models.CharField(blank=True, max_length=1000)
    url = models.CharField(blank=True, max_length=1000)
    year = models.IntegerField(blank=True, null=True)
    standard_status = models.CharField(blank=True, max_length=100)
    
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
        (ROLE_ADMIN, ROLE_ADMIN),
        (ROLE_SOCIETY_MANAGER, ROLE_SOCIETY_MANAGER),
    ]
    
    user = models.ForeignKey(User, unique=True)
    role = models.CharField(choices=ROLES, max_length=1000)
    reset_key = models.CharField(max_length=1000, null=True)

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


