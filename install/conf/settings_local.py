#
# CDR-Stats License
# http://www.cdr-stats.org
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

import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

#TODO : Installation script should ask the timezone
TIME_ZONE = 'Europe/Madrid'

APPLICATION_DIR = os.path.dirname(globals()['__file__'])

#DATABASE SETTINGS
#=================
DATABASES = {
    'default': {
        # Add 'postgresql_psycopg2','postgresql','mysql','sqlite3','oracle'
        'ENGINE': 'django.db.backends.sqlite3',
        # Or path to database file if using sqlite3.
        'NAME': APPLICATION_DIR + '/database/cdr-stats.db',
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost.
                                         # Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default.
                                         # Not used with sqlite3.
        'OPTIONS': {
           'init_command': 'SET storage_engine=INNODB',
        }
    }
}


#CELERY SETTINGS
#===============
CARROT_BACKEND = 'redis'
BROKER_HOST = 'localhost'  # Maps to redis host.
BROKER_PORT = 6379         # Maps to redis port.
BROKER_VHOST = 0        # Maps to database number.

CELERY_RESULT_BACKEND = 'redis'
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
#REDIS_CONNECT_RETRY = True


#EMAIL BACKEND
#=============
# Use only in Debug mode. Not in production
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

#TASTYPIE
#========
API_ALLOWED_IP = ['127.0.0.1', 'localhost', ]

#SOCKETIO
#========
SOCKETIO_HOST = 'SERVER_IP'
SOCKETIO_PORT = 9000
SOCKETIO_CALLNUM_DEFAULT = 0

#GENERAL
#=======
PHONE_NO_PREFIX_LIMIT_MIN = 2
PHONE_NO_PREFIX_LIMIT_MAX = 5

#Realtime Graph : set the Y axis limit
REALTIME_Y_AXIS_LIMIT = 10

# freeswitch, asterisk : see support Switches
LOCAL_SWITCH_TYPE = 'freeswitch'
LOCAL_SWITCH_ID = 1


#MONGODB
#=======
CDR_MONGO_DB_NAME = 'freeswitch_cdr'
CDR_MONGO_HOST = 'localhost'
CDR_MONGO_PORT = 27017
CDR_MONGO_CDR_COMMON = 'cdr_common'
CDR_MONGO_CONC_CALL = 'concurrent_call'
CDR_MONGO_CDR_COUNTRY_REPORT = 'cdr_country_report'
CDR_MONGO_CONC_CALL_AGG = 'concurrent_call_map_reduce'
CDR_MONGO_CDR_MONTHLY = 'cdr_monthly_analytic'
CDR_MONGO_CDR_DAILY = 'cdr_daily_analytic'
CDR_MONGO_CDR_HOURLY = 'cdr_hourly_analytic'
CDR_MONGO_CDR_HANGUP = 'cdr_hangup_cause_analytic'
CDR_MONGO_CDR_COUNTRY = 'cdr_country_analytic'


#MongoDB(s) to use for import
CDR_MONGO_IMPORT = {
    '127.0.0.1': {
        'db_name': 'freeswitch_cdr',
        'host': 'localhost',
        'port': 27017,
        'collection': 'cdr',
    },
    #'192.168.1.15': {
    #    'db_name': 'freeswitch_cdr',
    #    'host': '192.168.1.15',
    #    'port': 27017,
    #    'collection': 'cdr',
    #},
}
