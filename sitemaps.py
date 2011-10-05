from django.contrib.sitemaps import Sitemap
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from ieeetags.models import Node, NodeType
from urllib import quote

class OneOffsSitemap(Sitemap):
    def items(self):
        return [
            { 'name': 'home', 'path': '/'} 
            ,{'name': 'feedback', 'path': '/feedback'} 
            ,{'name': 'tags', 'path': '/tags'}
            ,{'name': 'tags/all', 'path': '/tags/all'} 
             ]

    def location(self, item):
        return item['path']

class TagsStartWithSitemap(Sitemap):
    def items(self):
        alphalist = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        alphalist = [quote('[0-9]')] + alphalist + [quote('[^a-z0-9]')]
        return alphalist

    def location(self, item):
        return reverse('tags_starts', args=[item])

class TagLandingSitemap(Sitemap):
    def items(self):
        return Node.objects.filter(node_type__name=NodeType.TAG)

    def location(self, item):
        return '%s%s' % (reverse('tag_landing', args=[item.pk]), slugify(item.name))
#        return '/tag/%s/%s' % (item.pk, slugify(item.name))



