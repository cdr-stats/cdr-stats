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


DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Your Name', 'your_email@domain.com'),
)
MANAGERS = ADMINS

SERVER_EMAIL = 'cdr-stats@localhost.com'

APPLICATION_DIR = os.path.dirname(globals()['__file__'])

DATABASES = {
    'default': {
        # Add 'postgresql_psycopg2','postgresql','mysql','sqlite3','oracle'
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        # Or path to database file if using sqlite3.
        'NAME': 'cdr_stats_psql',
        'USER': 'postgres',       # Not used with sqlite3.
        'PASSWORD': 'postgres',   # Not used with sqlite3.
        'HOST': 'localhost',      # Set to empty string for localhost.
        'PORT': '',               # Set to empty string for default.
    }
}

CACHES = {
    'default': {
        #'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        #'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': '127.0.0.1:6379',
        #'LOCATION': '/var/tmp/django_cache',
        'TIMEOUT': '600',  # 600 secs
    }
}

#Include for cache machine : http://jbalogh.me/projects/cache-machine/
CACHE_BACKEND = 'caching.backends.locmem://'

#Calls to QuerySet.count() can be cached,
CACHE_COUNT_TIMEOUT = 60  # seconds, not too long.

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
STATIC_ROOT = APPLICATION_DIR + "/static/"

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(APPLICATION_DIR, 'static')

COUNTRIES_FLAG_PATH = 'flags/%s.png'

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
    'dajaxice.finders.DajaxiceFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = ')ey%^d=pk^jxgam92tdqb0z+0bbhk=7dub_0$ttw#u8yj)rgo$'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'geordi.VisorMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
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
    # Put strings here, like "/home/html/django_templates"
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(APPLICATION_DIR, 'templates'),
)

INTERNAL_IPS = ('127.0.0.1')

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

DAJAXICE_MEDIA_PREFIX = "dajaxice"
#DAJAXICE_MEDIA_PREFIX = "dajax"  # http://domain.com/dajax/
#DAJAXICE_CACHE_CONTROL = 10 * 24 * 60 * 60

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
    'api',
    'cdr',
    'cdr_alert',
    'user_profile',
    'frontend',
    'dateutil',
    'south',
    'linaro_django_pagination',
    'djcelery',
    'tastypie',
    'common',
    'notification',
    'country_dialcode',
    #'geordi',
    'gunicorn',
    'apiplayground',
    'frontend_notification',
    'dajaxice',
    'dajax',
)

# Debug Toolbar
try:
    import debug_toolbar
except ImportError:
    pass
else:
    INSTALLED_APPS = INSTALLED_APPS + ('debug_toolbar',)
    MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + \
        ('debug_toolbar.middleware.DebugToolbarMiddleware',)
    DEBUG_TOOLBAR_CONFIG = {
        'INTERCEPT_REDIRECTS': False,
    }

# Nose
try:
    import nose
except ImportError:
    pass
else:
    INSTALLED_APPS = INSTALLED_APPS + ('django_nose',)
    TEST_RUNNER = 'utils.test_runner.MyRunner'

# Debug Toolbar mongo

# commented cause this module doesn't work at the moment
# https://groups.google.com/forum/?fromgroups#!topic/mongoengine-users/cwIdHSNPCwY

try:
    import debug_toolbar_mongo
except ImportError:
    pass
else:
    INSTALLED_APPS = INSTALLED_APPS + ('debug_toolbar_mongo',)

    DEBUG_TOOLBAR_MONGO_STACKTRACES = True
    DEBUG_TOOLBAR_PANELS = (
        'debug_toolbar.panels.version.VersionDebugPanel',
        'debug_toolbar.panels.timer.TimerDebugPanel',
        #Warning: If you run profiling this will duplicate the view execution
        #'debug_toolbar.panels.profiling.ProfilingDebugPanel',
        'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
        'debug_toolbar.panels.headers.HeaderDebugPanel',
        'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
        'debug_toolbar.panels.template.TemplateDebugPanel',
        'debug_toolbar.panels.sql.SQLDebugPanel',
        'debug_toolbar.panels.signals.SignalDebugPanel',
        'debug_toolbar.panels.logger.LoggingPanel',
    )
    DEBUG_TOOLBAR_PANELS = DEBUG_TOOLBAR_PANELS + \
        ('debug_toolbar_mongo.panel.MongoDebugPanel',)


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
DILLA_APPS = ['cdr']
DILLA_SPAMLIBS = ['cdr.cdr_custom_spamlib']
# To use Dilla
# > python manage.py run_dilla --cycles=100


gettext = lambda s: s

LANGUAGES = (
    ('en', gettext('English')),
    ('fr', gettext('French')),
    ('es', gettext('Spanish')),
    ('pt', gettext('Portuguese')),
    ('de', gettext('German')),
    ('ru', gettext('Russian')),
)

# News URL
NEWS_URL = 'http://www.cdr-stats.org/news.php'

#DJANGO-ADMIN-TOOL
#=================
ADMIN_TOOLS_MENU = 'cdr_stats.custom_admin_tools.menu.CustomMenu'
ADMIN_TOOLS_INDEX_DASHBOARD = \
    'cdr_stats.custom_admin_tools.dashboard.CustomIndexDashboard'
ADMIN_TOOLS_APP_INDEX_DASHBOARD = \
    'cdr_stats.custom_admin_tools.dashboard.CustomAppIndexDashboard'
ADMIN_MEDIA_PREFIX = '/static/admin/'

#CELERY
#======
CARROT_BACKEND = 'redis'

BROKER_HOST = 'localhost'  # Maps to redis host
BROKER_PORT = 6379         # Maps to redis port
BROKER_VHOST = 0           # Maps to database number

