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
from pymongo.connection import Connection
from pymongo.errors import ConnectionFailure
from cdr.models import Switch, CDR_TYPE
from cdr.functions_def import get_hangupcause_id
from cdr_alert.functions_blacklist import chk_destination
import datetime
import sys
import random

random.seed()


HANGUP_CAUSE = ['NORMAL_CLEARING', 'NORMAL_CLEARING', 'NORMAL_CLEARING',
                'NORMAL_CLEARING', 'USER_BUSY', 'NO_ANSWER', 'CALL_REJECTED',
                'INVALID_NUMBER_FORMAT']

# value 0 per default
# 1 in process of import, 2 imported successfully and verified
STATUS_SYNC = {"new": 0, "in_process": 1, "verified": 2}

# Assign collection names to variables
CDR_COMMON = settings.DBCON[settings.MONGO_CDRSTATS['CDR_COMMON']]
DAILY_ANALYTIC = settings.DBCON[settings.MONGO_CDRSTATS['DAILY_ANALYTIC']]
MONTHLY_ANALYTIC = settings.DBCON[settings.MONGO_CDRSTATS['MONTHLY_ANALYTIC']]


def print_shell(shell, message):
    if shell:
        print message


def set_int_default(val, default):
    """val if not int set default"""
    try:
        return int(val)
    except:
        return default


def get_element(cdr):
    """
    return some element from the cdr object
    """
    #Get accountcode
    if 'variables' in cdr and 'accountcode' in cdr['variables']:
        accountcode = cdr['variables']['accountcode']
    else:
        accountcode = ''
    #Get remote_media_ip
    if 'variables' in cdr and 'remote_media_ip' in cdr['variables']:
        remote_media_ip = cdr['variables']['remote_media_ip']
    else:
        remote_media_ip = ''
    #Get duration
    if 'variables' in cdr and 'duration' in cdr['variables'] \
       and cdr['variables']['duration']:
        duration = float(cdr['variables']['duration'])
    else:
        duration = 0
    #Get billsec
    if 'variables' in cdr and 'billsec' in cdr['variables'] \
       and cdr['variables']['billsec']:
        billsec = cdr['variables']['billsec']
    else:
        billsec = 0
    #Get direction
    if 'variables' in cdr and 'direction' in cdr['variables']:
        direction = cdr['variables']['direction']
    else:
        direction = 'unknown'
    #Get uuid
    if 'variables' in cdr and 'uuid' in cdr['variables']:
        uuid = cdr['variables']['uuid']
    else:
        uuid = ''
    #Get caller_id_number
    if 'callflow' in cdr and 'caller_profile' in cdr['callflow'][0] \
       and 'caller_id_number' in cdr['callflow'][0]['caller_profile']:
        caller_id_number = cdr['callflow'][0]['caller_profile']['caller_id_number']
    else:
        caller_id_number = ''
    #Get caller_id_name
    if 'callflow' in cdr and 'caller_profile' in cdr['callflow'][0] \
       and 'caller_id_name' in cdr['callflow'][0]['caller_profile']:
        caller_id_name = cdr['callflow'][0]['caller_profile']['caller_id_name']
    else:
        caller_id_name = ''
    # Get mduration
    if 'variables' in cdr and 'mduration' in cdr['variables']:
        mduration = cdr['variables']['mduration']
    else:
        mduration = ''
    # Get billmsec
    if 'variables' in cdr and 'billmsec' in cdr['variables']:
        billmsec = cdr['variables']['billmsec']
    else:
        billmsec = ''
    # Get read_codec
    if 'variables' in cdr and 'read_codec' in cdr['variables']:
        read_codec = cdr['variables']['read_codec']
    else:
        read_codec = ''
    # Get write_codec
    if 'variables' in cdr and 'write_codec' in cdr['variables']:
        write_codec = cdr['variables']['write_codec']
    else:
        write_codec = ''

    data_element = {
        'accountcode': accountcode,
        'remote_media_ip': remote_media_ip,
        'caller_id_number': caller_id_number,
        'caller_id_name': caller_id_name,
        'duration': duration,
        'billsec': billsec,
        'direction': direction,
        'uuid': uuid,
        'mduration': mduration,
        'billmsec': billmsec,
        'read_codec': read_codec,
        'write_codec': write_codec,
    }

    return data_element


