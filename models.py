from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import MultipleObjectsReturned
from django.db import connection
from django.db import models
from django.db.models.signals import post_save

#from profiler import Profiler
from new_models.node import Node
from new_models.society import NodeSocieties, Society
from new_models.types import ResourceType
from new_models.utils import single_row_or_none, list_to_choices



class ResourceManager(models.Manager):
    def get_conferences(self):
        'Returns all conferences.'
        resource_type = \
            ResourceType.objects.getFromName(ResourceType.CONFERENCE)
        return self.filter(resource_type=resource_type)
        
    def get_standards(self):
        'Returns all standards.'
        resource_type = \
            ResourceType.objects.getFromName(ResourceType.STANDARD)
        return self.filter(resource_type=resource_type)
        
    def get_periodicals(self):
        'Returns all periodicals.'
        resource_type = \
            ResourceType.objects.getFromName(ResourceType.PERIODICAL)
        return self.filter(resource_type=resource_type)
        
    def getForNode(self, node, resourceType=None):
        '''
        Gets all resources for the given node.
        Optionally filter by resource type.
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
        Returns a list of all distinct conference series codes and the number
        of conferences in each series (ignores blank fields).
        Returns:
            [
                (conference_series, num_in_series),
                ...
            ]
        """
        conference_type = \
            ResourceType.objects.getFromName(ResourceType.CONFERENCE)
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
        resources = Resource.objects.filter(
            resource_type__name=ResourceType.CONFERENCE,
            conference_series=series, year__gte=current_year
        ).order_by('date', 'year', 'id')
        #print '  resources.count(): %s' % resources.count()
        if resources.count():
            # Use the next future resource
            #print '  using next future'
            return resources[0]
        else:
            # Use the most-recent past resource
            #print '  using most recent'
            resources = Resource.objects.filter(
                resource_type__name=ResourceType.CONFERENCE,
                conference_series=series, year__lt=current_year
            ).order_by('-date', '-year', '-id')
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
    
    def get_non_current_conferences_for_series(self, series,
                                               current_conference=None):
        'Get all non-current conferences in the given series.'
        #print 'get_non_current_conferences_for_series()'
        #print '  series: %s' % series
        #print '  current_conference: %s' % current_conference
        if current_conference is None:
            current_conference = self.get_current_conference_for_series(series)
        #print '  current_conference: %s' % current_conference
        # Get the other conferences in the series
        return Resource.objects.filter(conference_series=series).\
            exclude(id=current_conference.id).all()


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
    'This field is a text field, displayed to society managers ' \
    'on Edit Resource page to help them tag.  Not used in any other way.'
    conference_series = models.CharField(max_length=100, blank=True)
    'Optional.  ' \
    'All conferences with the same "conference_series" are grouped together ' \
    'as a series.'
    date = models.DateField(null=True, blank=True)
    pub_id = models.CharField(max_length=1000, blank=True)
    'Used for Conferences and Standards (optional).  ' \
    'Matches IEEE Xpore PubID field for matching resources during xplore import.'
    
    url_status = models.CharField(blank=True, max_length=100,
                                  choices=URL_STATUS_CHOICES)
    'Reflects the status of this URL.  ' \
    'Can be "good", "bad", or None (not yet checked).'
    url_date_checked = models.DateTimeField(null=True, blank=True)
    url_error = models.CharField(null=True, blank=True, max_length=1000)
    'The error (if any) that occured when checking this URL.'
    
    nodes = models.ManyToManyField(Node, related_name='resources',
                                   through='ResourceNodes')
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

# ----------------------------------------------------------------------------


class ResourceAdditionNotificationRequest(models.Model):
    '''Tracks the request of a user to be notified when resources are newly
    related to a node.'''
    node = models.ForeignKey(Node, related_name='notification_node')
    date_created = models.DateTimeField(blank=False, null=False)
    email = models.CharField(blank=False, max_length=255)

    class Meta:
        unique_together = ('node', 'email')


class ResourceAdditionNotification(models.Model):
    'Tracke the sending a notification email.'
    request = models.ForeignKey(ResourceAdditionNotificationRequest)
    resourceNodes = models.ForeignKey(ResourceNodes, null=True)
    resourceSocieties = models.ForeignKey(NodeSocieties, null=True)
    date_notified = models.DateTimeField(blank=False, null=False)

# ----------------------------------------------------------------------------


class PermissionManager(models.Manager):
    '''This object stores all permission-related functions.
    All new permission checks should go here.'''
    
    def user_can_edit_society(self, user, society): 
        'Checks if a user can edit a society.'
        if user.is_superuser:
            return True
        elif society in user.societies.all():
            # If user is associated with the society, allow editing
            return True
        else:
            return self._user_has_permission(user,
                                             Permission.USER_CAN_EDIT_SOCIETY,
                                             society)

    def user_can_edit_society_name(self, user, society):
        'Only superusers (admins) can edit a society name.'
        if user.is_superuser:
            return True
        else:
            return False
    
    def _user_has_permission(self, user, permission_type, object):
        '''Generic helper function to check if the user has the a certain
        permission for an object.'''
        object_type = ContentType.objects.get_for_model(object)
        results = self.filter(user=user, object_id=object.id,
                              object_type=object_type,
                              permission_type=permission_type)
        return len(results) > 0


class Permission(models.Model):
    USER_CAN_EDIT_SOCIETY = 'user_can_edit_society'
    
    user = models.ForeignKey(User, related_name='permissions')
    object_type = models.ForeignKey(ContentType, related_name='permissions')
    object_id = models.PositiveIntegerField()
    object = generic.GenericForeignKey('object_type', 'object_id')    
    permission_type = models.CharField(max_length=1000)
    
    objects = PermissionManager()

# ----------------------------------------------------------------------------


class Profile(models.Model):
    '''A user\'s profile.
    By default, a profile is created whenever a user is created.'''
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
    copied_resource = models.ForeignKey(Resource, related_name='copied_users',
                                        null=True, blank=True)
    'This stores the source resource for copy & pasting tags.'

# ----------------------------------------------------------------------------


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
        return User.objects.filter(profile__last_login_time__isnull=False).\
            order_by('-profile__last_login_time')

# ----------------------------------------------------------------------------


def _create_profile_for_user(sender, instance, signal, created,
                             *args, **kwargs):
    """Automatically creates a profile for each newly created user.
    Uses signals to detect user creation."""
    if created:
        profile = Profile(user=instance)
        profile.save()


post_save.connect(_create_profile_for_user, sender=User)


def get_user_from_username(username):
    return single_row_or_none(User.objects.filter(username=username))


def get_user_from_email(email):
    return single_row_or_none(User.objects.filter(email=email))

# ----------------------------------------------------------------------------


# ----------------------------------------------------------------------------


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
            idtosave = super(CacheManager, self).\
                filter(name=name, params=params).order_by('-id')[0:1][0].id
            super(CacheManager, self).filter(name=name, params=params).\
                exclude(id=idtosave).delete()
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
        return '<Cache: %s, %s, %s>' % (self.name, self.params,
                                        len(self.content))
