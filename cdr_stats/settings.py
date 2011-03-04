# Django settings for stats project.

import os
APPLICATION_DIR = os.path.dirname( globals()[ '__file__' ] )



DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.dirname(os.path.abspath( __file__ )) + '/database/local.db', # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    },
}

# Only the Asterisk CDR table is supported at the moment, 
# but Freeswitch and other platform will be soon
VOIP_PLATFORM = 'Asterisk' # Asterisk, Freeswitch

# Name of the table containing the Asterisk/FreeSwitch CDR
ASTERISK_CDR_TABLE_NAME = 'cdr'
 

# Base folder for respective templates
BASE_TEMPLATE_PATH = 'cdr/backends/'

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

MEDIA_ROOT = os.path.join( APPLICATION_DIR, 'resources' )
MEDIA_URL = 'http://localhost:8000/resources/'
ADMIN_MEDIA_PREFIX = '/resources/admin/'


# Make this unique, and don't share it with anybody.
SECRET_KEY = ')ey%^d=pk^jxgam92tdqb0z+0bbhk=7dub_0$ttw#u8yj)rgo$'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.csrf.CsrfResponseMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    #'cdr.colorsql.ColorSQLMiddleware',
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
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    'django.contrib.admindocs',
    'cdr',
    'dilla',
    #'debug_toolbar',
    #'django_extensions',
    'dateutil',
    'uni_form',
    'south',
)

AUTH_PROFILE_MODULE = 'cdr.UserProfile'

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
#DILLA_SPAMLIBS = ['cdr.cdr_custom_spamlib']
# To use Dilla
# > python manage.py run_dilla --cycles=100



#LANGUAGES
#===========
gettext = lambda s: s
LANGUAGES = (
    ('en', gettext('English')),
    ('fr', gettext('French')),  
    ('es', gettext('Spanish')),  
    ('br', gettext('Brazilian')),
    ('de', gettext('German')),
#    ('ru', gettext('Russian')),
)

#IMPORT LOCAL SETTINGS
#=====================
try:
    from settings_local import *
except:
    pass