def apply_index(shell):
    """Apply index on cdr-stats mongodb collections"""
    CDR_COMMON.ensure_index([
        ("start_uepoch", -1),
        ("caller_id_number", 1),
        ("destination_number", 1),
        ("duration", 1),
        ("billsec", 1),
        ("hangup_cause_id", 1)])
    DAILY_ANALYTIC.ensure_index([
        ("metadata.date", -1),
        ("metadata.switch_id", 1),
        ("metadata.country_id", 1),
        ("metadata.accountcode", 1)])
    MONTHLY_ANALYTIC.ensure_index([
        ("metadata.date", -1),
        ("metadata.switch_id", 1),
        ("metadata.country_id", 1),
        ("metadata.accountcode", 1)])

    print_shell(shell, "Index applied on collection")
    return True


def create_daily_analytic(daily_date, switch_id, country_id,
                          accountcode, hangup_cause_id, duration):
    """Create DAILY_ANALYTIC"""
    id_daily = daily_date.strftime('%Y%m%d') + "/%d/%s/%d/%d" % \
        (switch_id, accountcode, country_id, hangup_cause_id)
    hour = daily_date.hour
    minute = daily_date.minute
    # Get a datetime that only include date info
    d = datetime.datetime.combine(daily_date.date(), datetime.time.min)

    DAILY_ANALYTIC.update(
        {
            "_id": id_daily,
            "metadata": {
                "date": d,
                "switch_id": switch_id,
                "country_id": country_id,
                "accountcode": accountcode,
                "hangup_cause_id": hangup_cause_id,
            },
        },
        {
            "$inc": {
                "call_daily": 1,
                "call_hourly.%d" % (hour,): 1,
                "call_minute.%d.%d" % (hour, minute,): 1,
                "duration_daily": int(duration),
                "duration_hourly.%d" % (hour,): int(duration),
                "duration_minute.%d.%d" % (hour, minute,): int(duration),
            }
        }, upsert=True)

    return True


def create_monthly_analytic(daily_date, start_uepoch, switch_id,
                            country_id, accountcode, duration):
    """Create DAILY_ANALYTIC"""
    # Get a datetime that only include year-month info
    d = datetime.datetime.strptime(str(start_uepoch)[:7], "%Y-%m")

    id_monthly = daily_date.strftime('%Y%m') + "/%d/%s/%d" %\
        (switch_id, accountcode, country_id)

    MONTHLY_ANALYTIC.update(
        {
            "_id": id_monthly,
            "metadata": {
                "date": d,
                "switch_id": switch_id,
                "country_id": country_id,
                "accountcode": accountcode,
            },
        },
        {
            "$inc": {
                "call_monthly": 1,
                "duration_monthly": int(duration),
            }
        }, upsert=True)

    return True


def generate_global_cdr_record(switch_id, caller_id_number, caller_id_name, destination_number,
                               duration, billsec, hangup_cause_id, accountcode, direction,
                               uuid, remote_media_ip, start_uepoch, answer_uepoch, end_uepoch,
                               mduration, billmsec, read_codec, write_codec, cdr_type,
                               cdr_object_id, country_id, authorized):
    """
    Common function to create global cdr record
    """
    cdr_record = {
        'switch_id': switch_id,
        'caller_id_number': caller_id_number,
        'caller_id_name': caller_id_name,
        'destination_number': destination_number,
        'duration': duration,
        'billsec': billsec,
        'hangup_cause_id': hangup_cause_id,
        'accountcode': accountcode,
        'direction': direction,
        'uuid': uuid,
        'remote_media_ip': remote_media_ip,
        'start_uepoch': start_uepoch,
        'answer_uepoch': answer_uepoch,
        'end_uepoch': end_uepoch,
        'mduration': mduration,
        'billmsec': billmsec,
        'read_codec': read_codec,
        'write_codec': write_codec,
        'cdr_type': cdr_type,
        'cdr_object_id': cdr_object_id,
        'country_id': country_id,
        'authorized': authorized,
    }
    return cdr_record


