from django.db import models
from new_models.utils import single_row


class NamedTypeManager(models.Manager):
    def getFromName(self, name):
        '''Looks up a NamedType that matches the given name.
        Fails if none found.'''
        types = self.filter(name=name)
        if len(types) != 1:
            raise Exception('Found %d %s for name "%s", looking for 1 result' %
                            (len(types), self.__class__, name))
        return types[0]


class NamedType(models.Model):
    'A named type.  Used for named constants in the DB.'
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name
    class Meta:
        abstract = True


class NamedValueTypeManager(NamedTypeManager):
    def getFromValue(self, value):
        '''Looks up a NamedType that matches the given value.
        Fails if none found.'''
        types = self.filter(value=value)
        return single_row(types)


class NamedValueType(NamedType):
    '''A named & valued type.  Each object has a name and value.
    Used for named/valued constants in the DB.'''
    value = models.CharField(max_length=500)

    def __unicode__(self):
        return '%s (%s)' % (self.name, self.value)
    class Meta:
        abstract = True


class NodeTypeManager(NamedTypeManager):
    pass


class NodeType(NamedType):
    'The constant node types.  Can be a cluster, tag, sector, or root.'
    TAG_CLUSTER = 'tag_cluster'
    TAG = 'tag'
    SECTOR = 'sector'
    ROOT = 'root'

    objects = NodeTypeManager()


class ResourceTypeManager(NamedTypeManager):
    pass


class ResourceType(NamedType):
    '''NamedType model for each of the available resource types:
    conference, expert, periodical, standard.'''
    objects = ResourceTypeManager()

    CONFERENCE = 'conference'
    EXPERT = 'expert'
    PERIODICAL = 'periodical'
    STANDARD = 'standard'
    EBOOK = 'ebook'
