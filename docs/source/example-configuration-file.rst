.. _conf-example:

Sample Configuration
====================

This is a sample configuration to get you started.
It should contain all you need to create a basic set-up.
 
------------------------
The Configuration Module
------------------------

Some of the more important parts of the configuration module for the cdr_stats,
``settings.py``, are explained below::

  import os.path
  APPLICATION_DIR = os.path.dirname(globals()['__file__'])

``APPLICATION_DIR`` now contains the full path of your project folder and can be used elsewhere
in the ``settings.py`` module so that your project may be moved around the system without you having to
worry about changing any troublesome hard-coded paths. ::

  DEBUG = True

turns on debug mode allowing the browser user to see project settings and temporary variables. ::

  ADMINS = ( ('xyz', 'xyz@abc.com') )

sends all errors from the production server to the admin's email address. ::

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

      or

      DATABASES = {
          'default': {
                  'ENGINE': 'django.db.backends.postgresql_psycopg2',
                  'NAME': 'cdr_stats_psql',
                  'USER': 'postgresuser',
                  'PASSWORD': 'postgrespasswd',
                  'HOST': 'localhost',
                  'PORT': '5432',
              }
      }

      or

      DATABASES = {
          'default': {
                  'ENGINE': 'mysql',
                  'NAME': 'cdr_stats_mysql',
                  'USER': 'mysqluser',
                  'PASSWORD': 'mysqlpasswd',
                  'HOST': 'localhost',
                  'PORT': '3306',
              }
      }

      CDR_TABLE_NAME = 'cdr' # Name of the table containing the Asterisk/FreeSwitch CDR

      # Only the Asterisk CDR table is supported at the moment,
      # but Freeswitch and other platform will be soon
      VOIP_PLATFORM = 'asterisk' # asterisk, freeswitch

      #MONGODB
      #=======
      CDR_MONGO_DB_NAME = 'cdr-stats'
      CDR_MONGO_HOST = 'localhost'
      CDR_MONGO_PORT = 27017

sets up the options required for Django to connect to your database. ::

     MEDIA_ROOT = os.path.join(APPLICATION_DIR, 'static')

tells Django where to find your media files such as images that the ``HTML
templates`` might use. ::

     ROOT_URLCONF = 'urls'

tells Django to start finding URL matches at in the ``urls.py`` module in the ``cdr_stats`` project folder. ::

      TEMPLATE_DIRS = ( os.path.join(APPLICATION_DIR, 'templates'), )

tells Django where to find your HTML template files. ::

     INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    ...
    'cdr',
    'cdr_alert',
    ...
    )

tells Django which applications (custom and external) to use in your project.
The custom applications, ``cdr`` etc. are stored in the project folder along with
these custom applications.

Configure different switches ::

    #MongoDB(s) to use for import
    CDR_MONGO_IMPORT = {
        '127.0.0.1': {
            'db_name': 'cdr-stats',
            'host': 'localhost',
            'port': 27017,
            'collection': 'cdr',
        },
        #'192.168.1.15': {
        #    'db_name': 'freeswitch_cdr',
        #    'host': '192.168.1.15',
        #    'port': 27017,
        #    'collection': 'cdr',
        #},
    }