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

**Answer:** If you have call detail records from an office PBX, telecoms switch(s), or carrier CDR to analyse
then CDR-Stats is a useful tool to analyse the data and look for patterns in the traffic that
may indicate problems or potential fraud. Furthermore, CDR-Stats can be configured to send email
alerts on detection of unusual activity, as well as send daily reports on traffic.


How to start over, delete CDRs and relaunch the import ?
--------------------------------------------------------

**Answer:** First, stop celery and drop your current mongoDB, you can do this with this command::

    $ mongo cdr-stats --eval 'db.dropDatabase();'

Update all your CDRs to be reimported as we flag them after import. This next step is dependant on your CDR store,

Mysql with Asterisk: run this command on the CDR Database::

    $ UPDATE  cdr SET  import_cdr =  '0';

MongoDB with Freeswitch: Run this command in MongoDB

    $ use freeswitch_cdr;
    db.cdr.update({"import_cdr" : 1}, { $set : {"import_cdr" : 0}}, { multi: true });

Start Celery, and check CDR are being imported correctly.


How to debug mail connectivity?
-------------------------------

**Answer:** Use mail_debug to test the mail connectivity::

    $ cd /usr/share/cdr_stats
    $ workon cdr-stats
    $ python manage.py mail_debug



What should I do if I have problems?
------------------------------------

**Answer:**

- Review the installation script, and check that services are running.
- Read the documentation contained in the CDR-Stats website.
- Ask a question on the forum.
- Ask a question on the mailing list
- Purchase support from Star2Billing.
