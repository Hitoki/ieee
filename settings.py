'''
Django settings for the ieeetags project.
'''

import logging
import os

from util import relpath

DEBUG = False

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)
'This stores all admins.  By default they will receive any errors.'

MANAGERS = ADMINS

# Database Settings

DATABASE_ENGINE = 'mysql'
DATABASE_NAME = None			 # Or path to database file if using sqlite3.
DATABASE_USER = None			 # Not used with sqlite3.
DATABASE_PASSWORD = None		 # Not used with sqlite3.
DATABASE_HOST = ''			 # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''			 # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = relpath(__file__, 'media')
CACHED_MEDIA_ROOT = os.path.join(MEDIA_ROOT, 'caches')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'
CACHED_MEDIA_URL = MEDIA_URL + 'caches/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin_media/'

LOGIN_URL = '/admin/login'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'o5tqsvh$&e3@@jzm)uvc02s*lsuw+5*r6jd%d+8u-6lzi3i%6j'

# Specify the user profile model
AUTH_PROFILE_MODULE = 'ieeetags.profile'

DEFAULT_CHARSET = 'utf-8'

# Outgoing Email Settings

EMAIL_HOST = None
EMAIL_PORT = None
EMAIL_HOST_USER = None
EMAIL_HOST_PASSWORD = None
EMAIL_USE_TLS = None

SERVER_EMAIL = None
DEFAULT_FROM_EMAIL = None

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#	 'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'ieeetags.middleware.ExceptionMiddleware.ExceptionMiddleware',
    #'ieeetags.djangologging.middleware.LoggingMiddleware',
    #'ieeetags.middleware.ProfilingMiddleware.ProfileMiddleware',
)

INTERNAL_IPS = ('127.0.0.1',)

ROOT_URLCONF = 'ieeetags.urls'

TEMPLATE_DIRS = (
    relpath(__file__, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.humanize',
    'dmigrations',
    'ieeetags',
    'ieeetags.site_admin',
    'noomake',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'ieeetags.context_processors.media_url',
    'ieeetags.context_processors.user',
    'ieeetags.context_processors.current_url',
    'ieeetags.context_processors.is_ajax',
)

# Application Settings ---------------------------------------------------------

SHOW_SOCIETY_LOGIN_BANNER = False
'OBSOLETE: Shows a "Welcome" banner on the login page.'

USE_SITEMINDER_LOGIN = False
'If True application authorizes users against IEEE SiteMinder database. Otherwise use local database.'

# Debug Settings ---------------------------------------------------------------

# Used for the COMSOC demo to assign all tags to comsoc by default
DEBUG_IMPORT_ASSIGN_ALL_TAGS_TO_COMSOC = False

# Enable the Help tab on the Manage Society page
DEBUG_ENABLE_MANAGE_SOCIETY_HELP_TAB = True

LOG_FILENAME = None
#LOG_CONSOLE = False

DMIGRATIONS_DIR = relpath(__file__, 'migrations')
DISABLE_SYNCDB = True

DEBUG_PRINT_EXCEPTIONS = False
'Print all exceptions to the console.  Should not be used with WSGI, only local dev.'

DEBUG_EMAIL_EXCEPTIONS = False
'Email all exceptions to the admins.'

DEBUG_ENABLE_EMAIL_TEST = False
'Enable the /debug/email test.'

DEBUG_ENABLE_CPROFILE = False
'Enable the profiling middleware (necessary for the DEBUG_WRITE_PROFILING option).'

DEBUG_WRITE_PROFILING = False
'Writes profiling logs for every request.'

DEBUG_ENABLE_CLUSTERS = True
'Enables clusters in the admin UI.'

DISABLE_SITE = False
'Disables the entire site, printing a "Site is disabled" message.  Used for server maintenance.'

# This setting should be modified in settings.py, not local_settings.py (to ease server configuration tracking)
#ENABLE_TEXTUI_SIMPLIFIED_COLORS = False
ENABLE_TEXTUI_SIMPLIFIED_COLORS = True
'Enables a single tag color in textui.  Otherwise, two extra color blocks are shown for sector/related tag popularity.  This is on by default, and the alternate color blocks method should be removed at some point.'

# Local Settings ---------------------------------------------------------------

try:
    from local_settings import *
except ImportError, e:
    print 'ERROR: "local_settings.py" file not found'

# Check for mandatory settings -------------------------------------------------

MANDATORY_VARS = [
    'DATABASE_NAME',
    'DATABASE_USER',
    'DATABASE_PASSWORD',
    'EMAIL_HOST',
    'SERVER_EMAIL',
    'DEFAULT_FROM_EMAIL',
]

for varname in MANDATORY_VARS:
    if varname not in globals() or globals()[varname] is None:
        logging.error('local_settings.py variable "%s" is not set' % varname)
        raise Exception('local_settings.py variable "%s" is not set' % varname)

# Profiling setup

if DEBUG_ENABLE_CPROFILE:
    list1 = list(MIDDLEWARE_CLASSES)
    list1.append('ieeetags.middleware.ProfilingMiddleware.CProfilerMiddleware')
    MIDDLEWARE_CLASSES = tuple(list1)

# Logging setup

logging.basicConfig(
    level = logging.DEBUG,
    #format = '%(asctime)s %(levelname)s %(message)s',
    format = '%(levelname)s %(message)s',
)

# Check if the logger has been setup yet, otherwise we create a new handler everytime settings.py is loaded
if not hasattr(logging, "is_setup"):
    if LOG_FILENAME is not None:
        # Add the file handler
        file_logger = logging.FileHandler(LOG_FILENAME)
        file_logger.setLevel(logging.DEBUG)
        file_logger.setFormatter(logging.Formatter('%(asctime)s: %(levelname)s: %(message)s'))
        logging.getLogger().addHandler(file_logger)
    
    logging.is_setup = True
