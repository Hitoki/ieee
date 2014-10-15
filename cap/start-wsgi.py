#!/usr/bin/env python
# encoding: utf-8
"""
start-wsgi.py
Starts the Django application with standard settings when called by mod_wsgi.
"""

import os
import sys
import django.core.handlers.wsgi

os.environ['DJANGO_SETTINGS_MODULE'] = 'ieeetags.settings'
sys.stdout = sys.stderr # in case there are any errant 'print' statements
application = django.core.handlers.wsgi.WSGIHandler()
