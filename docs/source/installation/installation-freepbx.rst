Installing on FreePBX
=====================

CDR-Stats will be configured to attach to the asteriskcdrdb database in MySQL installed by the FreePBX installation routine, which contains all the call data records. A connector is installed that takes the CDR from MySQL and imports them into PostgreSQL in realtime. The web interface for CDR-Stats will be installed on port 8008 and the Websocket on port 9000, so it is neceesary to update the firewall settings to allow access to these ports

Before commencing, a back up of FreePBX, in particular asteriskcdrdb is recommended. Also have a note of the root password for MySQL.

Run the following commands at the console::

    $ wget –no-check-certificate https://raw.github.com/Star2Billing/cdr-stats/master/install/install-cdr-stats-asterisk.sh -O install-cdr-stats-asterisk.sh
    $ bash install-cdr-stats-asterisk.sh

The install routine will ask a number of questions, all of which are self explanatory. Select “Install all” which is option 1 in the CDR-Stats Installation Menu.