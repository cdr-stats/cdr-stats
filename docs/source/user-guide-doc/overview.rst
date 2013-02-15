.. _cdr-stats-overview:

========
Overview
========

CDR-Stats is a web based application built on the Django framework, which uses MongoDB as the CDR
data stare, and uses MySQL, SQLite or Postgresql for Django framework management and user control.

Celery (http://celeryproject.org/) is an asynchronous task queue/job queue based on distributed message.
It is used to build our backend system to monitor CDR, detect unusual activity, and react by sending alert email.



**CDR Stats Management Features**
    
- Multi-tenant design that allows call detail records from multiple switches or PBX systems.
- Custom alarm triggers can be set to email the administrator for a range of conditions including unusual average call durations, failed calls, and unexpected destinations called.
- Graphical tools help detect unusual call patterns which may indicate suspicious or fraudulent activity.
- Import Call Detail Records in CSV format
- Configure Switches for import
- Create Customer and assign accountcode
- Configure alert to detect unsual increase/decrease of Traffic


**CDR Stats Customer Portal Features**

- Password management
- Call Details Record
- Monthly, Daily, Hourly Call reporting
- Impact Reporting
- Country Reporting
- Realtime Reporting of calls in progress
- View Fraudulent Calls
- Concurrent Call Statistic
- Configure Mail Reporting
- Top 10 destination Traffic
- Export to CSV
- Automated daily reporting.
