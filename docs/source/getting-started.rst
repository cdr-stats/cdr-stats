:Web: http://www.cdr-stats.org/
:Download: http://www.cdr-stats.org/download/
:Source: https://github.com/Star2Billing/cdr-stats/
:Keywords: voip, freeswitch, asterisk, django, python, call, reporting, 
   CDR, mongoDB

--

.. _getting_started:

Getting Started
===============

CDR-Stats is free and open source call detail record analysis and reporting software for Freeswitch, 
Asterisk and other type of VoIP Switch. It allows you to interrogate your CDR to provide reports 
and statistics via a simple to use, yet powerful, web interface.

It is based on the Django Python Framework, Celery, SocketIO, Gevent and MongoDB.

.. _`Freeswitch`: http://www.freeswitch.org/
.. _`Asterisk`: http://www.asterisk.org/
.. _`Django`: http://djangoproject.com/
.. _`CDR`: http://en.wikipedia.org/wiki/Call_detail_record


.. contents::
    :local:
    :depth: 1

.. _overview:

Overview
--------

CDR-Stats is an application that allows you to browse and analyse CDR (Call Detail Records).

Different reporting tools are provided:

- Search CDR: Search, filter, display and export CDR.
- Monthly Report: Summarise and compare call traffic history month on month.
- Analyse CDR : Analyse and compare call volumes with the previous day’s traffic.
- Daily Traffic : Graph and filter traffic loads by hour during the day.

MongoDB is an open source, document-oriented database designed with both scalability
and developer agility in mind. Instead of storing your data in tables and rows as
you would with a relational database, in MongoDB you store JSON-like documents with
dynamic schemas. The goal of MongoDB is to bridge the gap between key-value stores
(which are fast and scalable) and relational databases (which have rich functionality).

??? talk about Voip Switch supported


Screenshot Dashboard
~~~~~~~~~~~~~~~~~~~~

.. image:: ./_static/images/customer/dashboard.png
    :width: 1000


Screenshot Admin UI
~~~~~~~~~~~~~~~~~~~

.. image:: ./_static/images/admin/admin_dashboard.png
    :width: 1000


.. _utility:

Utility
-------

CDR-Stats is a great tool to provide easy analysist of your calls, it's a needed addition to your VoIP servers, if you are reselling or using VoIP services you will find CDR-Stats useful.
You will be able to keep an eye quickly of what calls passing through your Switches and detect errors, failure but also receive alert if unexpected calls or type of traffic is happening through your server.


.. _architecture:

Architecture
------------

Add graph on Architect 


.. _features:

Features
--------
 
A lot of features are provided on CDR-Stats, from browsing millions of CDRs, providing efficient search to build rich reporting such as monthly report, concurrent calls view, compare call traffic to previous days.

- Visualize your traffic and help you to understand it
- Map view, see where the traffic comes from and where it goes
- Compare traffic to previous dates, see how your traffic evolve
- Monitor your VoIP server, set alert to detect frauds
- Send daily mail report of your VoIP traffic
- See your traffic in Realtime
- Blacklist Phone number paterns to receive alarm
- Geographic alerts

Add more features


.. _latest_documentation:

Latest documentation
--------------------

The `latest documentation`_ with user guides, tutorials and API reference
is hosted at "Readthedocs".

.. _`latest documentation`: http://cdr-stats.readthedocs.org/

