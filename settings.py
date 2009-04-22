# Django settings for ieeetags project.

import logging
import os

from util import relpath

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'mysql'
DATABASE_NAME = ''			 # Or path to database file if using sqlite3.
DATABASE_USER = ''			 # Not used with sqlite3.
DATABASE_PASSWORD = ''		 # Not used with sqlite3.
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

EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
#EMAIL_HOST_USER
#EMAIL_HOST_PASSWORD
#EMAIL_USE_TLS

#SERVER_EMAIL = ''
#DEFAULT_FROM_EMAIL = ''

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
    'ieeetags.middleware.ConsoleException.ConsoleExceptionMiddleware',
    #'ieeetags.djangologging.middleware.LoggingMiddleware',
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

# Application Settings

SHOW_SOCIETY_LOGIN_BANNER = False

# Debug Settings

# Used for the COMSOC demo to assign all tags to comsoc by default
DEBUG_IMPORT_ASSIGN_ALL_TAGS_TO_COMSOC = False

# If true, all tags will show up for all filters in Roamer
DEBUG_TAGS_HAVE_ALL_FILTERS = False

# If true, all frontend pages will require login (useful before frontend is publicly launched)
DEBUG_REQUIRE_LOGIN_FRONTEND = True

# Disable all frontend pages until they're finished
DEBUG_DISABLE_FRONTEND = True

# Enable the Help tab on the Manage Society page
DEBUG_ENABLE_MANAGE_SOCIETY_HELP_TAB = False

LOG_FILENAME = relpath(__file__, 'log.txt')
LOG_CONSOLE = True

DMIGRATIONS_DIR = relpath(__file__, 'migrations')
DISABLE_SYNCDB = True

try:
    from local_settings import *
except ImportError, e:
    print 'ERROR: "local_settings.py" file not found'

logging.basicConfig(
    level = logging.DEBUG,
    #format = '%(asctime)s %(levelname)s %(message)s',
    format = '%(levelname)s %(message)s',
)

# Check if the logger has been setup yet, otherwise we create a new handler everytime settings.py is loaded
if not hasattr(logging, "is_setup"):
    
    #print 'setting up logger'
    
    # Add the file handler
    file_logger = logging.FileHandler(LOG_FILENAME)
    file_logger.setLevel(logging.DEBUG)
    file_logger.setFormatter(logging.Formatter('%(asctime)s: %(levelname)s: %(message)s'))
    logging.getLogger().addHandler(file_logger)
    
    #if not hasattr(logging, 'console'):
    #    print 'setting up console logger'
    #    logging.console = logging.getLogger('console')
    #    handler = logging.StreamHandler()
    #    handler.setLevel(logging.DEBUG)
    #    handler.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
    #    logging.console.addHandler(handler)
    
    logging.is_setup = True
    
    #logging.debug('setup logger')

logging.debug('---------------------------------------------------------------------')
logging.debug('settings.py')

if DEBUG:
    MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES)
    MIDDLEWARE_CLASSES.append('ieeetags.middleware.ProfilingMiddleware.ProfileMiddleware')
    MIDDLEWARE_CLASSES = tuple(MIDDLEWARE_CLASSES)
