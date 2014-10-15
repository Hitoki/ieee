from django.db import models
from webapp.models.node import Node
from webapp.models.resource import ResourceNodes
from webapp.models.society import NodeSocieties


class ResourceAdditionNotificationRequest(models.Model):
    """
    Tracks the request of a user to be notified when resources are newly
    related to a node.
    """
    node = models.ForeignKey(Node, related_name='notification_node')
    date_created = models.DateTimeField(blank=False, null=False,
                                        auto_now_add=True)
    email = models.CharField(blank=False, max_length=255)

    class Meta:
        app_label = 'webapp'
        db_table = 'ieeetags_resourceadditionnotificationrequest'
        unique_together = ('node', 'email')


class ResourceAdditionNotification(models.Model):
    """
    Tracke the sending a notification email.
    """
    request = models.ForeignKey(ResourceAdditionNotificationRequest)
    resourceNodes = models.ForeignKey(ResourceNodes, null=True)
    resourceSocieties = models.ForeignKey(NodeSocieties, null=True)
    date_notified = models.DateTimeField(blank=False, null=False)

    class Meta:
        app_label = 'webapp'
        db_table = 'ieeetags_resourcesdditionNotification'
