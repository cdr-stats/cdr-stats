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


