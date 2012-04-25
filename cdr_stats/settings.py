#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2012 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

import os
import djcelery
djcelery.setup_loader()

APPLICATION_DIR = os.path.dirname( globals()[ '__file__' ] )

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
     ('admin', 'admin@cdr-stats.com'),
)

MANAGERS = ADMINS

SERVER_EMAIL = 'cdr-stats@localhost.com'

MANAGERS = ADMINS

DATABASES = {
    'default': {
        # Add 'postgresql_psycopg2','postgresql','mysql','sqlite3','oracle'
        'ENGINE': 'django.db.backends.sqlite3',
        # Or path to database file if using sqlite3.
        'NAME': os.path.dirname(os.path.abspath(__file__)) + '/database/local.db',
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost.
                                         # Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default.
                                         # Not used with sqlite3.
    }
}

CDR_TABLE_NAME = 'cdr' # Name of the table containing the Asterisk/FreeSwitch CDR

# Only the Asterisk CDR table is supported at the moment, 
# but Freeswitch and other platform will be soon
VOIP_PLATFORM = 'asterisk' # asterisk, freeswitch


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True


# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT =  APPLICATION_DIR + "/static/"

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(APPLICATION_DIR, 'static')

COUNTRIES_FLAG_PATH = 'flags/%s.png'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
#MEDIA_URL = 'http://0.0.0.0:8000/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    # os.path.join(APPLICATION_DIR, "resources"),
    ("cdr-stats", os.path.join(APPLICATION_DIR, "resources")),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = ')ey%^d=pk^jxgam92tdqb0z+0bbhk=7dub_0$ttw#u8yj)rgo$'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    #'raven.contrib.django.middleware.SentryResponseErrorIdMiddleware',
    #'raven.contrib.django.middleware.Sentry404CatchMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    #'pagination.middleware.PaginationMiddleware',
    'linaro_django_pagination.middleware.PaginationMiddleware',
    'common.filter_persist_middleware.FilterPersistMiddleware',
    'mongodb_connection_middleware.MongodbConnectionMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
)

ROOT_URLCONF = 'cdr_stats.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join( APPLICATION_DIR, 'templates' ), 
)

INTERNAL_IPS = ('127.0.0.1')

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}


INSTALLED_APPS = (
    #admin tool apps
    'admin_tools',
    'admin_tools.theming',
    'admin_tools.menu',
    'admin_tools.dashboard',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.markup',
    #'django.contrib.admindocs',
    'cdr',
    'cdr_alert',
    'user_profile',
    'dateutil',
    'south',
    #'dilla',
    #'pagination',
    'linaro_django_pagination',
    'djcelery',
    'tastypie',
    'django_socketio',
    #'raven.contrib.django',
    'notification',
    'country_dialcode',
)

# Debug Toolbar
try:
    import debug_toolbar
except ImportError:
    pass
else:
    INSTALLED_APPS = INSTALLED_APPS #+ ('debug_toolbar',)
    MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES #+ \
        #('debug_toolbar.middleware.DebugToolbarMiddleware',)
    DEBUG_TOOLBAR_CONFIG = {
        'INTERCEPT_REDIRECTS': False,
    }

# Django extensions
try:
    import django_extensions
except ImportError:
    pass
else:
    INSTALLED_APPS = INSTALLED_APPS + ('django_extensions',)


AUTH_PROFILE_MODULE = 'user_profile.UserProfile'

LOG_COLORSQL_ENABLE = True
LOG_COLORSQL_VERBOSE = True

LOGIN_URL = '/pleaselog/'

#DILLA SETTINGS
#==============
DICTIONARY = "/usr/share/dict/words"
DILLA_USE_LOREM_IPSUM = False  # set to True ignores dictionary
DILLA_APPS = [                          
                'cdr',
             ]
DILLA_SPAMLIBS = [                
                'cdr.cdr_custom_spamlib',
                ]
# To use Dilla
# > python manage.py run_dilla --cycles=100


gettext = lambda s: s

LANGUAGES = (
    ('en', gettext('English')),
    ('fr', gettext('French')),
    ('es', gettext('Spanish')),
    ('pt', gettext('Portuguese')),
    ('de', gettext('German')),
#    ('ru', gettext('Russian')),
)


#DJANGO-ADMIN-TOOL
#=================
ADMIN_TOOLS_MENU = 'cdr_stats.custom_admin_tools.menu.CustomMenu'

