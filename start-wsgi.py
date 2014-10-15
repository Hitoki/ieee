#!/usr/bin/env python
# encoding: utf-8
"""
start-wsgi.py
Starts the Django application with standard settings when called by mod_wsgi.
"""

import sys
try:
    import activate_this    # modwsgi virtualenv path activation script;
        # bin/ of the virtual env must be on the PYTHONPATH
    if hasattr(sys, 'real_prefix'):
        # correct activate_this problem mentioned in modwsgi docs
        sys.prefix = sys.real_prefix
except ImportError:
    pass

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ieeetags.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
