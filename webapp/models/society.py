from datetime import datetime
from django.contrib.auth.models import User
from django.db import models
from webapp.models.node_extra import get_node_extra_info
from webapp.models.profile import Profile
from webapp.models.utils import single_row_or_none


class NodeSocietiesManager(models.Manager):
    def update_for_node(self, node, societies):
        # societies to delete
        self.filter(node=node).exclude(society__in=societies).delete()

        for society in societies:
            ns, created = self.get_or_create(node=node, society=society)
            if created:
                ns.date_created = datetime.utcnow()
                ns.save()

    def update_for_society(self, society, nodes):
        nodes_to_delete = self.filter(society=society).exclude(node__in=nodes)
        nodes_to_delete.delete()

        for node in nodes:
            ns, created = self.get_or_create(node=node, society=society)
            if created:
                ns.date_created = datetime.utcnow()
                ns.save()

    def update_for_society_cluster(self, nodes, society, cluster):
        nodes_to_delete = \
            self.filter(society=society,
                        node__parents__id__contains=cluster.id).\
            exclude(node__in=nodes)
        nodes_to_delete.delete()

        for node in nodes:
            ns, created = self.get_or_create(node=node, society=society)
            if created:
                ns.date_created = datetime.utcnow()
                ns.save()


class NodeSocieties(models.Model):
    node = models.ForeignKey('Node', related_name='node_societies')
    society = models.ForeignKey('Society', related_name='node_societies')
    date_created = models.DateTimeField(blank=True, null=True, default=None)
    is_machine_generated = models.BooleanField(default=False)

    objects = NodeSocietiesManager()

    class Meta:
        app_label = 'webapp'
        db_table = 'ieeetags_node_societies'
        ordering = ['node__name', 'society__name']


class SocietyManager(models.Manager):
    def getFromName(self, name):
        """
        Returns the society with the given name, or None.
        """
        return single_row_or_none(self.filter(name=name))

    def getFromAbbreviation(self, abbr):
        """
        Returns the society with the given abbreviation, or None.
        """
        return single_row_or_none(self.filter(abbreviation=abbr))

    def searchByNameSubstring(self, substring):
        """
        Returns any societies that match the search phrase.
        """
        if substring.strip() == '':
            return None
        return self.filter(name__icontains=substring)

    def getForUser(self, user):
        """
        Returns all societies that the given user has access to.
        """
        if user.get_profile().role == Profile.ROLE_ADMIN:
            return self.all()
        elif user.get_profile().role == Profile.ROLE_SOCIETY_ADMIN:
            return self.all()
        elif user.get_profile().role == Profile.ROLE_SOCIETY_MANAGER:
            return self.filter(users=user)
        raise Exception('Unknown role "%s"' % user.get_profile().role)

    def searchByNameSubstringForUser(self, substring, user):
        """
        Returns all societies that the given user has access to and that
        match the search phrase.
        """
        if substring.strip() == '':
            return None
        return self.getForUser(user).filter(name__icontains=substring)


class Society(models.Model):
    name = models.CharField(max_length=500)
    description = models.CharField(blank=True, max_length=5000)
    abbreviation = models.CharField(max_length=20)
    url = models.CharField(blank=True, max_length=1000)
    logo_thumbnail = models.FileField(upload_to='images/sc_logos/thumbnail',
                                      blank=True)
    logo_full = models.FileField(upload_to='images/sc_logos/full', blank=True)
    users = models.ManyToManyField(User, related_name='societies', blank=True)

    objects = SocietyManager()

    def __unicode__(self):
        return self.name

    def get_tag_ranges(self, show_empty_terms=False):
        """
        Returns the min/max amount of resources/sectors/related-tags per tag
        for the given society.
        Ignores tags with no resources, no filters, or no societies.
        Returns a tuple:
            (min_resources,
            max_resources,
            min_sectors,
            max_sectors,
            min_related_tags,
            max_related_tags,
            min_societies,
            max_societies)
        """
        #log('get_tag_ranges()')

        # Filter out tags with no resources
        tags = get_node_extra_info(self.tags)

        min_resources = None
        max_resources = None
        min_sectors = None
        max_sectors = None
        min_related_tags = None
        max_related_tags = None
        min_societies = None
        max_societies = None

        for tag in tags:
            if (show_empty_terms and tag.is_taxonomy_term) \
                    or (tag.num_societies1 > 0 and tag.num_resources1 > 0):
            # if tag.num_resources1 > 0 and tag.num_societies1 > 0 \
            #         and tag.num_filters1 > 0:
                if min_resources is None or tag.num_resources1 < min_resources:
                    min_resources = tag.num_resources1
                if max_resources is None or tag.num_resources1 > max_resources:
                    max_resources = tag.num_resources1

                if min_sectors is None or tag.num_sectors1 < min_sectors:
                    min_sectors = tag.num_sectors1
                if max_sectors is None or tag.num_sectors1 > max_sectors:
                    max_sectors = tag.num_sectors1

                if min_related_tags is None \
                        or tag.num_related_tags1 < min_related_tags:
                    min_related_tags = tag.num_related_tags1
                if max_related_tags is None \
                        or tag.num_related_tags1 > max_related_tags:
                    max_related_tags = tag.num_related_tags1

                if min_societies is None or tag.num_societies1 < min_societies:
                    min_societies = tag.num_societies1
                if max_societies is None or tag.num_societies1 > max_societies:
                    max_societies = tag.num_societies1

        #log('  min_resources: %s' % min_resources)
        #log('  max_resources: %s' % max_resources)
        #log('  min_sectors: %s' % min_sectors)
        #log('  max_sectors: %s' % max_sectors)
        #log('  min_related_tags: %s' % min_related_tags)
        #log('  max_related_tags: %s' % max_related_tags)
        #log('  min_societies: %s' % min_societies)
        #log('  max_societies: %s' % max_societies)

        #assert False

        return (min_resources, max_resources, min_sectors, max_sectors,
                min_related_tags, max_related_tags, min_societies,
                max_societies)

    def get_combined_ranges(self, show_empty_terms=False):
        """
        Returns the min/max combined score per tag for the given society.
        Ignores tags with no resources, no filters, or no societies.
        @return a tuple (min, max)
        """
        #p = Profiler('get_combined_sector_ranges()')
        #log('get_combined_sector_ranges()')
        #p.tick('get_extra_info()')

        # Filter out tags with no resources
        tags = get_node_extra_info(self.tags)

        min_score = None
        max_score = None

        #p.tick('start loop')

        for tag in tags:
            # Ignore all hidden tags
            # if (show_empty_terms and tag['is_taxonomy_term'])
            #     or (tag['num_societies1'] > 0 and tag['num_resources1'] > 0):
            if (show_empty_terms and tag.is_taxonomy_term) \
                    or (tag.num_societies1 > 0 and tag.num_resources1 > 0):
            # if tag.num_resources1 > 0 and tag.num_societies1 > 0 \
            #         and tag.num_filters1 > 0:
                if min_score is None or tag.score1 < min_score:
                    min_score = tag.score1

                if max_score is None or tag.score1 > max_score:
                    max_score = tag.score1

        #log('  min_score: %s' % min_score)
        #log('  max_score: %s' % max_score)
        return min_score, max_score

    class Meta:
        app_label = 'webapp'
        db_table = 'ieeetags_society'
        ordering = ['name']
