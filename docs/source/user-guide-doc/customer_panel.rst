.. _customer-panel:

==============
Customer Panel
==============

User Interface :

This application provides a user interface...

http://localhost:8000/



.. contents::
    :local:
    :depth: 1

.. _customer-screenshot-features:

Screenshot with Features
========================

Index
~~~~~

Index page for the customer interface after successful login with user credentials

.. image:: ../_static/images/customer/index.png
    :width: 1000

Dashboard
~~~~~~~~~

The dashboard displays a graphical representation of the last 24 hours calls, call status statistics
and calls by country, either agregrated for all switches, or selectable by switch.

**URL**:

    * http://localhost:8000/dashboard/


.. image:: ../_static/images/customer/dashboard.png
    :width: 1000

CDR-View
~~~~~~~~

Call detail records listed in table format which can be exported to CSV file. 

Advanced Search allows further filtering and searching on a range of criteria

The Report by Day shows a graphical illustration of the calls, minutes and average call time.

**URL**:

    * http://localhost:8000/cdr_view/

.. image:: ../_static/images/customer/cdr_view_I.png
    :width: 1000


.. image:: ../_static/images/customer/cdr_view_II.png
    :width: 1000

CDR-Overview
~~~~~~~~~~~~

In this view, you can get pictorial view of calls with call-count or call-duration
from any date or date-range

**URL**:

    * http://localhost:8000/cdr_overview/


.. image:: ../_static/images/customer/cdr_overview.png
    :width: 1000


CDR-Hourly-Report
~~~~~~~~~~~~~~~~~

In this view, you can get hourly pictorial view of calls with call-count & call-duration.
You can compare different dates

**URL**:

    * http://localhost:8000/hourly_report/

.. image:: ../_static/images/customer/call_compare.png
    :width: 1000


CDR-Global-Report
~~~~~~~~~~~~~~~~~

In this view, you can get pictorial view of all calls

**URL**:

    * http://localhost:8000/global_report/

.. image:: ../_static/images/customer/global_report.png
    :width: 1000


CDR-Country-Report
~~~~~~~~~~~~~~~~~~

In this view, you can get pictorial view of all calls by country. Also
you can have 10 most called countries name with pie chart

**URL**:

    * http://localhost:8000/country_report/


.. image:: ../_static/images/customer/country_report.png
    :width: 1000

Mail-Report
~~~~~~~~~~~

In this view, there is a list of the last 10 calls of the previous day, along with total calls, a
breakdown of the call status, and the top 5 countries called.

**URL**:

    * http://localhost:8000/mail_report/

.. image:: ../_static/images/customer/mail_report.png
    :width: 1000

Concurrent-call-report
~~~~~~~~~~~~~~~~~~~~~~

In this view, you can get report of concurrent calls

**URL**:

    * http://localhost:8000/cdr_concurrent_calls/

.. image:: ../_static/images/customer/concurrent_call.png
    :width: 1000


Realtime-Report
~~~~~~~~~~~~~~~

This view provides realtime monitoring of the traffic on the connected telecoms servers. 
Currently, only Freeswitch is supported.

**URL**:

    * http://localhost:8000/cdr_realtime/

.. image:: ../_static/images/customer/realtime.png
    :width: 1000

