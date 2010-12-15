import unittest
#from ieeetags.models import Animal
from ieeetags import views
from django.http import HttpRequest
from django.contrib.auth.models import User
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound

class LoadPagesTestCase(unittest.TestCase):
    def setUpClass(self):
        self.admin_user = User()
        self.admin_user.username = 'admin'
        self.admin_user.is_staff = True
        self.admin_user.save()
        
        self.user = User()
        self.user.username = 'normal_user'
        self.user.save()

    def testIndex(self):
        'Test that the index page loads.'
        client = Client()
        response = client.get(reverse('index'))
        # Redirect.
        self.assertEqual(response.status_code, 302)

    def testTextui(self):
        'Test that the textui page loads.'
        client = Client()
        response = client.get(reverse('textui'))
        self.assertEqual(response.status_code, 200)

    def test404Error(self):
        'Test a non-existent page (404 error).'
        client = Client()
        response = client.get('/kjsdhfkjshdfkshdfkjsdhfkjsdfh')
        self.assertEqual(response.status_code, 404)
