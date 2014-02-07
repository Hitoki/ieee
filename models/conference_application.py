from django.db import models
from models.node import Node


# class TestModel(models.Model):
#     '''
#     Just for check if migrations is working here, it can be removed later
#     '''
#     test_field = models.IntegerField(default=0)
#
#     class Meta:
#         app_label = 'ieeetags'


class ConferenceApplication(models.Model):
    name = models.CharField(verbose_name="Conference name:", max_length=200)
    keywords = models.ManyToManyField('TagKeyword',
                                      related_name="conference_applications")

    class Meta:
        app_label = 'ieeetags'


class TagKeyword(models.Model):
    name = models.CharField(max_length=500)
    tag = models.ForeignKey(Node, null=True)

    class Meta:
        app_label = 'ieeetags'
