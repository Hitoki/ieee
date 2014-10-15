from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

from webapp.models.node import Node
from webapp.models.resource import Resource
from webapp.models.society import Society


class UserFavorites(models.Model):
    user = models.OneToOneField(User)
    topics = models.ManyToManyField(
        Node,
        blank=True,
        help_text='Favorite Topics',
        related_name='user_favorite_topics'
    )
    resources = models.ManyToManyField(
        Resource,
        blank=True,
        help_text='Favorite Resources',
        related_name='user_favorite_resources'
    )
    societies = models.ManyToManyField(
        Society,
        blank=True,
        help_text='Favorite Societies',
        related_name='user_favorite_societies'
    )

    class Meta:
        app_label = 'ieeetags'


class UserExternalFavoritesManager(models.Manager):
    def get_external_ids(self, external_resource_type, user=None):
        if user is None or user.is_anonymous():
            return list()
        return self.filter(user=user,
                           external_resource_type=external_resource_type).\
            values_list('external_id', flat=True)


class UserExternalFavorites(models.Model):
    user = models.ForeignKey(User)
    external_resource_type = models.CharField(max_length=50)
    external_id = models.CharField(max_length=500)
    title = models.CharField(max_length=500, default='Untitled')
    creation_date = models.DateTimeField(auto_now_add=True)

    objects = UserExternalFavoritesManager()

    class Meta:
        app_label = 'ieeetags'

    def get_url(self):
        kwargs = dict(id=self.external_id)
        rtype = self.external_resource_type
        url_pattern = settings.EXTERNAL_RESOURCE_URLS.get(rtype, '')
        return url_pattern % kwargs