CELERY_RESULT_BACKEND = 'redis'
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
#REDIS_CONNECT_RETRY = True

CELERY_DEFAULT_QUEUE = 'cdrstats'
CELERY_DEFAULT_EXCHANGE = "cdrstats_tasks"
CELERY_DEFAULT_EXCHANGE_TYPE = "topic"
CELERY_DEFAULT_ROUTING_KEY = "task.cdrstats"
CELERY_QUEUES = {
    'cdrstats': {
        'binding_key': '#',
    },
}

#GENERAL
#=======
# PREFIX_LIMIT_MIN & PREFIX_LIMIT_MAX are used to know
# how many digits are used to match against the dialcode prefix database
PREFIX_LIMIT_MIN = 2
PREFIX_LIMIT_MAX = 5

# If PN is lower than PN_MIN_DIGITS it will be considered as an extension
# If PN is longer than PN_MIN_DIGITS but lower than PN_MAX_DIGITS then
# The PN will be considered as local call and the LOCAL_DIALCODE will be added
LOCAL_DIALCODE = 1  # Set the Dialcode of your country (44 for UK, 1 for US)
PN_MIN_DIGITS = 6
PN_MAX_DIGITS = 9

# List of phonenumber prefix to ignore, this will be remove prior analysis
PREFIX_TO_IGNORE = "+,0,00,000,0000,00000,011,55555,99999"

# When the dialed number is less or equal to INTERNAL_CALL, the call will be considered
# as a internal call, for example when dialed number is 41200
INTERNAL_CALL = 5

#Realtime Graph : set the Y axis limit
REALTIME_Y_AXIS_LIMIT = 300

#ASTERISK IMPORT
#===============
ASTERISK_PRIMARY_KEY = 'acctid'  # acctid, _id

#CDR_BACKEND
#===========
#list of CDR Backends to import
CDR_BACKEND = {
    # '127.0.0.1': {
    #     'db_engine': 'mysql',  # mysql, pgsql, mongodb
    #     'cdr_type': 'asterisk',  # asterisk or freeswitch
    #     'db_name': 'asteriskcdr',
    #     'table_name': 'cdr',  # collection if mongodb
    #     'host': 'localhost',
    #     'port': 3306,  # 3306 mysql, 5432 pgsql, 27017 mongodb
    #     'user': 'root',
    #     'password': 'password',
    # },
    '127.0.0.1': {
        'db_engine': 'mongodb',  # mysql, pgsql, mongodb
        'cdr_type': 'freeswitch',  # asterisk or freeswitch
        'db_name': 'freeswitch_cdr',
        'table_name': 'cdr',  # collection if mongodb
        'host': 'localhost',
        'port': 27017,  # 3306 mysql, 5432 pgsql, 27017 mongodb
        'user': '',
        'password': '',
    },
}

#Define the IP of your local Switch, it needs to exist in the CDR_BACKEND list
LOCAL_SWITCH_IP = '127.0.0.1'

#Asterisk Manager / Used for Realtime and Concurrent calls
ASTERISK_MANAGER_HOST = 'localhost'
ASTERISK_MANAGER_USER = 'cdrstats_user'
ASTERISK_MANAGER_SECRET = 'cdrstats_secret'

#MONGODB
#=======
#Settings of CDR-Stats MongoDB server, this is used to store the analytic data
MONGO_CDRSTATS = {
    'DB_NAME': 'cdr-stats',
    'HOST': 'localhost',
    'PORT': 27017,
    'USER': '',
    'PASSWORD': '',
    'CDR_COMMON': 'cdr_common',
    'DAILY_ANALYTIC': 'daily_analytic',
    'MONTHLY_ANALYTIC': 'monthly_analytic',
    'CONC_CALL': 'concurrent_call',
    'CONC_CALL_AGG': 'concurrent_call_aggregate'
}

#API PLAYGROUND
#==============
API_PLAYGROUND_FEEDBACK = False

#No of records per page
#=======================
PAGE_SIZE = 10

#TOTAL_GRAPH_COLOR For TOTAL Variable
#====================================
TOTAL_GRAPH_COLOR = '#A61700'

# Display Total Countries
#========================
NUM_COUNTRY = 10


#TASTYPIE API
#============
API_ALLOWED_IP = ['127.0.0.1', 'localhost']

#EMAIL BACKEND
#=============
# Email configuration
DEFAULT_FROM_EMAIL = 'CDR-Stats <cdr-stats@localhost.com>'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'username@gmail.com'
EMAIL_HOST_PASSWORD = 'password'
EMAIL_SUBJECT_PREFIX = '[CDR-Stats] '
# Use only in Debug mode. Not in production
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
#EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

#Define the delay in minute between mail notification
#This setting avoid getting span with loads of alarms
DELAY_BETWEEN_MAIL_NOTIFICATION = 10

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
            'include_html': True,
        },
        'default': {
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': '/var/log/cdr-stats/cdr-stats.log',
            'formatter': 'verbose',
        },
        'default-db': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/cdr-stats/cdr-stats-db.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 20,
            'formatter': 'verbose',
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
            'handlers': ['default'],
            'propagate': False,
            'level': 'DEBUG',
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'cdr-stats.filelog': {
            'handlers': ['default'],
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
    connection = Connection(MONGO_CDRSTATS['HOST'], MONGO_CDRSTATS['PORT'])
    DBCON = connection[MONGO_CDRSTATS['DB_NAME']]
    DBCON.autentificate(MONGO_CDRSTATS['USER'], MONGO_CDRSTATS['PASSWORD'])
except ConnectionFailure, e:
    sys.stderr.write("Could not connect to MongoDB: %s" % e)
    sys.exit(1)
