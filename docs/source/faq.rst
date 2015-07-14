.. _faq:

==========================
Frequently Asked Questions
==========================

.. contents::
    :local:
    :depth: 1

.. _faq-general:

General
=======

.. _faq-when-to-use:


What is CDR-Stats?
------------------

**Answer:** CDR-Stats is a free and open source web based Call Detail Record analysis application with the ability to display reports and graphs.


Why should I use CDR-Stats?
---------------------------

**Answer:** We foresee two main areas where CDR-Stats would be useful. For telecoms companies who wish to mediate and rate call data records, ultimately to create invoices for their customers, as well as do carrier reconciliation, and for organisations that wish to analyse call patterns. For instance: if you have call detail records from an office PBX, telecoms switch(s), or carrier CDR to analyse then CDR-Stats is a useful tool to analyse the data and look for patterns in the traffic that may indicate problems or potential fraud. Furthermore, CDR-Stats can be configured to send email alerts on detection of unusual activity, as well as send daily reports on traffic.


.. _faq-cdr-import:

CDR Import
==========

How to start over and relaunch the import?
------------------------------------------

**Answer:** First stop celery by stopping supervisor::

    $ /etc/init.d/supervisor stop

Then remove the aggregate data, connect on postgresql and enter the following::

    DROP MATERIALIZED VIEW matv_voip_cdr_aggr_hour;
    DROP MATERIALIZED VIEW matv_voip_cdr_aggr_min;

Recreate the Materialized View as follow::

    CREATE MATERIALIZED VIEW matv_voip_cdr_aggr_hour AS
        SELECT
            date_trunc('hour', starting_date) as starting_date,
            country_id,
            switch_id,
            cdr_source_type,
            hangup_cause_id,
            user_id,
            count(*) AS nbcalls,
            sum(duration) AS duration,
            sum(billsec) AS billsec,
            sum(buy_cost) AS buy_cost,
            sum(sell_cost) AS sell_cost
        FROM
            voip_cdr
        GROUP BY
            date_trunc('hour', starting_date), country_id, switch_id, cdr_source_type, hangup_cause_id, user_id;

    CREATE MATERIALIZED VIEW matv_voip_cdr_aggr_min AS
        SELECT
            date_trunc('minute', starting_date) as starting_date,
            country_id,
            switch_id,
            cdr_source_type,
            hangup_cause_id,
            user_id,
            count(*) AS nbcalls,
            sum(duration) AS duration,
            sum(billsec) AS billsec,
            sum(buy_cost) AS buy_cost,
            sum(sell_cost) AS sell_cost
        FROM
            voip_cdr
        GROUP BY
            date_trunc('minute', starting_date), country_id, switch_id, cdr_source_type, hangup_cause_id, user_id;


Then, update all your CDRs from 'import_cdr' PostgreSQL database to be reimported as we flag them after import::

    UPDATE cdr_import SET imported=FALSE;

Restart Celery::

    $ /etc/init.d/supervisor stop

Finally check in the logs file that the CDRs are being imported::

    tail -f /var/log/cdr-stats/djcelery_error.log


.. _faq-debugging:

Debugging
=========

How to debug mail connectivity?
-------------------------------

**Answer:** Use mail_debug to test the mail connectivity::

    $ workon cdr-stats
    $ cd /usr/share/cdrstats
    $ python manage.py mail_debug



What should I do if I have problems?
------------------------------------

**Answer:**

- Review the installation script, and check that services are running.
- Read the documentation contained in the CDR-Stats website: http://docs.cdr-stats.org/en/latest/
- Ask a question on the mailing list: http://www.cdr-stats.org/community/
- Get professional support from the CDR-Stats team (Star2Billing): http://www.cdr-stats.org/support/
