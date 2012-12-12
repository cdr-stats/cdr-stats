.. _configuration-freeswitch:

Import configuration for FreeSWITCH.
====================================

Freeswitch settings are under the CDR_BACKEND section, and should look as follows::

    CDR_BACKEND = {
        '127.0.0.1': {
            'db_engine': 'mongodb',  # mysql, pgsql, mongodb
            'cdr_type': 'freeswitch',  # asterisk or freeswitch
            'db_name': 'freeswitch_cdr',
            'table_name': 'cdr',  # collection if mongodb
            'host': 'localhost',
            'port': 3306,  # 3306 mysql, 5432 pgsql, 27017 mongodb
            'user': '',
            'password': '',
        },
        #'192.168.1.15': {
        #    'db_engine': 'mongodb',  # mysql, pgsql, mongodb
        #    'cdr_type': 'freeswitch',  # asterisk or freeswitch
        #    'db_name': 'freeswitch_cdr',
        #    'table_name': 'cdr',  # collection if mongodb
        #    'host': 'localhost',
        #    'port': 3306,  # 3306 mysql, 5432 pgsql, 27017 mongodb
        #    'user': '',
        #    'password': '',
        #},
    }


To connect a new Freeswitch system to CDR-Stats, ensure that port 27017 TCP is ONLY open to
the CDR-Stats server on the remote system, then uncomment the settings by removing the #,
and configure the IP address and db_name to match those in the mod_cdr_mongodb configuration
as described at :
http://www.cdr-stats.org/documentation/beginners-guide/howto-installing-on-freeswitch/


CDR-Stats can get CDR from both Freeswitch and Asterisk, or a combination of both.
