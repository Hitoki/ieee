from datetime import datetime
import time

from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import MultipleObjectsReturned
from django.db import connection
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save

#from profiler import Profiler
from enum import Enum
from new_models.node import Node
from new_models.types import ResourceType
from new_models.utils import single_row_or_none, list_to_choices
import util


class NodeSocietiesManager(models.Manager):
    def update_for_node(self, node, societies):
        societies_to_delete = self.filter(node=node).exclude(society__in=societies)
        societies_to_delete.delete()

        for society in societies:
            ns, created = self.get_or_create(node=node, society=society)
            if created:
                ns.date_created = datetime.utcnow()
                ns.save()

    def update_for_society(self, society, nodes):
        nodes_to_delete = self.filter(society=society).exclude(node__in=nodes)
        nodes_to_delete.delete()

        for node in nodes:
            ns, created = self.get_or_create(node=node, society=society)
            if created:
                ns.date_created = datetime.utcnow()
                ns.save()

    def update_for_society_cluster(self, nodes, society, cluster):
        nodes_to_delete = self.filter(society=society, node__parents__id__contains=cluster.id).exclude(node__in=nodes)
        nodes_to_delete.delete()

        for node in nodes:
            ns, created = self.get_or_create(node=node, society=society)
            if created:
                ns.date_created = datetime.utcnow()
                ns.save()
        

class NodeSocieties(models.Model):
    node = models.ForeignKey('Node', related_name='node_societies')
    society = models.ForeignKey('Society', related_name='node_societies')
    date_created = models.DateTimeField(blank=True, null=True, default=None)
    is_machine_generated = models.BooleanField(default=False)

    objects = NodeSocietiesManager()
    
    class Meta:
        db_table = 'ieeetags_node_societies'
        ordering = ['node__name', 'society__name']

# ----------------------------------------------------------------------------


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

    def searchByNameSubstringForUser(self, substring, user):
        '''Returns all societies that the given user has access to and that
        match the search phrase.'''
        if substring.strip() == '':
            return None
        return self.getForUser(user).filter(name__icontains=substring)


class Society(models.Model):
    name = models.CharField(max_length=500)
    description = models.CharField(blank=True, max_length=5000) 
    abbreviation = models.CharField(max_length=20)
    url = models.CharField(blank=True,max_length=1000)
    logo_thumbnail = models.FileField(upload_to='images/sc_logos/thumbnail',
                                      blank=True)
    logo_full = models.FileField(upload_to='images/sc_logos/full',blank=True)
    
    users = models.ManyToManyField(User, related_name='societies', blank=True)
    
    objects = SocietyManager()
    
    def __unicode__(self):
        return self.name
    
    def get_tag_ranges(self, show_empty_terms=False):
        """
        Returns the min/max amount of resources/sectors/related-tags per tag
        for the given society.
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
        
        return (min_resources, max_resources, min_sectors, max_sectors,
                min_related_tags, max_related_tags, min_societies,
                max_societies)
    
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

# ----------------------------------------------------------------------------


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


class FailedLoginLogManager(models.Manager):
    
    def check_if_disabled(self, username, ip):
        "Return True if a given username or ip has been disabled."
        #log('check_if_disabled()')
        #log('  username: %s' % username)
        #log('  ip: %s' % ip)
        ## log('  FailedLoginLog.DISABLE_ACCOUNT_TIME: %s' %
        ##     FailedLoginLog.DISABLE_ACCOUNT_TIME)
        before = datetime.fromtimestamp(time.time() -
                                        FailedLoginLog.DISABLE_ACCOUNT_TIME)
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
        """Records a bad login and checks if the max has been reached.
        Returns True if user is under the limit, and False if user is over
        the limit."""
        self._add_failed_login(username, ip)
        return self.check_if_disabled(username, ip)
    
    def _add_failed_login(self, username, ip):
        "Adds a bad login entry and disables an account if necessary."
        
        #log('_add_failed_login()')
        #log('  username: %s' % username)
        #log('  ip: %s' % ip)
        
        # Check if there have been too many bad logins (including this one)
        before = datetime.fromtimestamp(time.time() -
                                        FailedLoginLog.FAILED_LOGINS_TIME)
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
    '''Keeps track of past failed logins.
    Suspends future logins for a certain time if there are too many
    failed logins.'''

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

# ----------------------------------------------------------------------------


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
        return '<%s: %s, %s, %s>' % (self.__class__.__name__, self.url,
                                     self.elapsed_time,
                                     self.short_user_agent())


PROCESS_CONTROL_TYPES = Enum(
    'XPLORE_IMPORT',
)


class ProcessControl(models.Model):
    'Controls and stores information for a long-running process.'
    
    # The type (ie. name) of process.
    # Should only be one per name at any given time.
    type = models.CharField(max_length=100,
                            choices=util.make_choices(PROCESS_CONTROL_TYPES))
    'Log messages output by the process (stored in this DB field only).'
    log = models.CharField(max_length=1000, blank=True)
    'Filename for the logfile written by the process.'
    log_filename = models.CharField(max_length=1000, blank=True, default='')
    'Signal the process to quit.'
    is_alive = models.BooleanField(default=True)
    'Process will update periodically to the current time.'
    date_updated = models.DateTimeField(null=True, blank=True)
    
    # Process-type specific fields.
    'This is updated the most-recently processed tag by the Xplore Import ' \
    'script, allows resuming.'
    last_processed_tag = models.ForeignKey(Node, null=True, blank=True,
                                           default=None)

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
