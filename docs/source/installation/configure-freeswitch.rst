
.. _configure-freeswitch:

Configure FreeSWITCH with CDR-Stats and CDR-Pusher
==================================================

FreeSWITCH supports many backed to store CDRs, we will cover SQLite here.


Collect CDRs from SQLITE
~~~~~~~~~~~~~~~~~~~~~~~~

FreeSWITCH mod_cdr_sqlite is used to locally store the CDRs, to configure CDR
SQLite backend in FreeSWITCH you can find instruction here:
https://wiki.freeswitch.org/wiki/Mod_cdr_sqlite

Once your CDRs will be stored to a SQLite Database, you will have to install
CDR-Pusher on your FreeSWITCH server. You can find instruction how to install
CDR-Pusher here: https://github.com/areski/cdr-pusher

After installation of CDR-Pusher you can find the configuration file at
'/etc/cdr-pusher.yaml'. You will need to configure properly some settings in
order to connect CDR-pusher to your SQLite CDR backend and to your CDR-Stats
server.

By tweaking the configuration of Mod_cdr_sqlite and CDR-Pusher you can define
custom fields that you want to import to CDR-stats.

Here an example of 'cdr_sqlite.conf' that show how custom fields can be
defined to store some specific CDR variables to your CDR backend::

    <configuration name="cdr_sqlite.conf" description="SQLite CDR">
      <settings>
        <!-- SQLite database name (.db suffix will be automatically appended) -->
        <!-- <param name="db-name" value="cdr"/> -->
        <!-- CDR table name -->
        <!-- <param name="db-table" value="cdr"/> -->
        <!-- Log a-leg (a), b-leg (b) or both (ab) -->
        <param name="legs" value="a"/>
        <!-- Default template to use when inserting records -->
        <param name="default-template" value="example"/>
        <!-- This is like the info app but after the call is hung up -->
        <!--<param name="debug" value="true"/>-->
      </settings>
      <templates>
        <!-- Note that field order must match SQL table schema, otherwise insert will fail -->
        <template name="example">"${caller_id_name}","${caller_id_number}","${destination_number}","${context}","${start_stamp}","${answer_stamp}","${end_stamp}",${duration},${billsec},"${hangup_cause}", "${hangup_cause_q850}","${uuid}","${bleg_uuid}","${accountcode}"</template>
      </templates>
    </configuration>


Configure CDR-pusher to collect CDRs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here some of the settings you need to change to fetch CDR form Asterisk, edit
'/etc/cdr-pusher.yaml'::

    # storage_source_type: DB backend type where CDRs are stored
    # (accepted values: "sqlite3" and "mysql")
    storage_sourcestorage_source: "sqlite3"

    # db_file: specify the database path and name
    # db_file: "/usr/local/freeswitch/cdr.db"

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


Send CDRs from backend to the CDR-Stats Core DB
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The application cdr-pusher will need your correct CDR-Stats server settings to
push CDRs properly to the core DB, you set this in '/etc/cdr-pusher.yaml' by
changing::

    pg_datasourcename: "user=postgres password=password host=localhost port=5432 dbname=cdr-pusher sslmode=disable"


Replace 'postgres', 'password' and 'localhost' by your CDR-Stats server
settings and make sure you configured Remote Access to PostgreSQL, this is
described in our documentation here :ref:`configure-postgresql-remote-access`.

You may want to configure properly those 2 settings also::

    # switch_ip: leave this empty to default to your external IP (accepted value: ""|"your IP")
    switch_ip: ""

    # cdr_source_type: write the id of the cdr sources type
    # (accepted value: unknown: 0, csv: 1, api: 2, freeswitch: 3, asterisk: 4, yate: 5, kamailio: 6, opensips: 7, sipwise: 8, veraz: 9)
    cdr_source_type: 3


Restart CDR-Pusher
~~~~~~~~~~~~~~~~~~

After changes in '/etc/cdr-pusher.yaml' CDR-pusher will need to be restarted,
do this with the following command::

    $ /etc/init.d/supervisor stop
    $ /etc/init.d/supervisor start
