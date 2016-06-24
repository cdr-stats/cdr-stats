.. _resetting-data:

Resetting CDR Data
==================

Sometimes, some experimentation is required to get the optimum settings for
country reporting, to achieve this the data can be removed from CDR-Stats and
re-imported from the CDR data store correctly.


1. Stop Celery
--------------

Stop CDR-Stats celery::

    /etc/init.d/cdr-stats-celeryd stop


2. Empty the CDR-Stats dbshell
------------------------------

Enter in the virtualenv and launch dbshell the following commands::

    $ source /opt/miniconda/envs/cdr-stats/bin/activate /opt/miniconda/envs/cdr-stats
    $ cd /usr/share/cdrstats/
    $ python manage.py dbshell

Now you are connected on PostgreSQL cli, this is the internal database of
CDR-Stats.

The following command will delete all the CDRs, make sure you know what are you
doing here and that your CDRs are backed in the upstream CDR data store.

    $ DELETE FROM voip_cdr;

    CTRL-D exits the console.


3. Flag the CDR records for reimport
------------------------------------

Enter in the virtualenv and launch dbshell the following commands::

    $ source /opt/miniconda/envs/cdr-stats/bin/activate /opt/miniconda/envs/cdr-stats
    $ cd /usr/share/cdrstats/
    $ python manage.py dbshell --database=import_cdr

Enter the postgresql password found in `settings_local_py` conf file.

Now you are connected on PostgreSQL cli, you can flag CDRs for reimport::

    $ UPDATE cdr_import SET imported=FALSE;

    CTRL-D exits the console.


4. Start Celery
---------------

Start CDR-Stats celery::

    /etc/init.d/cdr-stats-celeryd start


5. Wait while the CDR are re-imported
-------------------------------------

Go to the diagnostic page to check if CDR-Stats is correctly configured and if
data is being imported.
