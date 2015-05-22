.. _configuration-asterisk:

Configuration for Asterisk
==========================

Import configuration for Asterisk
---------------------------------

Review your database settings and ensure the second database exists and that is configured correctly::

    # DATABASE SETTINGS
    # =================
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'cdrstats-billing',
            'USER': 'postgres',
            'PASSWORD': 'password',
            'HOST': 'localhost',
            'PORT': '5433',
            'OPTIONS': {
                # Postgresql Autocommit
                'autocommit': True,
            }
        },
        'import_cdr': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'cdr-pusher',
            'USER': 'postgres',
            'PASSWORD': 'password',
            'HOST': 'localhost',
            'PORT': '5433',
            'OPTIONS': {
                'autocommit': True,
            }
        }
    }

You will need to push your CDRs from Asterisk CDR datastore to a friendly CDR-Stats 'import_cdr' database.
To help on this job we created CDR-Pushed, please visit the website and the instructions there to install and configure CDR-Stats correctly: https://github.com/cdr-stats/cdr-stats


.. _realtime-configuration-asterisk:

Realtime configuration for Asterisk
===================================

The Asterisk Manager settings allow CDR-Stats to retrieve Realtime information to show the number of concurrent calls both in realtime and historically.

In Asterisk, add a new user in manager.conf, or one of its #include's for CDR-Stats. Further information about Asterisk Manager can be found here : http://www.voip-info.org/wiki/view/Asterisk+config+manager.conf

The collection of realtime information is done via Collectd (https://collectd.org/) and InfluxDB (http://influxdb.com/.
