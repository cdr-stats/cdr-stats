
.. image:: https://github.com/areski/cdr-stats/raw/master/docs/source/_static/images/cdr-stats_600.png

.. image:: https://secure.travis-ci.org/Star2Billing/cdr-stats.png?branch=develop


CDR-Stats is a free and open source call detail record analysis and reporting software for Freeswitch,
Asterisk and other types of VoIP Switch. It allows you to interrogate CDR to provide reports
and statistics via a simple to use powerful web interface.

It is based on the Django Python Framework, Celery, Gevent, PostgreSQL and InfluxDB.


Features
--------

* Highly scalable design to maintain high performance when analysing large quantities of data.

* Single and Multi-server architectures to allow reporting on many millions of calls from multiple call data sources.

* Browser Responsive - The pages resize to suit any browsing device so CDR-Stats can be managed from a phone browser, tablet or computer.

* Alarms – Custom alarm triggers can be set for a range of conditions including average length of calls, failed calls, and unexpected destinations called.

* Realtime Reporting of calls in progress on supported platforms.

* Fraud detection - Using graphical tools helps spot patterns which may indicate suspicious or fraudulent activity.

* Multi-tenant System that allows CDR from multiple sources or CDR assigned to customers on the basis of account-code.


Applications
------------

* User UI :
    http://localhost:8008/
    This application provide Reports, CDR Viewing, CDR reporting, Dashboard.
    Users can login and see their CDR only.

.. image:: https://github.com/areski/cdr-stats/raw/master/screenshot/cdr-stats-user.png

* Admin UI :
    http://localhost:8008/admin/
    This interface provides user (ACL) management, assignation of accountcode,
    also basic CRUD functions on the CDR

.. image:: https://github.com/areski/cdr-stats/raw/master/screenshot/cdr-stats-admin.png


Documentation
-------------

Project documentation is hosted on CDR-Stats website :

    - http://www.cdr-stats.org/documentation/

Beginner's Guide :

    - http://www.cdr-stats.org/documentation/beginners-guide/


Translation
-----------

We are using myGengo to ease the translation :
    - http://mygengo.com/string/p/cdr-stats-1/


Coding Conventions
------------------

This project is PEP8 compilant and please refer to these sources for the Coding
Conventions :

    - http://docs.djangoproject.com/en/dev/internals/contributing/#coding-style

    - http://www.python.org/dev/peps/pep-0008/


Additional information
-----------------------

Fork the project on GitHub : https://github.com/areski/cdr-stats

License : MPL 2.0 (https://raw.github.com/areski/cdr-stats/master/COPYING)

Website : http://www.cdr-stats.org


Support
-------

Star2Billing S.L. (http://www.star2billing.com) offers consultancy including
installation, training and customization

Please email us at cdr-stats@star2billing.com for more information

