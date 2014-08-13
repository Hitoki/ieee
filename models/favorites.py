from django.db import models
from django.contrib.auth.models import User

from models.node import Node

class UserFavorites(models.Model):
	user = models.OneToOneField(User)
	favorites = models.ManyToManyField(
		Node,
		blank=True,
		help_text='Favorite Topics',
		related_name='user_favorites'
	)
	
	class Meta:
		app_label = 'ieeetags'

	def __unicode__(self):
		return self.name