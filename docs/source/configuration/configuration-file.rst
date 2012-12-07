.. _configuration:

Configuration
=============

Some of the more important parts of the configuration module for the cdr_stats,
``settings_local.py``, are explained below.

``APPLICATION_DIR`` now contains the full path of the project folder and can be used elsewhere
in the ``settings.py`` module so that the project may be moved around the system without having to
worry about changing any hard-coded paths. ::

    import os.path
    APPLICATION_DIR = os.path.dirname(globals()['__file__'])

Turns on debug mode allowing the browser user to see project settings and temporary variables. ::

    DEBUG = True

Sends all errors from the production server to the admin's email address. ::

    ADMINS = ( ('xyz', 'xyz@abc.com') )


Sets up the options required for Django to connect to your database engine::

    DATABASES = {
        'default': {
            # Add 'postgresql_psycopg2','postgresql','mysql','sqlite3','oracle'
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'DATABASENAME',
            'USER': 'DB_USERNAME',
            'PASSWORD': 'DB_PASSWORD',
            'HOST': 'DB_HOSTNAME',
            'PORT': 'DB_PORT',
            'OPTIONS': {
                #Needed on Mysql
                # 'init_command': 'SET storage_engine=INNODB',
                #Postgresql Autocommit
                'autocommit': True,
            }
        }
    }


Sets up the options to connect to MongoDB Server, this server and database will be used to store the analytic data.
There is usually no need to change these settings, unless if your MongoDB server is on a remote server, or if
different names are required for the collections::

    #MONGODB
    #=======
    MONGO_CDRSTATS = {
        'DB_NAME': 'cdr-stats',
        'HOST': 'localhost',
        'PORT': 27017,
        'CDR_COMMON': 'cdr_common',
        'DAILY_ANALYTIC': 'daily_analytic',
        'MONTHLY_ANALYTIC': 'monthly_analytic',
        'CONC_CALL': 'concurrent_call',
        'CONC_CALL_AGG': 'concurrent_call_aggregate'
    }


Tells Django where to find your media files such as images that the ``HTML
templates`` might use. ::

    MEDIA_ROOT = os.path.join(APPLICATION_DIR, 'static')

    ROOT_URLCONF = 'urls'


Tells Django to start finding URL matches at in the ``urls.py`` module in the ``cdr_stats`` project folder. ::

      TEMPLATE_DIRS = ( os.path.join(APPLICATION_DIR, 'templates'), )


Tells Django where to find the HTML template files::

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

Tells Django which applications (custom and external) to use in the project.
The custom applications, ``cdr`` etc. are stored in the project folder along with
these custom applications.


.. _configuration-country-reporting:

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

PREFIX_LIMIT_MIN & PREFIX_LIMIT_MAX are used to determine how many digits are used to match against the dialcode prefix database, e.g::

    PREFIX_LIMIT_MIN = 2
    PREFIX_LIMIT_MAX = 5

If a phone number has less digits  than PN_MIN_DIGITS it will be considered an extension::

    PN_MIN_DIGITS = 6
    PN_MAX_DIGITS = 9

If a phone number has more digits than PHONENUMBER_DIGITS_MIN but less than PHONE_DIGITS_MAX then the phone number will be considered as local or national call and the LOCAL_DIALCODE will be added::

    LOCAL_DIALCODE = 1

Set the dialcode of your country (44 for UK, 1 for US)::

    PREFIX_TO_IGNORE = "+,0,00,000,0000,00000,011,55555,99999"

List of prefixes to ignore, these prefixes are removed from the phone number prior to analysis. In cases where
customers dial 9 for an outside line, 9, 90 or 900 may need to be removed as well to ensure accurate reporting.


Examples
~~~~~~~~

So for the USA, to cope with 10 or 11 digit dialling, PN_MAX_DIGITS would be set to 10, and LOCAL_DIALCODE set to 1. Thus 10 digit numbers would have a 1 added, but 11 digit numbers are left untouched.

In the UK, the number of significant digits is either 9 or 10 after the "0" trunk code. So to ensure that all UK numbers had 44 prefixed to them and the single leading 0 removed, the prefixes to ignore would include 0, the PN_MAX_DIGITS would be set to 10, and the LOCAL_DIALCODE would be 44.

In Spain, where there is no "0" trunk code, and the length of all numbers is 9, then the PN_MAX_DIGITS  would be set to 9, and the LOCAL_DIALCODE set to 34.

NB: After changing this file, then both celery and apache should be restarted.


.. _resetting-data:

Resetting Data
--------------

