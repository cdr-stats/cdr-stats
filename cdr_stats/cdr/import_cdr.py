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
from django.conf import settings
from django.utils.translation import gettext as _

from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe

from pymongo.connection import Connection
from pymongo.errors import ConnectionFailure

from cdr.models import Switch, HangupCause
from cdr.functions_def import *
from cdr_alert.functions_blacklist import *
from country_dialcode.models import Prefix
from random import choice
from uuid import uuid1
from datetime import *
import calendar
import time
import sys
import random
import json, ast
import re

random.seed()

HANGUP_CAUSE = ['NORMAL_CLEARING','NORMAL_CLEARING','NORMAL_CLEARING','NORMAL_CLEARING',
                'USER_BUSY', 'NO_ANSWER', 'CALL_REJECTED', 'INVALID_NUMBER_FORMAT']

CDR_TYPE = {"freeswitch":1, "asterisk":2, "yate":3, "opensips":4, "kamailio":5}

#value 0 per default, 1 in process of import, 2 imported successfully and verified
STATUS_SYNC = {"new":0, "in_process": 1, "verified":2}

# Assign collection names to variables
CDR_COMMON = settings.DB_CONNECTION[settings.CDR_MONGO_CDR_COMMON]
CDR_MONTHLY = settings.DB_CONNECTION[settings.CDR_MONGO_CDR_MONTHLY]
CDR_DAILY = settings.DB_CONNECTION[settings.CDR_MONGO_CDR_DAILY]
CDR_HOURLY = settings.DB_CONNECTION[settings.CDR_MONGO_CDR_HOURLY]
CDR_COUNTRY_REPORT = settings.DB_CONNECTION[settings.CDR_MONGO_CDR_COUNTRY_REPORT]


def update_cdr_collection(mongohandler, cdr_id, field_name):
    # change import_cdr_xxxx flag in cdr_common collection
    mongohandler.update(
                {'_id': cdr_id},
                {'$set': {field_name: 1}}
    )
    return True


def remove_prefix(phonenumber, removeprefix_list):
    # remove the prefix from phone number
    # @ removeprefix_list "+,0,00,000,0000,00000,011,55555,99999"
    #
    #clean : remove spaces
    removeprefix_list = removeprefix_list.strip(' \t\n\r')
    if removeprefix_list and len(removeprefix_list) > 0:
        for rprefix in removeprefix_list.split(","):
            rprefix = rprefix.strip(' \t\n\r')
            rprefix = re.sub("\+", "\\\+", rprefix)
            if rprefix and len(rprefix)>0:
                phonenumber = re.sub("^%s" % rprefix, "", phonenumber)
    return phonenumber


def print_shell(shell, message):
    if shell:
        print message


