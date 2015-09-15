
.. _configure-asterisk:

Configure Asterisk with CDR-Stats and CDR-Pusher
================================================

Asterisk supports many backends to store CDRs: SQLite3, PostgreSQL, MySQL and
many more.

In this document, we will explain how to configure Asterisk to store CDRs to
SQLite3 or Mysql. Sqlite3 is the one we will recommend as this is by far the
easiest to setup). Finally we will explain how to install CDR-Pusher on your
Asterisk server to push CDRs to the CDR-Stats server.


Store Asterisk CDRs to SQLITE3
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The cdr_sqlite module was deprecated and has been removed. Users of this
module should use the cdr_sqlite3_custom module instead.

If Asterisk is compiled from source, then providing that SQLite3 is installed,
then during make menuselect under Call Detail Recording, cdr_sqlite3_custom
can be selected for installation.

For those using Asterisk via RPMs such as in the popular free PBX system, then
something like yum install asterisk11-sqlite3.x86_64. Do `yum search sqlite3`
to find the correct module for your version of Asterisk.

There is only one config file for the `cdr_sqlite3_custom.so` module, this is
configured at `/etc/asterisk/cdr_sqlite3_custom.conf` and the default settings
are as follows::

    ;
    ; Mappings for custom config file
    ;
    [master] ; currently, only file "master.db" is supported, with only one table at a time.
    table => cdr
    columns => calldate, clid, dcontext, channel, dstchannel, lastapp, lastdata,source, destination, duration, billsec, disposition, amaflags, accountcode, uniqueid, userfield, test
    values => '${CDR(start)}','${CDR(clid)}','${CDR(dcontext)}','${CDR(channel)}','${CDR(dstchannel)}','${CDR(lastapp)}','${CDR(lastdata)}','${CDR(src)}','${CDR(dst)}','${CDR(duration,f)}','${CDR(billsec,f)}','${CDR(disposition)}','${CDR(amaflags)}','${CDR(accountcode)}','${CDR(uniqueid)}','${CDR(userfield)}','${CDR(test)}'

After installation, restart asterisk. When CDR are written, they will be found
at `/var/log/asterisk/master.db`.

To check that CDR are being written to the SQLite3 DB with the following::

    $ sqlite3 /var/log/asterisk/master.db
    $ SELECT * FROM cdr LIMIT 10;


The result will be::

    SQLite version 3.6.20
    Enter ".help" for instructions
    Enter SQL statements terminated with a ";"
    sqlite>

    For readability, type
    .header on
    .mode column
    Then you can list your CDR with standard SQL commands, e.g.
    select * from cdr;

    CTRL-D exits the SQLite console


Store Asterisk CDRs to MySQL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There is only one config file for the `cdr_mysql.so` module, this is
configured at `/etc/asterisk/cdr_mysql.conf` and the default settings
are as follows::


    ;
    ; Note - if the database server is hosted on the same machine as the
    ; asterisk server, you can achieve a local Unix socket connection by
    ; setting hostname=localhost
    ;
    ; port and sock are both optional parameters. If hostname is specified
    ; and is not "localhost", then cdr_mysql will attempt to connect to the
    ; port specified or use the default port. If hostname is not specified
    ; or if hostname is "localhost", then cdr_mysql will attempt to connect
    ; to the socket file specified by sock or otherwise use the default socket
    ; file.
    ;
    [global]
    hostname=localhost
    dbname=asteriskcdrdb
    password=password
    user=asteriskcdruser
    table=cdr
    ;port=3306
    ;sock=/tmp/mysql.sock
    ;userfield=1


Enable the last option `userfield` if you wish to use SetCDRUserField.

Configure with your hostname, dbname, password, user and table.

After installation, restart asterisk.

To check that CDR are being written to the MySQL DB with the following::

    $ mysql -uasteriskcdruser -pasteriskcdrdb asteriskcdrdb
    $ SELECT * FROM cdr LIMIT 10;


