
.. image:: https://github.com/cdr-stats/cdr-stats/raw/master/docs/source/_static/images/cdr-stats_600.png

.. image:: https://secure.travis-ci.org/Star2Billing/cdr-stats.png?branch=develop


CDR-Stats is an open source CDR_ (Call Detail Record) mediation rating, analysis
and reporting application for Freeswitch, Asterisk, Kamailio and other types of
proprietary VoIP Switch including Sipwise and Veraz. Other types of switch could
be added in the future such as Cisco and Alcatel-Lucent.

It allows you to mediate, rate and interrogate your CDR_ to provide reports and
statistics via a simple to use, yet powerful, web interface.

It is based on the Django_ Python Framework, Celery_, Gevent_, PostgreSQL_ and InfluxDB_.


Features
--------

* Telecommunications CDR Mediation to normalise CDR into the same format for rating.

* Telecoms call rating to put a cost against each call.

* Highly scalable design to maintain high performance when analysing large quantities of data.

* Single and Multi-server architectures to allow reporting on many millions of calls from multiple call data sources.

* Browser Responsive - The pages resize to suit any browsing device so CDR-Stats can be managed from a phone browser, tablet or computer.

* Alarms – Custom alarm triggers can be set for a range of conditions including average length of calls, failed calls, and unexpected destinations called.

* Realtime Reporting of calls in progress on supported platforms.

* Fraud detection - Using graphical tools helps spot patterns which may indicate suspicious or fraudulent activity.

* Multi-tenant System that allows CDR from multiple sources or CDR assigned to customers on the basis of account-code.


Applications
------------

* User UI:
    http://localhost:8008/
    This application provide Reports, CDR Viewing, CDR reporting, Dashboard.
    Users can login and see their CDR only.

.. image:: https://github.com/cdr-stats/cdr-stats/raw/develop/screenshot/cdr-stats-user.png

* Admin UI:
    http://localhost:8008/admin/
    This interface provides user (ACL) management, assignation of accountcode,
    also basic CRUD functions on the CDR

.. image:: https://github.com/cdr-stats/cdr-stats/raw/develop/screenshot/cdr-stats-admin.png


Documentation
-------------

The full Documentation is hosted on ReadtheDocs:

- http://docs.cdr-stats.org/

A Beginner's Guide can be found at:

- http://www.cdr-stats.org/documentation/beginners-guide/


Translation
-----------

Help us translate CDR-Stats, we use Transifex: https://www.transifex.com/projects/p/cdr-stats/


Coding Conventions
------------------

This project is PEP8 compilant and please refer to these sources for the Coding
Conventions :

    - http://docs.djangoproject.com/en/dev/internals/contributing/#coding-style

    - http://www.python.org/dev/peps/pep-0008/


Additional information
-----------------------

Fork the project on GitHub: https://github.com/cdr-stats/cdr-stats

License: MPL 2.0 (https://raw.github.com/cdr-stats/cdr-stats/master/COPYING)

Website: http://www.cdr-stats.org


Support
-------

Star2Billing_ (http://www.star2billing.com) offers consultancy including
installation, training and customization.

Please email us at cdr-stats@star2billing.com for more information.


.. _`CDR`: http://en.wikipedia.org/wiki/Call_detail_record
.. _`Freeswitch`: http://www.freeswitch.org/
.. _`Asterisk`: http://www.asterisk.org/
.. _`Django`: http://djangoproject.com/
.. _`Celery`: http://www.celeryproject.org/
.. _`Gevent`: http://www.gevent.org/
.. _`PostgreSQL`: http://www.postgresql.org/
.. _`InfluxDB`: http://influxdb.com/
.. _`Star2Billing`: http://www.star2billing.com/