def import_cdr(shell=False):
    #TODO : dont use the args here
    # Browse settings.CDR_MONGO_IMPORT and for each IP check if the IP exist in our Switch objects
    # If it does we will connect to that Database and import the data as we do below

    print_shell(shell, "Starting the synchronization...")

    #loop within the Mongo CDR Import List
    for ipaddress in settings.CDR_MONGO_IMPORT:
        #Select the Switch ID
        print_shell(shell, "Switch : %s" % ipaddress)

        DEV_ADD_IP = False
        #uncomment this if you need to import from a fake different IP / used for dev
        #DEV_ADD_IP = '127.0.0.2'

        if DEV_ADD_IP:
            previous_ip = ipaddress
            ipaddress = DEV_ADD_IP
        try:
            switch = Switch.objects.get(ipaddress=ipaddress)
        except Switch.DoesNotExist:
            switch = Switch(name=ipaddress, ipaddress=ipaddress)
            switch.save()

        if not switch.id:
            print "Error when adding new Switch!"
            raise SystemExit

        if DEV_ADD_IP:
            ipaddress = previous_ip

        #Connect on MongoDB Database
        host = settings.CDR_MONGO_IMPORT[ipaddress]['host']
        port = settings.CDR_MONGO_IMPORT[ipaddress]['port']
        db_name = settings.CDR_MONGO_IMPORT[ipaddress]['db_name']
        try:
            connection = Connection(host, port)
            DB_CONNECTION = connection[db_name]
        except ConnectionFailure, e:
            sys.stderr.write("Could not connect to MongoDB: %s - %s" % \
                                                            (e, ipaddress))
            sys.exit(1)

        #Connect to Mongo
        importcdr_handler = DB_CONNECTION[settings.CDR_MONGO_IMPORT[ipaddress]['collection']]

        total_record = importcdr_handler.find({'import_cdr': {'$exists': False}}).count()
        #print total_record

        PAGE_SIZE = int(5000)

        total_loop_count = int( int(total_record) / PAGE_SIZE ) + 1
        #print total_loop_count
        count_import = 0

        for j in range(1, total_loop_count+1):
            PAGE_NUMBER = int(j)
            
            result = importcdr_handler.find({'import_cdr': {'$exists': False}}, 
                    {
                        "callflow.caller_profile.caller_id_number":1,
                        "callflow.caller_profile.caller_id_name":1,
                        "callflow.caller_profile.destination_number": 1,
                        "variables.duration":1,
                        "variables.billsec":1,
                        "variables.hangup_cause_q850":1,
                        "variables.accountcode":1,
                        "variables.direction":1,
                        "variables.uuid":1,
                        "variables.remote_media_ip":1,
                        "variables.start_uepoch":1,
                        "variables.answer_uepoch":1,
                        "variables.end_uepoch":1,
                        "variables.mduration": 1,
                        "variables.billmsec":1,
                        "variables.read_codec": 1,
                        "variables.write_codec": 1,
                        "import_cdr_monthly": 1,
                        "import_cdr_daily": 1,
                        "import_cdr_hourly": 1,
                    }).sort([
                        ('variables.start_uepoch', -1),
                        ('callflow.caller_profile.destination_number', 1),
                        ('variables.accountcode', 1),
                        ('variables.hangup_cause_q850', 1)
                           ]).limit(PAGE_SIZE)

            #Retrieve FreeSWITCH CDRs
            for cdr in result:
                start_uepoch = datetime.fromtimestamp(int(cdr['variables']['start_uepoch'][:10]))
                answer_uepoch = datetime.fromtimestamp(int(cdr['variables']['answer_uepoch'][:10]))
                end_uepoch = datetime.fromtimestamp(int(cdr['variables']['end_uepoch'][:10]))

                # Check Destination number
                destination_number = cdr['callflow']['caller_profile']['destination_number']

                #remove prefix
                sanitized_destination = remove_prefix(destination_number, settings.PREFIX_TO_IGNORE)

                prefix_list = prefix_list_string(sanitized_destination)

                authorized = 1 # default
                #check desti against whiltelist
                authorized = chk_prefix_in_whitelist(prefix_list)
                if authorized:
                    # allowed destination
                    authorized = 1
                else:
                    #check against blacklist
                    authorized = chk_prefix_in_blacklist(prefix_list)
                    if not authorized:
                        # not allowed destination
                        authorized = 0

                print sanitized_destination
                if len(sanitized_destination) < settings.PHONENUMBER_MIN_DIGITS:
                    #It might be an extension
                    country_id = 0
                elif len(sanitized_destination) >= settings.PHONENUMBER_MIN_DIGITS \
                    and len(sanitized_destination) <= settings.PHONENUMBER_MAX_DIGITS:
                    #It might be an local call
                    print settings.LOCAL_DIALCODE
                    #Need to add coma for get_country_id to eval correctly
                    country_id = get_country_id(str(settings.LOCAL_DIALCODE) + ',')
                else:
                    #International call
                    country_id = get_country_id(prefix_list)

                if get_country_id==0:
                    #TODO: Add logger
                    print_shell(shell, "Error to find the country_id %s" % destination_number)

                destination_number = cdr['callflow']['caller_profile']['destination_number']
                hangup_cause_id = get_hangupcause_id(cdr['variables']['hangup_cause_q850'])
                try:
                    accountcode = cdr['variables']['accountcode']
                except:
                    accountcode = ''

                # Prepare global CDR
                cdr_record = {
                    'switch_id': switch.id,
                    'caller_id_number': cdr['callflow']['caller_profile']['caller_id_number'],
                    'caller_id_name': cdr['callflow']['caller_profile']['caller_id_name'],
                    'destination_number': destination_number,
                    'duration': int(cdr['variables']['duration']),
                    'billsec': int(cdr['variables']['billsec']),
                    'hangup_cause_id': hangup_cause_id,
                    'accountcode': accountcode,
                    'direction': cdr['variables']['direction'],
                    'uuid': cdr['variables']['uuid'],
                    'remote_media_ip': cdr['variables']['remote_media_ip'],
                    'start_uepoch': start_uepoch,
                    'answer_uepoch': answer_uepoch,
                    'end_uepoch': end_uepoch,
                    'mduration': cdr['variables']['mduration'],
                    'billmsec': cdr['variables']['billmsec'],
                    'read_codec': cdr['variables']['read_codec'],
                    'write_codec': cdr['variables']['write_codec'],
                    'cdr_type': CDR_TYPE["freeswitch"],
                    'cdr_object_id': cdr['_id'],
                    'country_id': country_id,
                    'authorized': authorized,
                }

                # record global CDR
                CDR_COMMON.insert(cdr_record)

                print_shell(shell, "Sync CDR (cid:%s, dest:%s, dur:%s, hg:%s, country:%s, auth:%s)" % (
                                            cdr['callflow']['caller_profile']['caller_id_number'],
                                            cdr['callflow']['caller_profile']['destination_number'],
                                            cdr['variables']['duration'],
                                            cdr['variables']['hangup_cause_q850'],
                                            country_id,
                                            authorized,))
                count_import = count_import + 1

                # change import_cdr flag
                #update_cdr_collection(importcdr_handler, cdr['_id'], 'import_cdr')
                
                # Store monthly cdr collection with unique import
                if not hasattr(cdr, 'import_cdr_monthly') or cdr['import_cdr_monthly'] == 0:
                    # monthly collection
                    current_y_m = datetime.strptime(str(start_uepoch)[:7], "%Y-%m")
                    CDR_MONTHLY.update(
                                {
                                    'start_uepoch': current_y_m,
                                    'destination_number': destination_number,
                                    'hangup_cause_id': hangup_cause_id,
                                    'accountcode': accountcode,
                                    'switch_id': switch.id,
                                },
                                {
                                    '$inc':
                                        {'calls': 1,
                                         'duration': int(cdr['variables']['duration']) }
                                }, upsert=True)

                # Store daily cdr collection with unique import
                if not hasattr(cdr, 'import_cdr_daily') or cdr['import_cdr_daily'] == 0:
                    # daily collection
                    current_y_m_d = datetime.strptime(str(start_uepoch)[:10], "%Y-%m-%d")
                    CDR_DAILY.update(
                            {
                                'start_uepoch': current_y_m_d,
                                'destination_number': destination_number,
                                'hangup_cause_id': hangup_cause_id,
                                'accountcode': accountcode,
                                'switch_id': switch.id,
                            },
                            {
                                '$inc':
                                    {'calls': 1,
                                     'duration': int(cdr['variables']['duration']) }
                            },upsert=True)

                # Store hourly cdr collection with unique import
                if not hasattr(cdr, 'import_cdr_hourly') or cdr['import_cdr_hourly'] == 0:
                    # hourly collection
                    current_y_m_d_h = datetime.strptime(str(start_uepoch)[:13], "%Y-%m-%d %H")
                    CDR_HOURLY.update(
                                {
                                    'start_uepoch': current_y_m_d_h,
                                    'destination_number': destination_number,
                                    'hangup_cause_id': hangup_cause_id,
                                    'accountcode': accountcode,
                                    'switch_id': switch.id,},
                                {
                                    '$inc': {'calls': 1,
                                             'duration': int(cdr['variables']['duration']) }
                                },upsert=True)

                    # Country report collection
                    current_y_m_d_h_m = datetime.strptime(str(start_uepoch)[:16], "%Y-%m-%d %H:%M")
                    CDR_COUNTRY_REPORT.update(
                                        {
                                            'start_uepoch': current_y_m_d_h_m,
                                            'country_id': country_id,
                                            'accountcode': accountcode,
                                            'switch_id': switch.id,},
                                        {
                                            '$inc': {'calls': 1,
                                                     'duration': int(cdr['variables']['duration']) }
                                        },upsert=True)

                # Flag the CDR as imported
                importcdr_handler.update(
                            {'_id': cdr['_id']},
                            {'$set': {'import_cdr': 1, 'import_cdr_monthly': 1, 'import_cdr_daily': 1, 'import_cdr_hourly': 1}}
                )

        if count_import > 0:
            # Apply index
            CDR_COMMON.ensure_index([("start_uepoch", -1)])
            CDR_MONTHLY.ensure_index([("start_uepoch", -1)])
            CDR_DAILY.ensure_index([("start_uepoch", -1)])
            CDR_HOURLY.ensure_index([("start_uepoch", -1)])
            CDR_COUNTRY_REPORT.ensure_index([("start_uepoch", -1)])

        print_shell(shell, "Import on Switch(%s) - Record(s) imported:%d" % (ipaddress, count_import))