The result will be::

    Reading table information for completion of table and column names
    You can turn off this feature to get a quicker startup with -A

    Welcome to the MySQL monitor.  Commands end with ; or \g.
    Your MySQL connection id is 4862
    Server version: 5.5.44-0ubuntu0.12.04.1 (Ubuntu)

    Copyright (c) 2000, 2015, Oracle and/or its affiliates. All rights reserved.

    Oracle is a registered trademark of Oracle Corporation and/or its
    affiliates. Other names may be trademarks of their respective
    owners.

    Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

    mysql> select * from cdr LIMIT 10;
    ...
    ...

    CTRL-D exits the MySQL console


Configure CDR-pusher to collect CDRs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once your CDRs will be stored to a SQLite Database, you will have to install
CDR-Pusher on your Asterisk server. You can find instruction how to install
CDR-Pusher here: https://github.com/cdr-stats/cdr-stats

To install Supervisor on CentOS 6 or RHEL6, the procedure is more complex,
here it's how we do it::

    $ yum -y install python-setuptools

    $ easy_install supervisor

    $ wget https://raw.githubusercontent.com/cdr-stats/cdr-stats/develop/install/supervisor/centos/supervisord.conf -O /etc/supervisord.conf

    $ wget https://raw.githubusercontent.com/cdr-stats/cdr-stats/develop/install/supervisor/centos/supervisord -O /etc/init.d/supervisor

    $ chmod +x /etc/init.d/supervisor

    $ supervisord --version

    $ /etc/init.d/supervisor stop ; sleep 2 ; /etc/init.d/supervisor start


Also make sure you have recent version of Git.

Check your git version with::

    git $ version


If your git version <= 1.7.4, then you will need to install a recent version,
you can follow the instructions here how to install a recent Git on CentOS6
here: http://tecadmin.net/how-to-upgrade-git-version-1-7-10-on-centos-6/

After installation of CDR-Pusher you can find the configuration file at
'/etc/cdr-pusher.yaml'. You will need to configure properly some settings in
order to connect CDR-pusher to your SQLite or MySQL CDR backend and to your
CDR-Stats server.


Configure CDR-Pusher for SQLite3
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here some of the settings you need to change to fetch SQLite CDR form Asterisk,
edit '/etc/cdr-pusher.yaml'::

    # storage_source_type: type to CDRs to push
    storage_source: "sqlite3"

    # db_file: specify the database path and name
    db_file: "/var/log/asterisk/master.db"

    # db_table: the DB table name
    db_table: "cdr"

    # cdr_fields is list of fields that will be fetched (from SQLite3) and pushed (to PostgreSQL)
    # - if dest_field is callid, it will be used in riak as key to insert
    cdr_fields:
        - orig_field: uniqueid
          dest_field: callid
          type_field: string
        - orig_field: "'' AS cidnum"
          dest_field: caller_id_number
          type_field: string
        - orig_field: clid
          dest_field: caller_id_name
          type_field: string
        - orig_field: destination
          dest_field: destination_number
          type_field: string
        - orig_field: "CASE WHEN disposition='ANSWER' THEN 16 WHEN disposition='ANSWERED' THEN 16 WHEN disposition='BUSY' THEN 17 WHEN disposition='NOANSWER' THEN 19 WHEN disposition='NO ANSWER' THEN 19 WHEN disposition='CANCEL' THEN 21 WHEN disposition='CANCELED' THEN 21 WHEN disposition='CONGESTION' THEN 34 WHEN disposition='CHANUNAVAIL' THEN 47 WHEN disposition='DONTCALL' THEN 21 WHEN disposition='TORTURE' THEN 21 WHEN disposition='INVALIDARGS' THEN 47 WHEN disposition='FAIL' THEN 41 WHEN disposition='FAILED' THEN 41 ELSE 41 END"
          dest_field: hangup_cause_id
          type_field: int
        - orig_field: CAST(duration AS INTEGER)
          dest_field: duration
          type_field: int
        - orig_field: CAST(billsec AS INTEGER)
          dest_field: billsec
          type_field: int
        - orig_field: "datetime(calldate)"
          dest_field: starting_date
          type_field: date
        - orig_field: accountcode
          dest_field: accountcode
          type_field: string
        - orig_field: channel
          dest_field: extradata
          type_field: jsonb
        - orig_field: lastapp
          dest_field: extradata
          type_field: jsonb
        - orig_field: dcontext
          dest_field: extradata
          type_field: jsonb


