.. _troubleshooting:

===============
Troubleshooting
===============

.. contents::
    :local:
    :depth: 1


.. _find-log-files:

Where to find the log files
===========================

All the logs are centralized into one single directory **/var/log/cdrstats/**


**cdrstats-django-db.log** : This contains all the Database queries performed by the UI


**cdrstats-django.log** : All the logger events from Django


**err-apache-cdrstats.log** : Any apache errors pertaining to CDR-Stats


**celery-cdrstats-node1.log** : This contains celery activity



.. _check-mongodb:

Check if MongoDB is running
===========================

Make sure MongoDB is well installed and running::

    ps auxw | grep mongo

You should see something like::

    mongodb   1184  0.2  0.2 572936  8640 ?        Ssl  Nov25  20:25 /usr/bin/mongod --config /etc/mongodb.conf


If the above failed, you might be willing to try to install MongoDB 2.2 manually : http://www.mongodb.org/


If MongoDB is running fine, you can then check if some data has been pulled correctly. Type the following on shell::

    mongo cdr-stats

Tthen on MongoDB CLI::

    db.cdr_common.findOne();

You should see some data, if it's not the case, backend process of CDR-Stats in charge of retrieving your CDRs and pushing them to MongoDB might have some issue. We will recommend to start by checking Celery logs, then if all the configuration to access database are correct, cf file /usr/share/cdr-stats/settings_local.py



.. _run-debug-mode:

Run in debug mode
=================

Make sure services are stopped first::

    $ /etc/init.d/cdrstats-celeryd stop


Then run in debug mode::

    $ workon cdr-stats
    $ cd /usr/share/cdrstats/
    $ python manage.py celeryd -EB --loglevel=DEBUG



.. _celerymon:

Celerymon
=========

* https://github.com/ask/celerymon

Running the monitor :

Start celery with the --events option on, so celery sends events for celerymon to capture::
    $ workon cdr-stats
    $ cd /usr/share/cdrstats/
    $ python manage.py celeryd -E


Run the monitor server::

    $ workon cdr-stats
    $ cd /usr/share/cdr-stats/
    $ python manage.py celerymon


However, in production the monitor is best run in the background as a daemon::

    $ workon cdr-stats
    $ cd /usr/share/cdrstats/
    $ python manage.py celerymon --detach


For a complete listing of the command line arguments available, with a short description, use the help command::

    $ workon cdr-stats
    $ cd /usr/share/cdrstats/
    $ python manage.py help celerymon


Visit the webserver celerymon stats by going to: http://localhost:8989
