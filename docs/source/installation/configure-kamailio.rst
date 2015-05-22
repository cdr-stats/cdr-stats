
.. _configure-kamailio:

Configure Kamailio with CDR-Stats and CDR-Pusher
================================================

In Kamailio, you can store easily your CDR using Mysql, using the 'acc module'
(kamailio.org/docs/modules/4.0.x/modules/acc.html). You will need to configure
Kamailio to store CDRs to Mysql and afterwards you will have to install
CDR-Pusher on your Kamailio server to push those CDRs to the CDR-Stats server.


Collect CDRs from Kamailio MYSQL Database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Kamailio and module acc can help you storing your CDRs to a Mysql database.
Here you can find some of the SQL schema and procedure that will be needed to
achieve it http://siremis.asipto.com/install-accounting/

Simeris have some documentation on how to setup accounting services:
http://kb.asipto.com/siremis:install40x:accounting

You will end up with a Mysql cdr table similar to this one::

    CREATE TABLE `cdrs` (
      `cdr_id` bigint(20) NOT NULL AUTO_INCREMENT,
      `src_username` varchar(64) NOT NULL DEFAULT '',
      `src_domain` varchar(128) NOT NULL DEFAULT '',
      `dst_username` varchar(64) NOT NULL DEFAULT '',
      `dst_domain` varchar(128) NOT NULL DEFAULT '',
      `dst_ousername` varchar(64) NOT NULL DEFAULT '',
      `call_start_time` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
      `duration` int(10) unsigned NOT NULL DEFAULT '0',
      `sip_call_id` varchar(128) NOT NULL DEFAULT '',
      `sip_from_tag` varchar(128) NOT NULL DEFAULT '',
      `sip_to_tag` varchar(128) NOT NULL DEFAULT '',
      `src_ip` varchar(64) NOT NULL DEFAULT '',
      `cost` int(11) NOT NULL DEFAULT '0',
      `rated` int(11) NOT NULL DEFAULT '0',
      `created` datetime NOT NULL,
      PRIMARY KEY (`cdr_id`),
      UNIQUE KEY `uk_cft` (`sip_call_id`,`sip_from_tag`,`sip_to_tag`)
    ) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=latin1;

You will have to install the stored procedure 'kamailio_cdrs' &
'kamailio_rating' and call them from your Kamailio config.

In  order to register failed calls to missed_calls, you will need to set flag
'FLT_ACCFAILED' and 'FLT_ACCMISSED' as follow::

    if (is_method("INVITE"))
    {
    setflag(FLT_ACC); # do accounting
        setflag(FLT_ACCFAILED); # -- this is added to record failed calls
        setflag(FLT_ACCMISSED);
    }


Install Triggers to regroup CDRs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The triggers will push your new Kamailio CDRs to a new table `collection_cdrs`.
This table helps to merge both table entries 'cdr and 'missed_calls', that way
we could send the CDRs easily from CDR-Pusher application.


Connect to your Kamailio Mysql Database and create the following table and
triggers::

    DROP TABLE IF EXISTS `collection_cdrs`;

    CREATE TABLE `collection_cdrs` (
        `id` bigint(20) NOT NULL auto_increment,
        `cdr_id` bigint(20) NOT NULL default '0',
        `src_username` varchar(64) NOT NULL default '',
        `src_domain` varchar(128) NOT NULL default '',
        `dst_username` varchar(64) NOT NULL default '',
        `dst_domain` varchar(128) NOT NULL default '',
        `dst_ousername` varchar(64) NOT NULL default '',
        `call_start_time` datetime NOT NULL default '0000-00-00 00:00:00',
        `duration` int(10) unsigned NOT NULL default '0',
        `sip_call_id` varchar(128) NOT NULL default '',
        `sip_from_tag` varchar(128) NOT NULL default '',
        `sip_to_tag` varchar(128) NOT NULL default '',
        `src_ip` varchar(64) NOT NULL default '',
        `cost` integer NOT NULL default '0',
        `rated` integer NOT NULL default '0',
        `sip_code` char(3) NOT NULL default '',
        `sip_reason` varchar(32) NOT NULL default '',
        `created` datetime NOT NULL,
        `flag_imported` integer NOT NULL default '0',
        PRIMARY KEY  (`id`)
    );

    DELIMITER //
    CREATE TRIGGER copy_cdrs
    AFTER INSERT
        ON cdrs FOR EACH ROW
    BEGIN
        INSERT INTO collection_cdrs SET
            cdr_id = NEW.cdr_id,
            src_username = NEW.src_username,
            src_domain = NEW.src_domain,
            dst_username = NEW.dst_username,
            dst_domain = NEW.dst_domain,
            dst_ousername = NEW.dst_ousername,
            call_start_time = NEW.call_start_time,
            duration = NEW.duration,
            sip_call_id = NEW.sip_call_id,
            sip_from_tag = NEW.sip_from_tag,
            sip_to_tag = NEW.sip_to_tag,
            src_ip = NEW.src_ip,
            cost = NEW.cost,
            rated = NEW.rated,
            sip_code = 200,
            sip_reason = ''
            ;
    END; //
    DELIMITER ;

    DELIMITER //
    CREATE TRIGGER copy_missed_calls
    AFTER INSERT
        ON missed_calls FOR EACH ROW
    BEGIN
        INSERT INTO collection_cdrs SET
            cdr_id = NEW.cdr_id,
            src_username = NEW.src_user,
            src_domain = NEW.src_domain,
            dst_username = NEW.dst_user,
            dst_domain = NEW.dst_domain,
            dst_ousername = NEW.dst_ouser,
            call_start_time = NEW.time,
            duration = 0,
            sip_call_id = NEW.callid,
            sip_from_tag = NEW.from_tag,
            sip_to_tag = NEW.to_tag,
            src_ip = NEW.src_ip,
            cost = 0,
            rated = 0,
            sip_code = NEW.sip_code,
            sip_reason = NEW.sip_reason
            ;
    END; //
    DELIMITER ;