Configure CDR-Pusher for MySQL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here some of the settings you need to change to fetch MySQL CDR form Asterisk,
edit '/etc/cdr-pusher.yaml'::

    # storage_source_type: type to CDRs to push
    storage_source: "mysql"

    # db_file: specify the database path and name
    db_file: ""

    # Database DNS
    # Use this with MySQL
    db_dns: "username:password@/database"

    # db_table: the DB table name
    db_table: "cdr"

    # cdr_fields is list of fields that will be fetched and pushed (to PostgreSQL)
    # - if dest_field is callid, it will be used in riak as key to insert
    cdr_fields:
        - orig_field: uniqueid
          dest_field: callid
          type_field: string
        - orig_field: clid
          dest_field: caller_id_name
          type_field: string
        - orig_field: "'' AS cidnum"
          dest_field: caller_id_number
          type_field: string
        - orig_field: dst
          dest_field: destination_number
          type_field: string
        - orig_field: "CASE disposition WHEN 'ANSWER' THEN 16 WHEN 'ANSWERED' THEN 16 WHEN 'BUSY' THEN 17 WHEN 'NOANSWER' THEN 19 WHEN 'NO ANSWER' THEN 19 WHEN 'CANCEL' THEN 21 WHEN 'CANCELED' THEN 21 WHEN 'CONGESTION' THEN 34 WHEN 'CHANUNAVAIL' THEN 47 WHEN 'DONTCALL' THEN 21 WHEN 'TORTURE' THEN 21 WHEN 'INVALIDARGS' THEN 47 WHEN 'FAIL' THEN 41 WHEN 'FAILED' THEN 41 ELSE 41 END"
          dest_field: hangup_cause_id
          type_field: int
        - orig_field: duration
          dest_field: duration
          type_field: int
        - orig_field: billsec
          dest_field: billsec
          type_field: int
        - orig_field: accountcode
          dest_field: accountcode
          type_field: string
        - orig_field: calldate
          dest_field: starting_date
          type_field: date
        - orig_field: userfield
          dest_field: extradata
          type_field: jsonb
        - orig_field: dcontext
          dest_field: extradata
          type_field: jsonb
        - orig_field: channel
          dest_field: extradata
          type_field: jsonb
        - orig_field: lastapp
          dest_field: extradata
          type_field: jsonb
        - orig_field: lastdata
          dest_field: extradata
          type_field: jsonb


CDR-Pusher always needs a Primary Key to import CDRs, therefore if you use
MySQL, please ensure that you have a Primary Key in your `cdr` table as it
might not be the default case.

You can create a Primary Key with::

    ALTER TABLE cdr ADD COLUMN id int(10) UNSIGNED PRIMARY KEY AUTO_INCREMENT FIRST;


Send CDRs from backend to the CDR-Stats Core DB
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The application cdr-pusher will need your correct CDR-Stats server settings to
push CDRs properly to the core DB, you set this in '/etc/cdr-pusher.yaml' by
changing::

    pg_datasourcename: "user=postgres password=password host=localhost port=5432 dbname=cdr-pusher sslmode=disable"


Replace 'postgres', 'password' and 'localhost' by your CDR-Stats server
settings and make sure you configured Remote Access to PostgreSQL, this is
described in our documentation here :ref:`configure-postgresql-remote-access`.

You may want to properly configure these 2 settings also::

    # switch_ip: leave this empty to default to your external IP (accepted value: ""|"your IP")
    switch_ip: ""

    # cdr_source_type: write the id of the cdr sources type
    # (accepted value: unknown: 0, csv: 1, api: 2, freeswitch: 3, asterisk: 4, yate: 5, kamailio: 6, opensips: 7, sipwise: 8, veraz: 9)
    cdr_source_type: 4


Restart CDR-Pusher
~~~~~~~~~~~~~~~~~~

After changes in '/etc/cdr-pusher.yaml' CDR-pusher will need to be restarted,
do this with the following command::

    $ /etc/init.d/supervisor stop
    $ /etc/init.d/supervisor start
