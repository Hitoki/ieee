'''
Checks all resources' URLs from the command line.
'''

# Setup django so we can run this from command-line

from django.core.management import setup_environ
import sys


sys.path = ['../..'] + sys.path
import ieeetags.settings
setup_environ(ieeetags.settings)
from core import url_checker
from webapp.models.resource import Resource
import logging

# -----

try:
	logging.debug('check_urls.py: Begin.')
	resources = Resource.objects.exclude(url='').filter(url_status='')
	logging.debug('check_urls.py:   resources.count(): %s' % resources.count())
	NUM_THREADS = 100
	logging.debug('check_urls.py:   Checking %s URLs...' % resources.count())
	url_checker.check_resources(resources, NUM_THREADS)
	logging.debug('check_urls.py:   Done checking URLs.')
	logging.debug('check_urls.py: End.')

except Exception, e:
	logging.error('check_urls.py: ----------------------------------------------')
	logging.error('check_urls.py: EXCEPTION: %s' % e)
	logging.error('check_urls.py: ----------------------------------------------')