ADMIN_TOOLS_INDEX_DASHBOARD = 'cdr_stats.custom_admin_tools.dashboard.CustomIndexDashboard'
ADMIN_TOOLS_APP_INDEX_DASHBOARD = 'cdr_stats.custom_admin_tools.dashboard.CustomAppIndexDashboard'

#CELERY
#======
CARROT_BACKEND = 'ghettoq.taproot.Redis'
#CARROT_BACKEND = 'redis'

BROKER_HOST = 'localhost'  # Maps to redis host.
BROKER_PORT = 6379         # Maps to redis port.
BROKER_VHOST = 0        # Maps to database number.


CELERY_RESULT_BACKEND = 'redis'
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
#REDIS_CONNECT_RETRY = True

#SOCKETIO
#========
SOCKETIO_HOST = 'localhost'
SOCKETIO_PORT = 9000

#GENERAL
#=======
PHONE_NO_PREFIX_LIMIT_MIN = 2
PHONE_NO_PREFIX_LIMIT_MAX = 5

#MONGODB
#=======
CDR_MONGO_DB_NAME = 'cdr-stats'
CDR_MONGO_HOST = 'localhost'
CDR_MONGO_PORT = 27017
CDR_MONGO_CDR_COMMON = 'cdr_common'
CDR_MONGO_CONC_CALL = 'concurrent_call'
CDR_MONGO_CDR_COUNTRY_REPORT = 'cdr_country_report'
CDR_MONGO_CONC_CALL_AGG = 'concurrent_call_map_reduce'
CDR_MONGO_CDR_MONTHLY = 'cdr_monthly_analytic'
CDR_MONGO_CDR_DAILY = 'cdr_daily_analytic'
CDR_MONGO_CDR_HOURLY = 'cdr_hourly_analytic'
CDR_MONGO_CDR_HANGUP = 'cdr_hangup_cause_analytic'
CDR_MONGO_CDR_COUNTRY = 'cdr_country_analytic'


#CDR_MONGO_IMPORT define the list of host that you are willing to import cdr from
CDR_MONGO_IMPORT = {
    '127.0.0.1': {
        'host': 'localhost',
        'port': 27017,
        'db_name': 'freeswitch_cdr',
        'collection': 'cdr',
    },
    #'192.168.1.15': {
    #    'host': '192.168.1.15',
    #    'port': 27017,
    #    'db_name': 'freeswitch_cdr',
    #    'collection': 'cdr',
    #},
}

#No of records per page
#=======================
PAGE_SIZE = 10

#TASTYPIE API
#============
API_ALLOWED_IP = ['127.0.0.1', 'localhost']

#EMAIL BACKEND
#=============
# Use only in Debug mode. Not in production
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
#EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

#LOGGING
#=======
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'level': 'DEBUG',
        'handlers': ['default'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(asctime)s %(levelname)s || %(message)s'
        },
    },
    'handlers': {
        # Include the default Django email handler for errors
        # This is what you'd get without configuring logging at all.
        'mail_admins': {
            'class': 'django.utils.log.AdminEmailHandler',
            'level': 'ERROR',
             # But the emails are plain text by default - HTML is nicer
            'include_html': True,
        },
        'default': {
            'class':'logging.handlers.WatchedFileHandler',
            'filename': '/var/log/cdr-stats/cdr-stats.log',
            'formatter':'verbose',
        },
        'default-db': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/cdr-stats/cdr-stats-db.log',
            'maxBytes': 1024*1024*5, # 5 MB
            'backupCount': 20,
            'formatter':'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        # Again, default Django configuration to email unhandled exceptions
        'django': {
            'handlers':['default'],
            'propagate': False,
            'level':'DEBUG',
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'cdr-stats.filelog': {
            'handlers': ['default',],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['default-db'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

#IMPORT LOCAL SETTINGS
#=====================
try:
    from settings_local import *
except:
    pass

#CONNECT MONGODB
#===============

#Connect on MongoDB Database
from pymongo.connection import Connection
from pymongo.errors import ConnectionFailure
import sys
try:
    connection = Connection(CDR_MONGO_HOST, CDR_MONGO_PORT)
    DB_CONNECTION = connection[CDR_MONGO_DB_NAME]
except ConnectionFailure, e:
    sys.stderr.write("Could not connect to MongoDB: %s" % e)
    sys.exit(1)