def common_function_to_create_analytic(date_start_uepoch, start_uepoch, switch_id,
                                       country_id, accountcode, hangup_cause_id, duration):
    """
    Common function to create DAILY_ANALYTIC, MONTHLY_ANALYTIC
    """
    # DAILY_ANALYTIC
    daily_date = datetime.datetime.fromtimestamp(int(date_start_uepoch[:10]))

    # insert daily analytic record
    create_daily_analytic(daily_date, switch_id, country_id, accountcode,
        hangup_cause_id, duration)

    # MONTHLY_ANALYTIC
    # insert monthly analytic record
    create_monthly_analytic(daily_date, start_uepoch, switch_id, country_id,
        accountcode, duration)

    return True


def func_importcdr_aggregate(shell, importcdr_handler, switch, ipaddress):
    """
    function go through the current mongodb, then will
    - create CDR_COMMON
    - build the pre-aggregate
    """

    #We limit the import tasks to a maximum - 1000
    #This will reduce the speed but that s the only way to make sure
    #we dont have several time the same tasks running

    PAGE_SIZE = 1000
    count_import = 0
    local_count_import = 0

    #Store cdr in list to insert by bulk
    cdr_bulk_record = []

    result = importcdr_handler.find(
        {
            '$or': [{'import_cdr': {'$exists': False}},
                {'import_cdr': 0}]
        },
        {
            "callflow.caller_profile.caller_id_number": 1,
            "callflow.caller_profile.caller_id_name": 1,
            "callflow.caller_profile.destination_number": 1,
            "variables.duration": 1,
            "variables.billsec": 1,
            "variables.hangup_cause_q850": 1,
            "variables.accountcode": 1,
            "variables.direction": 1,
            "variables.uuid": 1,
            "variables.remote_media_ip": 1,
            "variables.start_uepoch": 1,
            "variables.answer_uepoch": 1,
            "variables.end_uepoch": 1,
            "variables.mduration": 1,
            "variables.billmsec": 1,
            "variables.read_codec": 1,
            "variables.write_codec": 1,
            "import_cdr_monthly": 1,
            "import_cdr_daily": 1,
            "import_cdr_hourly": 1,
        }).limit(PAGE_SIZE)

    #Retrieve FreeSWITCH CDRs
    for cdr in result:
        #find result so let's look later for more records
        start_uepoch = datetime.datetime.fromtimestamp(
            int(cdr['variables']['start_uepoch'][:10]))

        answer_uepoch = ''
        if cdr['variables']['answer_uepoch']:
            answer_uepoch = datetime.datetime.fromtimestamp(
                int(cdr['variables']['answer_uepoch'][:10]))

        end_uepoch = ''
        if cdr['variables']['end_uepoch']:
            end_uepoch = datetime.datetime.fromtimestamp(
                int(cdr['variables']['end_uepoch'][:10]))

        # Check Destination number
        print(cdr)
        destination_number = cdr['callflow'][0]['caller_profile']['destination_number']

        if len(destination_number) <= settings.INTERNAL_CALL:
            authorized = 1
            country_id = 999
        else:
            destination_data = chk_destination(destination_number)
            authorized = destination_data['authorized']
            country_id = destination_data['country_id']

        hangup_cause_id = get_hangupcause_id(cdr['variables']['hangup_cause_q850'])

        #Retrieve Element from CDR Object
        data_element = get_element(cdr)
        accountcode = data_element['accountcode']
        remote_media_ip = data_element['remote_media_ip']
        caller_id_number = data_element['caller_id_number']
        caller_id_name = data_element['caller_id_name']
        duration = data_element['duration']
        billsec = data_element['billsec']
        direction = data_element['direction']
        uuid = data_element['uuid']

        mduration = data_element['mduration']
        billmsec = data_element['billmsec']
        read_codec = data_element['read_codec']
        write_codec = data_element['write_codec']

        # Prepare global CDR
        cdr_record = generate_global_cdr_record(switch.id, caller_id_number,
            caller_id_name, destination_number, duration, billsec, hangup_cause_id,
            accountcode, direction, uuid, remote_media_ip, start_uepoch, answer_uepoch,
            end_uepoch, mduration, billmsec, read_codec, write_codec,
            CDR_TYPE["freeswitch"], cdr['_id'], country_id, authorized)

        # Append cdr to bulk_cdr list
        cdr_bulk_record.append(cdr_record)

        # Count CDR import
        count_import = count_import + 1
        local_count_import = local_count_import + 1

        # print_shell(shell, "Sync CDR (cid:%s, dest:%s, dur:%s, " \
        #             " hg:%s,country:%s, auth:%s, row_count:%s)" % (
        #             caller_id_number,
        #             destination_number,
        #             duration,
        #             cdr['variables']['hangup_cause_q850'],
        #             country_id,
        #             authorized,
        #             count_import))

        date_start_uepoch = cdr['variables']['start_uepoch'][:10]
        common_function_to_create_analytic(date_start_uepoch, start_uepoch, switch.id,
            country_id, accountcode, hangup_cause_id, duration)

        # Flag the CDR as imported
        importcdr_handler.update(
            {'_id': cdr['_id']},
            {
                '$set': {
                    'import_cdr': 1,
                }
            }
        )

    if local_count_import > 0:
        # Bulk cdr list insert into cdr_common
        CDR_COMMON.insert(cdr_bulk_record)
        # Reset counter to zero
        local_count_import = 0
        print_shell(shell, "Switch(%s) - currently imported CDRs:%d" %
            (ipaddress, count_import))

    print_shell(shell, "Import on Switch(%s) - Total Record(s) imported:%d" %
        (ipaddress, count_import))


