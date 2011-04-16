===============
About CDR-Stats
===============


What is CDR-Stats
-----------------

CDR-Stats is a CDR viewer for Asterisk/Freeswitch Call Data Records. It allows you to interrogate your CDR to provide reports and statistics via a simple to use, yet powerful, web interface.

It is based on the Django Python Framework which enables the building of clean, maintainable web applications, and encourages rapid development with clean and pragmatic design.

Star2Billing S.L. is the company behind the development of CDR-Stats, and was originally formed to provide a revenue stream to support the popular open source A2Billing Telecom Switch and Billing System by providing professional support, installation and consultancy services.


How to use it
-------------

CDR-Stats comes with 2 web interfaces, one for Customers and one for Admins.

User Interface :
http://localhost:8000/ This application provide Report, CDR View, several CDR reporting, Dashboard. User with accountcode can login and see their restrected data


Admin UI :
http://localhost:8000/admin/ This interface provides user (ACL) management, assignation of accountcode, also basic CRUD functions on the CDR



Requirements
------------

- Django (Python based web-framework):
  
  .. warning::
    You must use Django version 1.3.

    2. Sqlite3 / Mysql
    3. Apache
    4. Python 2.6


Admin Panel
-----------

--------------
Administration
--------------

~~~~~~~~~~~
Auth System
~~~~~~~~~~~
Admin users & customer users

~~~
CDR
~~~


