from django.db import models
from models.utils import single_row


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

    class Meta:
        app_label = 'ieeetags'
        abstract = True

    def __unicode__(self):
        return self.name


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
        app_label = 'ieeetags'
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

    class Meta:
        app_label = 'ieeetags'


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

    class Meta:
        app_label = 'ieeetags'


class FilterManager(NamedValueTypeManager):
    def get_from_name_list(self, names):
        'Returns a list of filters whose names match the given list of names.'
        results = self.filter(name__in=names)
        if len(results) != len(names):
            raise Exception('Did not find matches for all filters:\n'
                            'names: %s\nresults: %s' % (names, results))
        return results


class Filter(NamedValueType):
    EMERGING_TECHNOLOGIES = 'emerging_technologies'
    FOUNDATION_TECHNOLOGIES = 'foundation_technologies'
    HOT_TOPICS = 'hot_topics'
    MARKET_AREAS = 'market_areas'

    FILTERS = [
        EMERGING_TECHNOLOGIES,
        FOUNDATION_TECHNOLOGIES,
        HOT_TOPICS,
        MARKET_AREAS,
    ]

    objects = FilterManager()

    class Meta:
        app_label = 'ieeetags'

    def __unicode__(self):
        return self.name

