"""
Django settings for the ieeetags project.
"""

import logging
import os
from django.core.urlresolvers import reverse_lazy

from core.util import relpath

RELEASE_VERSION = "1.34"

DEBUG = False

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)
'This stores all admins.  By default they will receive any errors.'

MANAGERS = ADMINS

# Database Settings

DATABASE_ENGINE = 'mysql'
DATABASE_NAME = None
DATABASE_USER = None
DATABASE_PASSWORD = None
DATABASE_HOST = ''
DATABASE_PORT = ''

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
STATIC_ROOT = relpath(__file__, 'static')
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

# EXTERNAL_XPLORE_URL = 'http://ieeexplore.ieee.org/gateway/ipsSearch.jsp?'
EXTERNAL_XPLORE_URL = 'http://ieeexplore.ieee.org/gateway/ipsSearch.jsp?'
EXTERNAL_XPLORE_AUTHORS_URL = \
    'http://ieeexplore.ieee.org/gateway/ipsSearch.jsp?'
# EXTERNAL_XPLORE_AUTHORS_URL = \
#     'http://xploreqa.ieee.org/gateway/ipsSearch.jsp?'
EXTERNAL_XPLORE_TIMEOUT_SECS = 10
XPLORE_TIMEOUT_RECENT_MESSAGE = 'Xplore is not currently responding. ' \
                                'Please try again later.'

MOBILE_URL_PREFIX = 'm.'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'o5tqsvh$&e3@@jzm)uvc02s*lsuw+5*r6jd%d+8u-6lzi3i%6j'

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

# Address from which non-error emails will be sent
DEFAULT_FROM_EMAIL = \
    'IEEE Technology Navigator <technav_admin@systemicist.com>'

# Google Analytics
GA_SITE_NUM = 1

# Live search options
ENABLE_SEARCH_BUTTON = True
SEARCH_KEY_DELAY = 500

# JoyRide tour
ENABLE_JOYRIDE = True

# Jobs settings
JOBS_URL = "http://jobs.ieee.org/jobs/search/results"

# External resources' urls
EXTERNAL_RESOURCE_URLS = {
    'job': "http://jobs.ieee.org/jobs/-%(id)s-d",
    'author': "http://ieeexplore.ieee.org/search/searchresult.jsp?"
              "facet=d-au&refinements=%(id)s",
    'article': "http://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=%(id)s",
    'video': "http://ieeetv.ieee.org/%(id)s",
    'educational course': "http://ieeexplore.ieee.org/stamp/stamp.jsp?"
                          "arnumber=%(id)s",
}

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    # 'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = [
    #'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'core.middleware.ExceptionMiddleware.ExceptionMiddleware',
    # 'core.djangologging.middleware.LoggingMiddleware',
    # 'core.middleware.ProfilingMiddleware.ProfileMiddleware',
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
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.humanize',
    'django.contrib.sitemaps',
    'django.contrib.staticfiles',
    # 'south',
    'rest_framework',
    'rest_framework_swagger',
    'webapp',
    'core',
    'site_admin',
    'api',
    'noomake',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.linkedin_oauth2',
]

STATIC_URL = '/static/'

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'core.context_processors.media_url',
    'core.context_processors.logo_href',
    'core.context_processors.external_help_url',
    'core.context_processors.user',
    'core.context_processors.current_url',
    'core.context_processors.is_ajax',
    'core.context_processors.survey',
    'core.context_processors.django_settings',
    'core.context_processors.host_info',
    'core.context_processors.total_tag_count',
    'core.context_processors.socialauth_using_providers',
    "allauth.account.context_processors.account",
    "allauth.socialaccount.context_processors.socialaccount",
)

# Application Settings -------------------------------------------------------