Import previous CDRs and Missed Calls
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you were already collecting CDRs in Kamailio, you may want to import
the existing ones to the table 'collection_cdrs', you can do the following
with those SQL commands::

    -- !!! Only do the following once !!!

    -- import cdrs
    INSERT collection_cdrs (cdr_id, src_username, src_domain, dst_username, dst_domain, dst_ousername, call_start_time, duration, sip_call_id, sip_from_tag, sip_to_tag, src_ip, cost, rated, sip_code, sip_reason) SELECT cdr_id, src_username, src_domain, dst_username, dst_domain, dst_ousername, call_start_time, duration, sip_call_id, sip_from_tag, sip_to_tag,  src_ip, cost, rated, 200, '' FROM cdrs;


    -- import missed_calls
    INSERT collection_cdrs (cdr_id, src_username, src_domain, dst_username, dst_domain, dst_ousername, call_start_time, duration, sip_call_id, sip_from_tag, sip_to_tag, src_ip, cost, rated, sip_code, sip_reason) SELECT cdr_id, src_user, src_domain, dst_user, dst_domain, dst_ouser, time, 0, callid, from_tag, to_tag,  src_ip, 0, 0, sip_code, sip_reason FROM missed_calls;


Install CDR-Pusher
~~~~~~~~~~~~~~~~~~

Once your CDRs will be stored to a Mysql Database, you will have to install
CDR-Pusher on your Kamailio server. You can find instruction how to install
CDR-Pusher here: https://github.com/areski/cdr-pusher

After installation of CDR-Pusher you can find the configuration file at
'/etc/cdr-pusher.yaml'. You will need to configure properly some settings in
order to connect CDR-pusher to your Mysql CDR backend and to your CDR-Stats
server.


Configure CDR-pusher to collect CDRs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here some of the settings you need to change to fetch CDR form Kamailio, edit
'/etc/cdr-pusher.yaml'::

    # storage_source_type: DB backend type where CDRs are stored
    # (accepted values: "sqlite3" and "mysql")
    storage_source: "mysql"

    # Database DNS
    db_dns: "username:password@/database"

    # db_table: the DB table name
    db_table: "collection_cdrs"

    # cdr_fields is list of fields that will be fetched (from SQLite3) and pushed (to PostgreSQL)
    # - if dest_field is callid, it will be used in riak as key to insert
    cdr_fields:
        - orig_field: sip_call_id
          dest_field: callid
          type_field: string
        - orig_field: src_username
          dest_field: caller_id_number
          type_field: string
        - orig_field: src_username
          dest_field: caller_id_name
          type_field: string
        - orig_field: dst_username
          dest_field: destination_number
          type_field: string
        - orig_field: "CASE sip_code WHEN '400' THEN 41 WHEN '401' THEN 21 WHEN '402' THEN 21 WHEN '403' THEN 21 WHEN '404' THEN 1 WHEN '486' THEN 17 WHEN '408' THEN 18 WHEN '480' THEN 19 WHEN '603' THEN 21 WHEN '410' THEN 22 WHEN '483' THEN 25 WHEN '502' THEN 27 WHEN '484' THEN 28 WHEN '501' THEN 29 WHEN '503' THEN 38 WHEN '488' THEN 65 WHEN '504' THEN 102 ELSE 41 END"
          dest_field: hangup_cause_id
          type_field: int
        - orig_field: CONVERT(duration,UNSIGNED INTEGER)
          dest_field: duration
          type_field: int
        - orig_field: CONVERT(duration,UNSIGNED INTEGER)
          dest_field: billsec
          type_field: int
        - orig_field: "call_start_time"
          dest_field: starting_date
          type_field: date


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
    cdr_source_type: 6


Restart CDR-Pusher
~~~~~~~~~~~~~~~~~~

After changes in '/etc/cdr-pusher.yaml' CDR-pusher will need to be restarted,
do this with the following command::

    /etc/init.d/supervisor stop
    /etc/init.d/supervisor start
