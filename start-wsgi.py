#!/usr/bin/env python
# encoding: utf-8
"""
start-wsgi.py

Starts the Django application with standard settings when called by mod_wsgi.
"""

import os
import sys

#sys.path.insert(0, os.path.dirname(__file__))

import django.core.handlers.wsgi

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.stdout = sys.stderr # in case there are any errant 'print' statements
application = django.core.handlers.wsgi.WSGIHandler()
