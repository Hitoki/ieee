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

EXTERNAL_HELP_URL = 'http://help.technav.systemicist.com/forums'

EXTERNAL_XPLORE_URL = 'http://ieeexplore.ieee.org/gateway/ipsSearch.jsp?'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'o5tqsvh$&e3@@jzm)uvc02s*lsuw+5*r6jd%d+8u-6lzi3i%6j'

# Specify the user profile model
AUTH_PROFILE_MODULE = 'ieeetags.profile'

DEFAULT_CHARSET = 'utf-8'

# Outgoing Email Settings

#EMAIL_HOST = None
#EMAIL_PORT = None
#EMAIL_HOST_USER = None
#EMAIL_HOST_PASSWORD = None
#EMAIL_USE_TLS = None

SERVER_EMAIL = None

# Postmark email service setting
EMAIL_BACKEND = 'postmark.django_backend.EmailBackend'

# Default email backend:
#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

POSTMARK_SENDER = 'IEEE Technology Navigator <technav_admin@systemicist.com>'
DEFAULT_FROM_EMAIL = 'IEEE Technology Navigator <technav_admin@systemicist.com>' # Address from which non-error emails will be sent

# Google Analytics
GA_SITE_NUM = 1

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#	 'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = [
    #'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'ieeetags.middleware.ExceptionMiddleware.ExceptionMiddleware',
    #'ieeetags.djangologging.middleware.LoggingMiddleware',
    #'ieeetags.middleware.ProfilingMiddleware.ProfileMiddleware',
]

INTERNAL_IPS = ('127.0.0.1',)

ROOT_URLCONF = 'ieeetags.urls'

TEMPLATE_DIRS = (
    relpath(__file__, 'templates'),
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.humanize',
    'south',
    'ieeetags',
    'ieeetags.site_admin',
    'noomake',
]

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'ieeetags.context_processors.media_url',
    'ieeetags.context_processors.logo_href',
    'ieeetags.context_processors.external_help_url',
    'ieeetags.context_processors.user',
    'ieeetags.context_processors.current_url',
    'ieeetags.context_processors.is_ajax',
    'ieeetags.context_processors.survey',
    'ieeetags.context_processors.settings',
    'ieeetags.context_processors.host_info',
    'ieeetags.context_processors.total_tag_count'
)

# Application Settings ---------------------------------------------------------

USE_SITEMINDER_LOGIN = False
'If True application authorizes users against IEEE SiteMinder database. Otherwise use local database.'

REQUIRE_LOGIN_FOR_NON_ADMIN_VIEWS = False
'If False the optional_login_required decorator will allow unauthenticated users.'

# Django Debug Toolbar Settings ------------------------------------------------

DEBUG_TOOLBAR_CONFIG = {
	'INTERCEPT_REDIRECTS': False,
}

#XPLORE_IMPORT_LOG_PATH = None
#'Must be set in local_settings.py.  The path wherein to save the xplore import process log files.'
XPLORE_IMPORT_MAX_QUERY_RESULTS = 10
'Will be used for the "hc" parameter when querying xplore. Controls the max number of results returned.' 

# Disable south logging.
import south.logger
logging.getLogger('south').setLevel(logging.CRITICAL)

# This forces south to use 'syncdb' when running tests, vs. using the migrations.
SOUTH_TESTS_MIGRATE = False

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

ENABLE_FIREBUG_LITE = False
'Enables firebug lite JS.'

PROFILER_OUTPUT_ROOT = None
'Specifies the folder to store profiler output.'

PROFILER_OUTPUT_LINEBYLINE = False
'Saves a line-by-line profiling summary.  This is mutually exclusive with all the other profiler output settings.'

PROFILER_OUTPUT_TXT = True
'Saves a .txt summary file in the profiler output folder.'

PROFILER_OUTPUT_BINARY = True
'Saves a binary cProfile file in the profiler output folder.'

PROFILER_OUTPUT_PNG = True
'Saves a PNG callgraph in the profiler output folder.'

PROFILER_OUTPUT_KCACHEGRIND = True
'Saves a binary kCacheGrind file in the profiler output folder.'

ENABLE_SHOW_CLUSTERS_CHECKBOX = False
'Enables the "Show Clusters" link on textui page.'

ENABLE_SHOW_TERMS_CHECKBOX = False
'Enables the "Show Terms" link on textui page.'

ENABLE_DEBUG_TOOLBAR = False

ENABLE_PROGRESSIVE_LOADING = True
'Enables loading the tags progressively (piecemeal) for textui page.'

DEBUG_IGNORE_CACHE = False
'If enabled, the cache is never used (ie. pages are regenerated for each view).'

# Local Settings ---------------------------------------------------------------

try:
    from local_settings import *
except ImportError, e:
    print 'ERROR: "local_settings.py" file not found'

# Setup testing database -------------------------------------------------------

import sys
if 'test' in sys.argv:
    print 'Using test database.'
    DATABASE_ENGINE = 'sqlite3'
    DATABASE_NAME = ':memory:'
    DATABASE_USER = ''
    DATABASE_PASSWORD = ''
    DATABASE_HOST = ''
    DATABASE_PORT = ''
    TEST_DATABASE_NAME = ":memory:"

# Check for mandatory settings -------------------------------------------------

MANDATORY_VARS = [
    'DATABASE_NAME',
    'DATABASE_USER',
    'DATABASE_PASSWORD',
    #'EMAIL_HOST',
    #'SERVER_EMAIL',
    'DEFAULT_FROM_EMAIL',
    'XPLORE_IMPORT_LOG_PATH',
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

if ENABLE_DEBUG_TOOLBAR:
    MIDDLEWARE_CLASSES.append('debug_toolbar.middleware.DebugToolbarMiddleware')
    INSTALLED_APPS.append('debug_toolbar')

