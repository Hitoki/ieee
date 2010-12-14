#!/usr/bin/env python
# encoding: utf-8
"""
start-wsgi.py
Starts the Django application with standard settings when called by mod_wsgi.
"""

import os
import sys
try:
    import activate_this    # modwsgi virtualenv path activation script;
        # bin/ of the virtual env must be on the PYTHONPATH
    if hasattr(sys, 'real_prefix'):
        # correct activate_this problem mentioned in modwsgi docs
        sys.prefix = sys.real_prefix
except ImportError:
    pass

import django.core.handlers.wsgi

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
DEBUG = os.environ.get('DEBUG', False)
sys.stdout = sys.stderr # in case there are any errant 'print' statements

class WSGIDebugWrapper: # log traceback in case of exceptions Django doesn't handle
    def __init__(self, app):
        self.app = app

    def __call__(self, *args, **kwargs):
        try:
            return self.app(*args, **kwargs)
        except:
            import traceback
            # print exception traceback, where it will appear in Apache's logs
            traceback.print_exc()
            # following line will generate an error if WSGI response hasn't
            # been started, but that's OK; we already have a good traceback
            return []

application = django.core.handlers.wsgi.WSGIHandler()
if DEBUG:
    application = WSGIDebugWrapper(application)
