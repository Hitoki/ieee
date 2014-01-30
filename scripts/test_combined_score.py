'''
Checks that score1 is effected by .societies.count().
'''

# Setup django so we can run this from command-line

from django.core.management import setup_environ
import random
import sys
from models import get_node_extra_info


sys.path = ['../..'] + sys.path
import ieeetags.settings
setup_environ(ieeetags.settings)
from models.node import Node
from models.society import Society


# -----

tag_id = 2458
tags = Node.objects.filter(id=tag_id)

societies = tags[0].societies.all()[:]
print 'len(societies): %s' % len(societies)

if len(societies) == 0:
    societies = random.sample(Society.objects.all(), 5)
    print 'len(societies): %s' % len(societies)
print ''

tags = get_node_extra_info(tags)
print 'tags[0].id: %s' % tags[0].id
print 'tags[0].name: %s' % tags[0].name
print 'tags[0].score1: %s' % tags[0].score1
print 'tags[0].societies.count(): %s' % tags[0].societies.count()
print ''

tags[0].societies = []
tags = get_node_extra_info(tags)
print 'tags[0].id: %s' % tags[0].id
print 'tags[0].name: %s' % tags[0].name
print 'tags[0].score1: %s' % tags[0].score1
print 'tags[0].societies.count(): %s' % tags[0].societies.count()
print ''

tags[0].societies = societies
tags = get_node_extra_info(tags)
print 'tags[0].id: %s' % tags[0].id
print 'tags[0].name: %s' % tags[0].name
print 'tags[0].score1: %s' % tags[0].score1
print 'tags[0].societies.count(): %s' % tags[0].societies.count()
print ''
