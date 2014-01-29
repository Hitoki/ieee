# Setup django.
import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import ieeetags.settings
from django.core.management import setup_environ
setup_environ(ieeetags.settings)

# ------------------------------------------------------------------------------

import unittest
from django.contrib.auth.models import User
from django.test.client import Client
from django.core.urlresolvers import reverse

class LoadPagesTestCase(unittest.TestCase):
    # NOTE: 'fixtures' doesn't work in Python 2.4.
    #fixtures = ['test_data']
    
    def setUp(self):
        if User.objects.count() == 0:
            # No data yet, install the test_data.json fixture.
            print '  Loading "test_data.json" fixture for testing.'
            from django.core import management
            import os
            initial_data_filename = os.path.abspath(os.path.join(os.path.dirname(__file__), 'fixtures/test_data.json'))
            management.call_command('loaddata', initial_data_filename)
            print '  Done loading fixture.'
        
    def testDataExists(self):
        'Tests that the test_data fixture is being installed.'
        from models.types import NodeType
        num_node_types = NodeType.objects.count()
        self.assertTrue(num_node_types > 0, 'There are no NodeType objects.')
        
    def testIndex(self):
        'Test that the index page loads.'
        client = Client()
        response = client.get(reverse('index'))
        
        # Redirect.
        self.assertEqual(response.status_code, 302)
        
        # Fail
        #self.assertEqual(response.status_code, 200)

    def testTextui(self):
        'Test that the textui page loads.'
        client = Client()
        response = client.get(reverse('textui'))
        self.assertEqual(response.status_code, 200)
        
        # ERROR:
        #self.assertEqual(response.status_code, 1000)

    def test404Error(self):
        'Test a non-existent page (404 error).'
        client = Client()
        response = client.get('/kjsdhfkjshdfkshdfkjsdhfkjsdfh')
        self.assertEqual(response.status_code, 404)