# auth and allauth settings
LOGIN_REDIRECT_URL = reverse_lazy('login_redirect')
ACCOUNT_USER_DISPLAY = 'webapp.models.profile.email_user_display'
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['https://www.googleapis.com/auth/userinfo.profile',
                  'https://www.googleapis.com/auth/userinfo.email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    },
    'facebook': {
        'SCOPE': ['email', 'publish_stream'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'METHOD': 'oauth2',
    },
    'linkedin': {
        'SCOPE': ['r_emailaddress'],
        'PROFILE_FIELDS': ['id', 'first-name', 'last-name', 'email-address',
                           'picture-url', 'public-profile-url'],
    },
}

SOCIALACCOUNT_KEYS = {
    'google': {
        'client_id': '769505530548-k75b93tfttmhaojb1vf3btca36dljjrd.'
                     'apps.googleusercontent.com',
        'secret': '_UrMw6FDhYpiUuw3MWsJzWH5',
    },
    'linkedin_oauth2': {
        'client_id': '77b5n1cbs93nzw',
        'secret': 'B9HdT4f7VSoV0T8J',
    }
}

USING_GOOGLE_PROVIDER = True
USING_LINKEDIN_PROVIDER = False
USING_FACEBOOK_PROVIDER = False

# If True application authorizes users against IEEE SiteMinder database.
# Otherwise use local database.'
USE_SITEMINDER_LOGIN = False

# If False the optional_login_required decorator will allow unauthenticated
# users.
REQUIRE_LOGIN_FOR_NON_ADMIN_VIEWS = False

# Django Debug Toolbar Settings ----------------------------------------------

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

# Must be set in local_settings.py.
# The path wherein to save the xplore import process log files.
# XPLORE_IMPORT_LOG_PATH = None

# Will be used for the "hc" parameter when querying xplore.
# Controls the max number of results returned.
XPLORE_IMPORT_MAX_QUERY_RESULTS = 10

# Disable south logging.
# import south.logger
# logging.getLogger('south').setLevel(logging.CRITICAL)

# This forces south to use 'syncdb' when running tests, vs. using the
# migrations.
SOUTH_TESTS_MIGRATE = False

# Debug Settings -------------------------------------------------------------

# Used for the COMSOC demo to assign all tags to comsoc by default
DEBUG_IMPORT_ASSIGN_ALL_TAGS_TO_COMSOC = False

# Enable the Help tab on the Manage Society page
DEBUG_ENABLE_MANAGE_SOCIETY_HELP_TAB = True

LOG_FILENAME = None
PROCESS_CONF_DIFF_LOG = None
#LOG_CONSOLE = False

DMIGRATIONS_DIR = relpath(__file__, 'migrations')
DISABLE_SYNCDB = True

# Print all exceptions to the console.
# Should not be used with WSGI, only local dev.
DEBUG_PRINT_EXCEPTIONS = False

# Email all exceptions to the admins.
DEBUG_EMAIL_EXCEPTIONS = False

# Enable the /debug/email test.
DEBUG_ENABLE_EMAIL_TEST = False

# Enable the profiling middleware
# (necessary for the DEBUG_WRITE_PROFILING option).
DEBUG_ENABLE_CPROFILE = False

# Writes profiling logs for every request.
DEBUG_WRITE_PROFILING = False

# Enables clusters in the admin UI.
DEBUG_ENABLE_CLUSTERS = True

# Disables the entire site, printing a "Site is disabled" message.
# Used for server maintenance.
DISABLE_SITE = False

# Enables firebug lite JS.
ENABLE_FIREBUG_LITE = False

# Specifies the folder to store profiler output.
PROFILER_OUTPUT_ROOT = None

# Saves a line-by-line profiling summary.
# This is mutually exclusive with all the other profiler output settings.
PROFILER_OUTPUT_LINEBYLINE = False

# Saves a .txt summary file in the profiler output folder.
PROFILER_OUTPUT_TXT = True

# Saves a binary cProfile file in the profiler output folder.
PROFILER_OUTPUT_BINARY = True

# Saves a PNG callgraph in the profiler output folder.
PROFILER_OUTPUT_PNG = True

# Saves a binary kCacheGrind file in the profiler output folder.
PROFILER_OUTPUT_KCACHEGRIND = True

# Enables the "Show Clusters" link on textui page.
ENABLE_SHOW_CLUSTERS_CHECKBOX = False

# Enables the "Show Terms" link on textui page.
ENABLE_SHOW_TERMS_CHECKBOX = False

ENABLE_DEBUG_TOOLBAR = False

# Enables loading the tags progressively (piecemeal) for textui page.
ENABLE_PROGRESSIVE_LOADING = True

# If enabled, the cache is never used
# (ie. pages are regenerated for each view).
DEBUG_IGNORE_CACHE = False

# Local Settings -------------------------------------------------------------

try:
    from local_settings import *
except ImportError, e:
    print 'ERROR: "local_settings.py" file not found'

# django debug toolbar
# if DEBUG:
#     INSTALLED_APPS += (
#         'debug_toolbar.apps.DebugToolbarConfig',
#         # 'debug_toolbar',
#     )
#
#     MIDDLEWARE_CLASSES += (
#         'debug_toolbar.middleware.DebugToolbarMiddleware',
#     )
#
#     DEBUG_TOOLBAR_PANELS = (
#         'debug_toolbar.panels.version.VersionDebugPanel',
#         'debug_toolbar.panels.timer.TimerDebugPanel',
#         'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
#         'debug_toolbar.panels.headers.HeaderDebugPanel',
#         'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
#         'debug_toolbar.panels.template.TemplateDebugPanel',
#         'debug_toolbar.panels.sql.SQLDebugPanel',
#         'debug_toolbar.panels.signals.SignalDebugPanel',
#         'debug_toolbar.panels.logger.LoggingPanel',
#     )

# Setup testing database -----------------------------------------------------

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

# Check for mandatory settings -----------------------------------------------

MANDATORY_VARS = [
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
    list1.append('core.middleware.ProfilingMiddleware.CProfilerMiddleware')
    MIDDLEWARE_CLASSES = tuple(list1)

# Logging setup
logging.basicConfig(
    level=logging.DEBUG,
    #format='%(asctime)s %(levelname)s %(message)s',
    format='%(levelname)s %(message)s',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d '
                      '%(thread)d %(message)s'
        },
    },
    'handlers': {
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.raven_compat.handlers.'
                     'SentryHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}

# Check if the logger has been setup yet, otherwise we create a new handler
# everytime settings.py is loaded
if not hasattr(logging, "is_setup"):
    if LOG_FILENAME is not None:
        # Add the file handler
        file_logger = logging.FileHandler(LOG_FILENAME)
        file_logger.setLevel(logging.DEBUG)
        file_logger.setFormatter(logging.Formatter(
            '%(asctime)s: %(levelname)s: %(message)s'))
        logging.getLogger().addHandler(file_logger)

        process_conf_diff_logger = logging.FileHandler(PROCESS_CONF_DIFF_LOG)
        process_conf_diff_logger.setLevel(logging.DEBUG)
        process_conf_diff_logger.setFormatter(
            logging.Formatter('%(asctime)s: %(levelname)s: %(message)s'))
        logging.getLogger('process_conf_diff').\
            addHandler(process_conf_diff_logger)

    logging.is_setup = True

# if ENABLE_DEBUG_TOOLBAR and 'debug_toolbar' not in INSTALLED_APPS:
#     MIDDLEWARE_CLASSES.append('debug_toolbar.middleware.'
#                               'DebugToolbarMiddleware')
#     INSTALLED_APPS.append('debug_toolbar.apps.DebugToolbarConfig')
#     # INSTALLED_APPS.append('debug_toolbar')

try:
    if RAVEN_CONFIG:
        INSTALLED_APPS.append('raven.contrib.django.raven_compat')
except NameError:
    pass


TEST_RUNNER = 'django.test.runner.DiscoverRunner'
