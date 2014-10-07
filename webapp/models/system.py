from django.core.exceptions import MultipleObjectsReturned
from django.db import models
from enum import Enum
from webapp.models.node import Node
from core import util


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

    class Meta:
        app_label = 'ieeetags'

    def __str__(self):
        return '<Cache: %s, %s, %s>' % (self.name, self.params,
                                        len(self.content))


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

    class Meta:
        app_label = 'ieeetags'
