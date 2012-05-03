
.. image:: https://github.com/Star2Billing/cdr-stats/raw/master/docs/source/_static/images/cdr-stats_600.png

CDR-Stats is free and open source web -based call detail record analysis and reporting software for Freeswitch, 
Asterisk and other types of VoIP Switch. It allows interrogation of CDR to provide reports 
and statistics via a simple to use, yet powerful, web interface written to be responsive 
and fluid so it can be viewed on a variety of devices.

It is based on the Django Python Framework, Celery, SocketIO, Gevent and MongoDB.


Features
--------

* Highly scalable design to maintain high performance when querying large quantities of data.

* Single and Multi-server architectures to allow reporting on many millions of calls from multiple call data sources.

* Browser Responsive - The pages resize to suit any browsing device so CDR-Stats can be managed from a phone browser, tablet or computer.

* Alarms – Custom alarm triggers can be set for a range of conditions including average length of calls, failed calls, and unexpected destinations called.

* Realtime Reporting of call in progress on supported platforms.

* Fraud detection - Using graphical tools helps spot patterns which may indicate suspicious or fraudulent activity.

* Multi-tenant System that allows CDR from multiple sources or CDR assigned to customers on the basis of account-code.


Applications
------------

* User UI :
    http://localhost:8008/
    This application provide Reports, CDR Viewing, CDR reporting, Dashboard.
    User with accountcode can login and see only their CDR.

.. image:: https://github.com/Star2Billing/cdr-stats/raw/master/screenshot/cdr-stats-user.png

* Admin UI :
    http://localhost:8008/admin/
    This interface provides user (ACL) management, assigning the accountcode to CDR.
    also basic CRUD functions on the CDR

.. image:: https://github.com/Star2Billing/cdr-stats/raw/master/screenshot/cdr-stats-admin.png


Documentation
-------------

Complete documentation :

    - http://cdr-stats.readthedocs.org/

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

Fork the project on GitHub : https://github.com/Star2Billing/cdr-stats

License : MPL 2.0 (https://raw.github.com/Star2Billing/cdr-stats/master/COPYING)

Website : http://www.cdr-stats.org


Support 
-------

Star2Billing S.L. (http://www.star2billing.com) offers consultancy including 
installation, training and customization 

Please email us at cdr-stats@star2billing.com for more information