Sometimes, some experimentation is required to get the optimum settings for country reporting, to achieve this the data is removed
from MongoDB and re-imported from the Asterisk MySQL database.

1. Stop Celery

2. Type mongo to enter the MongoDB database then apply the following commands::

    mongo
    use cdr-stats;
    db.monthly_analytic.remove({});
    db.daily_analytic.remove({});
    db.aggregate_world_report.remove({});
    db.aggregate_result_cdr_view.remove({});
    db.aggregate_hourly_country_report.remove({});
    db.cdr_common.remove({});

    CTRL-D exits the console.

3. Flag the CDR records for reimport
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

3a. With Asterisk and Mysql ::

    Go to the CDR database in Asterisk and change the field 'import_cdr' to 0:

    Enter the MySQL console with the following command, changing the credentials and database name
    to suit your installation:
    mysql -uasteriskuser -pamp109 asteriskcdrdb

    update cdr SET import_cdr = 0;

    CTRL-C exits the MySQL


3b. With FreeSWITCH and MongoDB::

    Go to the CDR FreeSWITCH MongoDB database, update all the records by setting the 'import_cdr' field to 0.

    mongo
    use freeswitch_cdr;
    db.cdr.update({"import_cdr" : 1}, { $set : {"import_cdr" : 0}}, { multi: true });

4. Now start Celery.
5. Wait while the CDR are re-imported.


.. _configuration-asterisk:

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

To add a new remote Asterisk MySQL CDR store,  ensure that there is a connection to the remote MySQL database, then uncomment the new server settings by removing the # and configuring the credentials to connect to the remote Asterisk CDR store.



.. _realtime-configuration-asterisk:

Realtime configuration for Asterisk
------------------------------------

The Asterisk Manager settings allow CDR-Stats to retrieve Realtime information.

The settings to configure are::

    #Asterisk Manager / Used for Realtime and Concurrent calls
    ASTERISK_MANAGER_HOST = 'localhost'
    ASTERISK_MANAGER_USER = 'cdrstats_user'
    ASTERISK_MANAGER_SECRET = 'cdrstats_secret'


In Asterisk, add a new user in manager.conf, or one of its #include's for CDR-Stats. Further information about Asterisk Manager can be found here : http://www.voip-info.org/wiki/view/Asterisk+config+manager.conf

.. _configuration-freeswitch:

Import configuration for FreeSWITCH
------------------------------------

Freeswitch settings are under the CDR_BACKEND section, and should look as follows::

    CDR_BACKEND = {
        '127.0.0.1': {
            'db_engine': 'mongodb',  # mysql, pgsql, mongodb
            'cdr_type': 'freeswitch',  # asterisk or freeswitch
            'db_name': 'freeswitch_cdr',
            'table_name': 'cdr',  # collection if mongodb
            'host': 'localhost',
            'port': 3306,  # 3306 mysql, 5432 pgsql, 27017 mongodb
            'user': '',
            'password': '',
        },
        #'192.168.1.15': {
        #    'db_engine': 'mongodb',  # mysql, pgsql, mongodb
        #    'cdr_type': 'freeswitch',  # asterisk or freeswitch
        #    'db_name': 'freeswitch_cdr',
        #    'table_name': 'cdr',  # collection if mongodb
        #    'host': 'localhost',
        #    'port': 3306,  # 3306 mysql, 5432 pgsql, 27017 mongodb
        #    'user': '',
        #    'password': '',
        #},
    }


To connect a new Freeswitch system to CDR-Stats, ensure that port 27017 TCP is ONLY open to
the CDR-Stats server on the remote system, then uncomment the settings by removing the #,
and configure the IP address and db_name to match those in the mod_cdr_mongodb configuration
as described at :
http://www.cdr-stats.org/documentation/beginners-guide/howto-installing-on-freeswitch/

Configuring Email
-----------------

To configure the SMTP client so that reports and alerts are sent via email, edit 
/usr/share/cdr-stats/settings_local.py, and identify the email section::

    #EMAIL BACKEND
    #=============
    # Email configuration
    DEFAULT_FROM_EMAIL = 'CDR-Stats <cdr-...@localhost.com>'
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_USE_TLS = True
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_HOST_USER = 'user...@gmail.com'
    EMAIL_HOST_PASSWORD = 'password'
    EMAIL_SUBJECT_PREFIX = '[CDR-Stats] '

Fill in the details to match your SMTP server. The above example is for Gmail. When done, restart Celery and Apache.

To test that the email is working, from the command line type::

    $ cd /usr/src/cdr-stats/
    $ workon cdr-stats
    $ python manage.py send_daily_report


