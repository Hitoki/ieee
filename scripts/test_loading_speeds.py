# Setup django so we can run this from command-line

from django.core.management import setup_environ
import os
import sys
sys.path = [os.path.join(os.path.dirname(__file__), '../..')] + sys.path
import ieeetags.settings
setup_environ(ieeetags.settings)

# -----

from ieeetags.models import *
import time
import urllib2

def get_url_time(url):
    start = time.time()
    url = urllib2.urlopen(url)
    end = time.time()
    return end - start

urls = [
    'http://localhost:8001/',
    'http://localhost:8001/ajax/textui_nodes?sector_id=all&sort=connectedness&search_for=',
    #'http://localhost:8001/ajax/tooltip/1170?parent_id=all&society_id=null&search_for=None',
]

results = []
for url in urls:
    time1 = get_url_time(url)
    print '%s,%s' % (url, time1)
