from django.db import models
from django.contrib.auth.models import User

from models.node import Node
from models.resource import Resource
from models.society import Society


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

    def __unicode__(self):
        return self.name


class OtherFavorites(models.Model):
    user_id = models.ForeignKey(User)
    external_resource_type = models.CharField(max_length=50)
    data_id = models.CharField(max_length=50)
    creation_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'ieeetags'
