.. _celery-configuration:

Celery Configuration
====================

-------------------------------------------
After installing Broker (Redis or Rabbitmq)
-------------------------------------------

1. Redis Settings
-----------------

This is a configuration example for Redis.

.. code-block:: python

    # Redis Settings
    CARROT_BACKEND = "ghettoq.taproot.Redis"
    
    BROKER_HOST = "localhost"  # Maps to redis host.
    BROKER_PORT = 6379         # Maps to redis port.
    BROKER_VHOST = "0"         # Maps to database number.
    
    CELERY_RESULT_BACKEND = "redis"
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_DB = 0
    #REDIS_CONNECT_RETRY = True


2. Rabbitmq Settings
--------------------

This is a configuration example for Rabbitmq.

::

    BROKER_HOST = "localhost"
    BROKER_PORT = 5672
    BROKER_USER = "root"
    BROKER_PASSWORD = "root"
    BROKER_VHOST = "localhost"
    
    CELERY_RESULT_BACKEND = "amqp"


--------------------------------------
Launch celery/celerybeat in debug mode
--------------------------------------

If you don't want to run celeryd and celerybeat as a daemon then

To run celeryd ::

    $ python manage.py celeryd -E -l debug

To run celerybeat ::

    $ python manage.py celerybeat --schedule=/var/run/celerybeat-schedule

To run both ::

    $ python manage.py celeryd -E -B -l debug

------------------------------------------------------
Running celeryd/celerybeat as a daemon (Debian/Ubuntu)
------------------------------------------------------

To configure celeryd you will need to tell it where to change directory
to, when it starts in order to find your celeryconfig.
::

$ cd install/celery-init/etc/default/

1) Open celeryd in text editor & change the following variables

   Configuration file:  /etc/default/celeryd

   Init script: `celeryd`_.

   .. _celeryd: https://github.com/Star2Billing/newfies-dialer/raw/master/install/celery-init/etc/init.d/celeryd

   Usage : /etc/init.d/celeryd {start|stop|force-reload|restart|try-restart|status}::

    # Where to chdir at start
    CELERYD_CHDIR="/path/to/newfies/"

    # Path to celeryd
    CELERYD="/path/to/newfies/manage.py celeryd"

    # Extra arguments to celeryd
    CELERYD_OPTS="--time-limit=300"

    # Name of the celery config module.
    CELERY_CONFIG_MODULE="celeryconfig"

    # Extra Available options
    # %n will be replaced with the nodename.
    # Full path to the PID file. Default is /var/run/celeryd.pid.
    CELERYD_PID_FILE="/var/run/celery/%n.pid"

    # Full path to the celeryd log file. Default is /var/log/celeryd.log
    CELERYD_LOG_FILE="/var/log/celery/%n.log"

    # User/Group to run celeryd as. Default is current user.
    # Workers should run as an unprivileged user.
    CELERYD_USER="celery"
    CELERYD_GROUP="celery"


2) Open celeryd (for periodic task) in text editor & add the following variables

   Configuration file:  /etc/default/celerybeat or /etc/default/celeryd

   Init script: `celerybeat`_

   .. _celerybeat: https://github.com/Star2Billing/newfies-dialer/raw/master/install/celery-init/etc/init.d/celerybeat

   Usage:	/etc/init.d/celerybeat {start|stop|force-reload|restart|try-restart|status}::

    # Path to celerybeat
    CELERYBEAT="/path/to/newfies/manage.py celerybeat"

    # Extra arguments to celerybeat
    CELERYBEAT_OPTS="--schedule=/var/run/celerybeat-schedule"


3) Copy the configuration file & init scripts to /etc dir::

    $ cp etc/default/celeryd /etc/default/

    $ cp etc/init.d/celeryd /etc/init.d/

    $ cp etc/init.d/celerybeat /etc/init.d/


4) Run/Start or Stop celery as a daemon::

    $ /etc/init.d/celeryd start or stop

    $ /etc/init.d/celerybeat start or stop

---------------
Troubleshooting
---------------

If you can't get the celeryd as a daemon to work, you should try running them in verbose mode::

    $ sh -x /etc/init.d/celeryd start

    $ sh -x /etc/init.d/celerybeat start
