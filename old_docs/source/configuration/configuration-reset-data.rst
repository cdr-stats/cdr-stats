.. _resetting-data:

Resetting CDR Data
==================

Sometimes, some experimentation is required to get the optimum settings for country reporting, to achieve this the data is removed
from MongoDB on CDR-Stats and re-imported from either the Asterisk MySQL CDR store, or the Freeswitch MongoDB CDR-Store.


1. Stop Celery
--------------

Stop CDR-Stats celery::

    /etc/init.d/cdr-stats-celeryd stop


2. Empty the CDR-Stats MonoDB data store
----------------------------------------

Type mongo to enter the MongoDB database then apply the following commands::

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
------------------------------------

    a) With Asterisk and Mysql.

        Go to the CDR database in Asterisk and change the field 'import_cdr' to 0:

        Enter the MySQL console with the following command, changing the credentials and database name
        to suit your installation::

            mysql -uasteriskuser -pamp109 asteriskcdrdb
            update cdr SET import_cdr = 0;

        CTRL-C exits the MySQL


    b) With FreeSWITCH and MongoDB.

        Go to the CDR FreeSWITCH MongoDB database, update all the records by setting the 'import_cdr' field to 0::

            mongo
            use freeswitch_cdr;
            db.cdr.update({"import_cdr" : 1}, { $set : {"import_cdr" : 0}}, { multi: true });

     CTRL-D exits

4. Start Celery
---------------

Start CDR-Stats celery::

    /etc/init.d/cdr-stats-celeryd start


5. Wait while the CDR are re-imported
-------------------------------------

Go to the diagnostic page to check if the CDR-Backend are correctly configured and if data are being imported.
