#
# Newfies-Dialer License
# http://www.newfies-dialer.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2012 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#


#IMPORT SETTINGS
#===============
from settings import *

SOUTH_TESTS_MIGRATE = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

#Celery test
BROKER_BACKEND = "memory"
CELERY_ALWAYS_EAGER = True


#LOGGING
#=======
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
}

INSTALLED_APPS += ('django_nose', )
TEST_RUNNER = 'django_nose.run_tests'


#SOCKETIO
#========
SOCKETIO_HOST = 'localhost'
SOCKETIO_PORT = 9000
SOCKETIO_CALLNUM_DEFAULT = 100

#GENERAL
#=======
# PREFIX_LIMIT_MIN & PREFIX_LIMIT_MAX are used to know
# how many digits are used to match against the dialcode prefix database
PREFIX_LIMIT_MIN = 2
PREFIX_LIMIT_MAX = 5

# If PN is lower than PN_MIN_DIGITS it will be considered as an extension
# If PN is longer than PN_MIN_DIGITS but lower than PN_MAX_DIGITS then
# The PN will be considered as local call and the LOCAL_DIALCODE will be added
LOCAL_DIALCODE = 1  # Set the Dialcode of your country (44 for UK, 1 for US)
PN_MIN_DIGITS = 6
PN_MAX_DIGITS = 9

# List of phonenumber prefix to ignore, this will be remove prior analysis
PREFIX_TO_IGNORE = "+,0,00,000,0000,00000,011,55555,99999"

#Realtime Graph : set the Y axis limit
REALTIME_Y_AXIS_LIMIT = 300

#ASTERISK IMPORT
#===============
ASTERISK_PRIMARY_KEY = 'acctid'  # acctid, _id

#CDR_BACKEND
#===========
#list of CDR Backends to import
CDR_BACKEND = {
    '127.0.0.1': {
        'db_engine': 'mysql',  # mysql, pgsql, mongodb
        'cdr_type': 'asterisk',  # asterisk or freeswitch
        'db_name': 'asteriskcdr',
        'table_name': 'cdr',  # collection if mongodb
        'host': 'localhost',
        'port': 3306,  # 3306 mysql, 5432 pgsql, 27017 mongodb
        'user': 'root',
        'password': 'password',
    },
    # '127.0.0.1': {
    #     'db_engine': 'mongodb',  # mysql, pgsql, mongodb
    #     'cdr_type': 'freeswitch',  # asterisk or freeswitch
    #     'db_name': 'freeswitch_cdr',
    #     'table_name': 'cdr',  # collection if mongodb
    #     'host': 'localhost',
    #     'port': 27017,  # 3306 mysql, 5432 pgsql, 27017 mongodb
    #     'user': '',
    #     'password': '',
    # },
}

#Define the IP of your local Switch, it needs to exist in the CDR_BACKEND list
LOCAL_SWITCH_IP = '127.0.0.1'

#Asterisk Manager / Used for Realtime and Concurrent calls
ASTERISK_MANAGER_HOST = 'localhost'
ASTERISK_MANAGER_USER = 'user'
ASTERISK_MANAGER_SECRET = 'secret'
