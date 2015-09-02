
.. _cdr-pusher-installation:

CDR-Pusher Installation
-----------------------

CDR-Pusher is a Go Application that will push your CDRs (Call Detail Record) from your Telco Switch (Asterisk, FreeSWITCH or other supported switch http://www.cdr-stats.org/pricing/switch-connectors/) to the centralized PostgreSQL Database CDR-Pusher on the CDR-Stats server.rebo


3.1 Install / Run
~~~~~~~~~~~~~~~~~

Install Golang dependencies (Debian/Ubuntu)::

    $ apt-get -y install mercurial git bzr bison
    $ apt-get -y install bison


Install GVM to select which version of Golang you want to install::

    $ bash < <(curl -s -S -L https://raw.githubusercontent.com/moovweb/gvm/master/binscripts/gvm-installer)
    $ source /root/.gvm/scripts/gvm
    $ gvm install go1.4.2 --binary
    $ gvm use go1.4.2 --default


Make sure you are running by default Go version >= 1.4.2, check by typing the following::

    $ go version


To install and run the cdr-pusher application, follow these steps::

    $ mkdir /opt/app
    $ cd /opt/app
    $ git clone https://github.com/cdr-stats/cdr-pusher.git
    $ cd cdr-pusher
    $ export GOPATH=`pwd`
    $ make build
    $ ./bin/cdr-pusher


The config file cdr-pusher.yaml is installed at the following location: /etc/cdr-pusher.yaml


3.2 Configuration file
~~~~~~~~~~~~~~~~~~~~~~

Config file /etc/cdr-pusher.yaml::

    # CDR FETCHING - SOURCE
    # ---------------------

    # storage_source_type: DB backend type where CDRs are stored
    # (accepted values: "sqlite3" and "mysql")
    storage_source: "sqlite3"

    # db_file: specify the database path and name
    db_file: "/usr/local/freeswitch/cdr.db"

    # Database DNS
    # Use this with Mysql
    db_dns: ""

    # db_table: the DB table name
    db_table: "cdr"

    # db_flag_field defines the table field that will be added/used to track the import
    db_flag_field: "flag_imported"

    # max_fetch_batch: Max number of CDR to push in batch (value: 1-1000)
    max_fetch_batch: 100

    # heartbeat: Frequency of check for new CDRs in seconds
    heartbeat: 1

    # cdr_fields is list of fields that will be fetched (from SQLite3) and pushed (to PostgreSQL)
    # - if dest_field is callid, it will be used in riak as key to insert
    cdr_fields:
        - orig_field: uuid
          dest_field: callid
          type_field: string
        - orig_field: caller_id_name
          dest_field: caller_id_name
          type_field: string
        - orig_field: caller_id_number
          dest_field: caller_id_number
          type_field: string
        - orig_field: destination_number
          dest_field: destination_number
          type_field: string
        - orig_field: hangup_cause_q850
          dest_field: hangup_cause_id
          type_field: int
        - orig_field: duration
          dest_field: duration
          type_field: int
        - orig_field: billsec
          dest_field: billsec
          type_field: int
        # - orig_field: account_code
        #   dest_field: accountcode
        #   type_field: string
        - orig_field: "datetime(start_stamp)"
          dest_field: starting_date
          type_field: date
        # - orig_field: "strftime('%s', answer_stamp)" # convert to epoch
        - orig_field: "datetime(answer_stamp)"
          dest_field: extradata
          type_field: jsonb
        - orig_field: "datetime(end_stamp)"
          dest_field: extradata
          type_field: jsonb

    # CDR PUSHING - DESTINATION
    # -------------------------

    # storage_dest_type defines where push the CDRs (accepted values: "postgres" or "riak")
    storage_destination: "postgres"

    # Used when storage_dest_type = postgres
    # datasourcename: connect string to connect to PostgreSQL used by sql.Open
    pg_datasourcename: "user=postgres password=password host=localhost port=5432 dbname=cdr-pusher sslmode=disable"

    # Used when storage_dest_type = postgres
    # pg_store_table: the DB table name to store CDRs in Postgres
    table_destination: "cdr_import"

    # Used when storage_dest_type = riak
    # riak_connect: connect string to connect to Riak used by riak.ConnectClient
    riak_connect: "127.0.0.1:8087"

    # Used when storage_dest_type = postgres
    # riak_bucket: the bucket name to store CDRs in Riak
    riak_bucket: "cdr_import"

    # switch_ip: leave this empty to default to your external IP (accepted value: ""|"your IP")
    switch_ip: ""

    # cdr_source_type: write the id of the cdr sources type
    # (accepted value: unknown: 0, csv: 1, api: 2, freeswitch: 3, asterisk: 4, yate: 5, kamailio: 6, opensips: 7, sipwise: 8, veraz: 9)
    cdr_source_type: 0

    # SETTINGS FOR FAKE GENERATOR
    # ---------------------------

    # fake_cdr will populate the SQLite database with fake CDRs for testing purposes (accepted value: "yes|no")
    fake_cdr: "no"

    # fake_amount_cdr is the number of CDRs to generate into the SQLite database for testing (value: 1-1000)
    # this amount of CDRs will be created every second
    fake_amount_cdr: 1000


3.3 Deployment
~~~~~~~~~~~~~~

CDR-Pusher application aims to be run as Service, it can easily be run by Supervisord.


3.3.1 Install Supervisord
*************************

Some Linux distributions offer a version of Supervisor that is installable through the system package manager. These packages may include distribution-specific changes to Supervisor::

    $ apt-get install supervisor


3.3.2 Configure CDR-Pusher with Supervisord
*******************************************

Create an Supervisor conf file for cdr-pusher::

    $ vim /etc/supervisor/conf.d/cdr-pusher-prog.conf


A supervisor configuration could look as follow::

    [program:cdr-pusher]
    autostart=true
    autorestart=true
    startretries=10
    startsecs = 5
    directory = /opt/app/cdr-pusher/bin
    command = /opt/app/cdr-pusher/bin/cdr-pusher
    user = root
    redirect_stderr = true
    stdout_logfile = /var/log/cdr-pusher/cdr-pusher.log
    stdout_logfile_maxbytes=50MB
    stdout_logfile_backups=10


Make sure the director to store the logs is created, in this case you should create '/var/log/cdr-pusher'::

    $ mkdir /var/log/cdr-pusher


3.3.4 Supervisord Manage
************************

Supervisord provides 2 commands, supervisord and supervisorctl::

    supervisord: Initialize Supervisord, run configed processes
    supervisorctl stop programX: Stop process programX. programX is config name in [program:mypkg].
    supervisorctl start programX: Run the process.
    supervisorctl restart programX: Restart the process.
    supervisorctl stop groupworker: Restart all processes in group groupworker
    supervisorctl stop all: Stop all processes. Notes: start, restart and stop won't reload the latest configs.
    supervisorctl reload: Reload the latest configs.
    supervisorctl update: Reload all the processes where the config has changed.


3.3.5 Supervisord Service
*************************

You can also use supervisor using the supervisor service::

    $ /etc/init.d/supervisor start



3.4 Configure CDR-Pusher
~~~~~~~~~~~~~~~~~~~~~~~~

Edit `/etc/cdr-pusher.yaml`

Get started by configuring the CDR source, this is your original CDR backend, for instance on Asterisk this can be MySQL, SQlite or Postgresql.

For Mysql & PostgreSQL you will need to configure the DNS too: https://github.com/go-sql-driver/mysql

Some of the settings to configure::

    # storage_source_type: DB backend type where CDRs are stored
    # (accepted values: "sqlite3" and "mysql")
    storage_source: "mysql"

    # Database DNS
    db_dns: "root:password@/accounting"


Then configure the 'CDR Pushing' section, here you will need to define where the CDRs will go, this will 'almost' always be the 'cdr-pusher' database living on your CDR-Stats server.

Check your CDR-Stats installation, you should find the Database settings for cdr-pusher database in settings_local.py

Some of the settings to configure::

    # storage_dest_type defines where push the CDRs (accepted values: "postgres", "riak" or "both")
    storage_destination: "postgres"

    # Used when storage_dest_type = postgres
    pg_datasourcename: "user=postgres password=password host=localhost port=5432 dbname=cdr-pusher sslmode=disable"


3.5 Configure your Switch CDR with CDR-Pusher
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You will need to configure CDR-Pusher and you Telco Switch to work together, for this we put some individual instructions for :

> Configure FreeSWITCH with CDR-Stats and CDR-Pusher - :ref:`configure-freeswitch`

> Configure Asterisk with CDR-Stats and CDR-Pusher - :ref:`configure-asterisk`

> Configure Kamailio with CDR-Stats and CDR-Pusher - :ref:`configure-kamailio`


3.6 Restart Supervisord
~~~~~~~~~~~~~~~~~~~~~~~

After changes in CDR-Pusher configuration you will need to restart supervisord,
you can do so with gently with::

    /etc/init.d/supervisor stop
    /etc/init.d/supervisor start


3.7 Troubleshooting
~~~~~~~~~~~~~~~~~~~

An easy way to verify that CDR-Stats is running smoothly is to look at the logs.

Find the import log activity on CDR-Stats at::

    tail -f  /var/log/cdr-stats/djcelery_error.log


Find the import log activity on CDR-Pusher at::

    tail -f /var/log/cdr-pusher/cdr-pusher.log


Check out the CDR-Stats Database 'import_cdr' to see realtime import::

    python manage.py dbshell --database=import_cdr