def chk_ipaddress(ipaddress):
    """
    Check if IP address exists in our database
    """
    DEV_ADD_IP = False
    # uncomment this to import from a fake different IP / used for dev
    # DEV_ADD_IP = '127.0.0.2'

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

    data = {
        'ipaddress': ipaddress,
        'switch': switch
    }
    return data


def import_cdr_freeswitch_mongodb(shell=False):
    # Browse settings.CDR_BACKEND and for each IP check if the IP exist
    # in our Switch objects. If it does we will connect to that Database
    # and import the data as we do below

    print_shell(shell, "Starting the synchronization...")

    #loop within the Mongo CDR Import List
    for ipaddress in settings.CDR_BACKEND:

        #Connect to Database
        db_name = settings.CDR_BACKEND[ipaddress]['db_name']
        table_name = settings.CDR_BACKEND[ipaddress]['table_name']
        db_engine = settings.CDR_BACKEND[ipaddress]['db_engine']
        cdr_type = settings.CDR_BACKEND[ipaddress]['cdr_type']
        host = settings.CDR_BACKEND[ipaddress]['host']
        port = settings.CDR_BACKEND[ipaddress]['port']
        user = settings.CDR_BACKEND[ipaddress]['user']
        password = settings.CDR_BACKEND[ipaddress]['password']

        if db_engine != 'mongodb' or cdr_type != 'freeswitch':
            sys.stderr.write('This function is intended for mongodb and freeswitch')
            sys.exit(1)

        data = chk_ipaddress(ipaddress)
        ipaddress = data['ipaddress']
        switch = data['switch']

        #Connect on MongoDB Database
        try:
            connection = Connection(host, port)
            DBCON = connection[db_name]
            DBCON.autentificate(user, password)
        except ConnectionFailure, e:
            sys.stderr.write("Could not connect to MongoDB: %s - %s" %
                (e, ipaddress))
            sys.exit(1)

        #Connect to Mongo
        importcdr_handler = DBCON[table_name]

        #Start import for this mongoDB
        func_importcdr_aggregate(shell, importcdr_handler, switch, ipaddress)
