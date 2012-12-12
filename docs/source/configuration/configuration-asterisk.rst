.. _configuration-asterisk:

Asterisk Configuration.
=======================

Import configuration for Asterisk.
----------------------------------


The asterisk settings may be as follows::

    #list of CDR Backends to import
    CDR_BACKEND = {
        '127.0.0.1': {
            'db_engine': 'mysql',
            'cdr_type': 'asterisk',
            'db_name': 'asteriskcdrdb',
            'table_name': 'cdr',
            'host': 'localhost',
            'port': '',
            'user': 'root',
            'password': 'password',
        },
        #'192.168.1.200': {
            #'db_engine': 'mysql',
            #'cdr_type': 'asterisk',
            #'db_name': 'asteriskcdrdb',
            #'table_name': 'cdr',
            #'host': 'localhost',
            #'port': '',
            #'user': 'root',
            #'password': 'password',
        #},
    }

To add a new remote Asterisk MySQL CDR store,  ensure that there is a connection to the remote MySQL database, then uncomment the new server settings by removing the # and configuring the credentials to connect to the remote Asterisk CDR store.



.. _realtime-configuration-asterisk:

Realtime configuration for Asterisk.
====================================

The Asterisk Manager settings allow CDR-Stats to retrieve Realtime information to show the number of concurrent calls both in realtime and historically.

The settings to configure are::

    #Asterisk Manager / Used for Realtime and Concurrent calls
    ASTERISK_MANAGER_HOST = 'localhost'
    ASTERISK_MANAGER_USER = 'cdrstats_user'
    ASTERISK_MANAGER_SECRET = 'cdrstats_secret'


In Asterisk, add a new user in manager.conf, or one of its #include's for CDR-Stats. Further information about Asterisk Manager can be found here : http://www.voip-info.org/wiki/view/Asterisk+config+manager.conf

