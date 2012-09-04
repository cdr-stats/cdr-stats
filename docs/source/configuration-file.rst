.. _confifuration:

Configuration
=============

Some of the more important parts of the configuration module for the cdr_stats,
``settings.py``, are explained below::

  import os.path
  APPLICATION_DIR = os.path.dirname(globals()['__file__'])

``APPLICATION_DIR`` now contains the full path of your project folder and can be used elsewhere
in the ``settings.py`` module so that your project may be moved around the system without you having to
worry about changing any hard-coded paths. ::

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

      #MONGODB
      #=======
      MG_DB_NAME = 'cdr-stats'
      MG_HOST = 'localhost'
      MG_PORT = 27017

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


.. _confifuration-country-reporting:

Country Reporting
-----------------

CDR-Stats is able to identify the destination country of the call. This is a
useful fraud prevention measure, so that calls to unexpected destinations
are immediately apparent. Places that should not be called should be added
in the Blacklist in the admin section so that these destinations are
highlighted in the call data records.

However, in order to get accurate reporting, the call detail records have to
be in international format, e.g. in the USA, this means 11 digit numbers,
beginning with a 1, and for other countries, the numbers called should be
prefixed with the international dial code.

There is a facility for manipulating the dialled digits reported in the call
detail records, as well as identifying calls as internal calls. This is done
in the "general" section of /usr/share/cdr-stats/settings_local.py.

PREFIX_LIMIT_MIN & PREFIX_LIMIT_MAX are used to determine how many digits are used to match against the dialcode prefix database, e.g

* **PREFIX_LIMIT_MIN = 2**
* **PREFIX_LIMIT_MAX = 5**

If a phone number has less digits  than PN_MIN_DIGITS it will be considered an extension::

* **PN_MIN_DIGITS = 6**
* **PN_MAX_DIGITS = 9**

If a phone number has more digits than PHONENUMBER_DIGITS_MIN but less than PHONE_DIGITS_MAX then the phone number will be considered as local or national call and the LOCAL_DIALCODE will be added.

* **LOCAL_DIALCODE = 1**

Set the dialcode of your country (44 for UK, 1 for US)

* **PREFIX_TO_IGNORE = "+,0,00,000,0000,00000,011,55555,99999"**

List of prefixes to ignore, these prefixes are removed from the phone number prior to analysis.


Examples
~~~~~~~~

So for the USA, to cope with 10 or 11 digit dialling, PN_MAX_DIGITS would be set to 10, and LOCAL_DIALCODE set to 1. Thus 10 digit numbers would have a 1 added, but 11 digit numbers are left untouched.

In the UK, the number of significant digits is either 9 or 10 after the "0" trunk code. So to ensure that all UK numbers had 44 prefixed to them and the single leading 0 removed, the prefixes to ignore would include 0, the PN_MAX_DIGITS would be set to 10, and the LOCAL_DIALCODE would be 44.

In Spain, where there is no "0" trunk code, and the length of all numbers is 9, then the PN_MAX_DIGITS  would be set to 9, and the LOCAL_DIALCODE set to 34.

NB: After changing this file, then both celery and apache should be restarted.


.. _confifuration-asterisk:

Import configuration for Asterisk
---------------------------------


The asterisk settings may be as follows::

#list of CDR Backends to import
    CDR_BACKEND = {
        '127.0.0.1': {
            'db_engine': 'mysql',
            'cdr_type': 'asterisk',
            'db_name': 'asteriskcdrdb',
            'table_name': 'cdr',
            'host': 'localhost',
            'port': '',
            'user': 'root',
            'password': 'password',
        },
        #'192.168.1.200': {
            #'db_engine': 'mysql',
            #'cdr_type': 'asterisk',
            #'db_name': 'asteriskcdrdb',
            #'table_name': 'cdr',
            #'host': 'localhost',
            #'port': '',
            #'user': 'root',
            #'password': 'password',
        #},
    }

To add a new remote Asterisk MySQL CDR store, you would ensure connection to the remote MySQL database, then uncomment the new server settings by removing the # and configuring the credentials to connect to the remote Asterisk CDR store.


.. _confifuration-freeswitch:

Import configuration for FreeSWITCH
------------------------------------

Freeswitch settings are under the MG_IMPORT section, and should look as follows::

    MG_IMPORT = {
        '127.0.0.1': {
            'db_name': 'freeswitch_cdr',
            'host': 'localhost',
            'port': 27017,
            'collection': 'cdr',
        },
        #'192.168.1.15': {
            # 'db_name': 'freeswitch_cdr',
            # 'host': '192.168.1.15',
            # 'port': 27017,
            # 'collection': 'cdr',
        #},
    }


To connect a new Freeswitch system to CDR-Stats, you would ensure that port 27017 TCP
was open to ONLY the CDR-Stats server on the remote system, uncomment the settings
by removing the #, and then configure the IP address and db_name to match those in
the mod_cdr_mongodb configuration as described at
http://www.cdr-stats.org/documentation/beginners-guide/howto-installing-on-freeswitch/

