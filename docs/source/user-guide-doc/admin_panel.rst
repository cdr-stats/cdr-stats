.. _admin-panel:

===========
Admin Panel
===========

http://localhost:8000/admin/

The Admin section allows you to create administrators who have access the admin screens. Levels of
access can be set.

.. contents::
    :local:
    :depth: 1

.. _admin-screenshot-features:

Screenshot with Features
========================

Dashboard
~~~~~~~~~

Dashboard page for the admin interface after successful login with superuser credentials

.. image:: ../_static/images/admin/admin_dashboard.png    


Alarm
~~~~~

The alarm list will be displayed from the following URL. You can add a new
alarm by clicking ``Add alarm`` and adding the name of the alarm and its
description, Also from the alarm list, click on the alarm that you want
to update.

**URL**:

    * http://localhost:8000/admin/cdr_alert/alarm/

.. image:: ../_static/images/admin/alarm_list.png


To Add/Update alarm

**URL**:

    * http://localhost:8000/admin/cdr_alert/alarm/add/
    * http://localhost:8000/admin/cdr_alert/alarm/1/

.. image:: ../_static/images/admin/add_alarm.png


Alarm-report
~~~~~~~~~~~~

The alarmreport will be displayed from the following URL.

**URL**:

    * http://localhost:8000/admin/cdr_alert/alarmreport/

.. image:: ../_static/images/admin/alarm_report_list.png

To Add/Update alarmreport

**URL**:

    * http://localhost:8000/admin/cdr_alert/alarmreport/add/
    * http://localhost:8000/admin/cdr_alert/alarmreport/1/

.. image:: ../_static/images/admin/alarm_report.png


Blacklist
~~~~~~~~~

The blacklist will be displayed from the following URL. You can add a new
blacklist by clicking ``Blacklist by country`` and selecting the country name and its
prefixes, Also from the blacklist, click on the blacklist that you want
to update.

**URL**:

    * http://localhost:8000/admin/cdr_alert/blacklist/

.. image:: ../_static/images/admin/blacklist_prefix_list.png
    

.. image:: ../_static/images/admin/add_prefix_into_blacklist.png


Whitelist
~~~~~~~~~

The whitelist will be displayed from the following URL. You can add a new
Whitelist by clicking ``Whitelist by country`` and selecting the country name and its
prefixes, Also from the whitelist, click on the blacklist that you want
to update.

**URL**:

    * http://localhost:8000/admin/cdr_alert/whitelist/

.. image:: ../_static/images/admin/whitelist_prefix_list.png
    


.. image:: ../_static/images/admin/add_prefix_into_whitelist.png


Alert-remove-prefix
~~~~~~~~~~~~~~~~~~~

The alert remove prefix will be displayed from the following URL. You can add a new
remove prefix by clicking ``Add alert remove prefix`` and selecting the remove prefix,
Also from the alert remove prefix, click on the remove prefix that you want to update.


**URL**:

    * http://localhost:8000/admin/cdr_alert/alertremoveprefix/

.. image:: ../_static/images/admin/alert_remove_prefix_list.png
    

To Add/Update alert-remove prefix

**URL**:

    * http://localhost:8000/admin/cdr_alert/alertremoveprefix/add/
    * http://localhost:8000/admin/cdr_alert/alertremoveprefix/1/

.. image:: ../_static/images/admin/add_alert_remove_prefix.png
    

Switch
~~~~~~

**URL**:

    * http://localhost:8000/admin/cdr/switch/

.. image:: ../_static/images/admin/switch_list.png
    

HangupCause
~~~~~~~~~~~

**URL**:

    * http://localhost:8000/admin/cdr/hangupcause/

.. image:: ../_static/images/admin/hangup_cause_list.png
    


CDR View
~~~~~~~~

**URL**:

    * http://localhost:8000/admin/cdr/switch/cdr_view/

.. image:: ../_static/images/admin/admin_cdr_view.png
    