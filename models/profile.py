from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.signals import post_save
from models.resource import Resource
from models.utils import list_to_choices, single_row_or_none


class PermissionManager(models.Manager):
    """
    This object stores all permission-related functions.
    All new permission checks should go here.
    """

    def user_can_edit_society(self, user, society):
        """
        Checks if a user can edit a society.
        """
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
        """
        Only superusers (admins) can edit a society name.
        """
        if user.is_superuser:
            return True
        else:
            return False

    def _user_has_permission(self, user, permission_type, object):
        """
        Generic helper function to check if the user has the a certain
        permission for an object.
        """
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

    class Meta:
        app_label = 'ieeetags'


class Profile(models.Model):
    """
    A user's profile.
    By default, a profile is created whenever a user is created.
    """
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

    class Meta:
        app_label = 'ieeetags'


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


def _create_profile_for_user(sender, instance, signal, created,
                             *args, **kwargs):
    """
    Automatically creates a profile for each newly created user.
    Uses signals to detect user creation.
    """
    if created:
        try:
            Profile.objects.get(user=instance)
        except ObjectDoesNotExist:
            profile = Profile(user=instance)
            profile.save()

post_save.connect(_create_profile_for_user, sender=User)


def get_user_from_username(username):
    return single_row_or_none(User.objects.filter(username=username))


def get_user_from_email(email):
    return single_row_or_none(User.objects.filter(email=email))


def email_user_display(user):
    return user.email
