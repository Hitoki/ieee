from django.db import models
from django.contrib.auth.models import User

from models.node import Node
from models.resource import Resource

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
	
	class Meta:
		app_label = 'ieeetags'

	def __unicode__(self):
		return self.name