#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2014 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from django.conf import settings
from pymongo.connection import Connection
from pymongo.errors import ConnectionFailure
from cdr.models import CDR_SOURCE_TYPE
from cdr.functions_def import get_hangupcause_id
from user_profile.models import UserProfile
from cdr.helpers import chk_ipaddress, print_shell
from cdr.analytic_handler import generate_global_cdr_record, create_analytic
from voip_billing.rate_engine import calculate_call_cost
import datetime
import sys
import random
from mongodb_connection import mongodb

random.seed()


def build_cdr_dict(cdr):
    """
    function that build and return only the useful element from the
    cdr freeswitch object
    """
    # Get accountcode
    if 'variables' in cdr and 'accountcode' in cdr['variables']:
        accountcode = cdr['variables']['accountcode']
    else:
        accountcode = ''
    # Get remote_media_ip
    if 'variables' in cdr and 'remote_media_ip' in cdr['variables']:
        remote_media_ip = cdr['variables']['remote_media_ip']
    else:
        remote_media_ip = ''
    # Get duration
    if 'variables' in cdr and 'duration' in cdr['variables'] \
       and cdr['variables']['duration']:
        duration = float(cdr['variables']['duration'])
    else:
        duration = 0
    # Get billsec
    if 'variables' in cdr and 'billsec' in cdr['variables'] \
       and cdr['variables']['billsec']:
        billsec = cdr['variables']['billsec']
    else:
        billsec = 0
    # Get direction
    if 'variables' in cdr and 'direction' in cdr['variables']:
        direction = cdr['variables']['direction']
    else:
        direction = 'unknown'
    # Get uuid
    if 'variables' in cdr and 'uuid' in cdr['variables']:
        uuid = cdr['variables']['uuid']
    else:
        uuid = ''
    # Get caller_id_number
    if 'callflow' in cdr and 'caller_profile' in cdr['callflow'][0] \
       and 'caller_id_number' in cdr['callflow'][0]['caller_profile']:
        caller_id_number = cdr['callflow'][0]['caller_profile']['caller_id_number']
    else:
        caller_id_number = ''
    # Get caller_id_name
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


def aggregate_freeswitch_cdr(shell, importcdr_handler, switch, ipaddress):
    """
    function go through the current mongodb, then will
    - create mongodb.cdr_common
    - build the pre-aggregate
    """

    # We limit the import tasks to a maximum - 1000
    # This will reduce the speed but that s the only way to make sure
    # we dont have several time the same tasks running

    PAGE_SIZE = 1000
    count_import = 0
    local_count_import = 0

    # Store cdr in list to insert by bulk
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

    # Retrieve FreeSWITCH CDRs
    for cdr in result:
        # find result so let's look later for more records
        start_uepoch = datetime.datetime.fromtimestamp(
            int(str(cdr['variables']['start_uepoch'])[:10]))

        answer_uepoch = ''
        if cdr['variables']['answer_uepoch']:
            answer_uepoch = datetime.datetime.fromtimestamp(
                int(str(cdr['variables']['answer_uepoch'])[:10]))

        end_uepoch = ''
        if cdr['variables']['end_uepoch']:
            end_uepoch = datetime.datetime.fromtimestamp(
                int(str(cdr['variables']['end_uepoch'])[:10]))

        # Check Destination number
        # print(cdr)
        dest_number = cdr['callflow'][0]['caller_profile']['destination_number']

        if len(dest_number) <= settings.INTERNAL_CALL:
            authorized = 1
            country_id = 999
        else:
            from cdr_alert.functions_blacklist import chk_destination
            destination_data = chk_destination(dest_number)
            authorized = destination_data['authorized']
            country_id = destination_data['country_id']

        hangup_cause_id = get_hangupcause_id(cdr['variables']['hangup_cause_q850'])

        # Retrieve Element from CDR Object
        data_element = build_cdr_dict(cdr)
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

        try:
            voipplan_id = UserProfile.objects.get(accountcode=accountcode).voipplan_id
        except:
            voipplan_id = False
            print_shell(shell, "No VoipPlan created for this user/accountcode")

        print_shell(shell, "calculate_call_cost for vp=%d, dst=%s, billsec=%s" % (voipplan_id, dest_number, billsec))
        call_rate = calculate_call_cost(voipplan_id, dest_number, billsec)
        print_shell(shell, call_rate)
        buy_rate = call_rate['buy_rate']
        buy_cost = call_rate['buy_cost']
        sell_rate = call_rate['sell_rate']
        sell_cost = call_rate['sell_cost']

        # Prepare global CDR
        cdr_record = generate_global_cdr_record(
            switch.id, caller_id_number,
            caller_id_name, dest_number, duration, billsec, hangup_cause_id,
            accountcode, direction, uuid, remote_media_ip, start_uepoch, answer_uepoch,
            end_uepoch, mduration, billmsec, read_codec, write_codec,
            CDR_SOURCE_TYPE.FREESWITCH, cdr['_id'], country_id, authorized,
            buy_rate, buy_cost, sell_rate, sell_cost)

        # Append cdr to bulk_cdr list
        cdr_bulk_record.append(cdr_record)

        # Count CDR import
        count_import = count_import + 1
        local_count_import = local_count_import + 1

        # print_shell(shell, "Sync CDR (cid:%s, dest:%s, dur:%s, " \
        #             " hg:%s,country:%s, auth:%s, row_count:%s)" % (
        #             caller_id_number,
        #             dest_number,
        #             duration,
        #             cdr['variables']['hangup_cause_q850'],
        #             country_id,
        #             authorized,
        #             count_import))

        date_start_uepoch = int(str(cdr['variables']['start_uepoch'])[:10])
        create_analytic(
            date_start_uepoch, start_uepoch, switch.id, country_id, accountcode,
            hangup_cause_id, duration, buy_cost, sell_cost)

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
        # Bulk cdr list insert into mongodb.cdr_common
        mongodb.cdr_common.insert(cdr_bulk_record)
        # Reset counter to zero
        local_count_import = 0
        print_shell(shell, "Switch(%s) - currently imported CDRs:%d" % (ipaddress, count_import))

    print_shell(shell, "Import on Switch(%s) - Total Record(s) imported:%d" % (ipaddress, count_import))


def import_cdr_freeswitch_mongodb(shell=False):
    # Browse settings.CDR_BACKEND and for each IP check if the IP exist
    # in our Switch objects. If it does we will connect to that Database
    # and import the data as we do below

    print_shell(shell, "Starting the synchronization...")

    if not mongodb.cdr_common:
        sys.stderr.write('Error mongodb connection')
        sys.exit(1)

    # loop within the Mongo CDR Import List
    for ipaddress in settings.CDR_BACKEND:

        # Connect to Database
        db_name = settings.CDR_BACKEND[ipaddress]['db_name']
        table_name = settings.CDR_BACKEND[ipaddress]['table_name']
        db_engine = settings.CDR_BACKEND[ipaddress]['db_engine']
        cdr_type = settings.CDR_BACKEND[ipaddress]['cdr_type']
        host = settings.CDR_BACKEND[ipaddress]['host']
        port = settings.CDR_BACKEND[ipaddress]['port']
        # user = settings.CDR_BACKEND[ipaddress]['user']
        # password = settings.CDR_BACKEND[ipaddress]['password']

        if db_engine != 'mongodb' or cdr_type != 'freeswitch':
            sys.stderr.write('This function is intended for mongodb and freeswitch')
            sys.exit(1)

        data = chk_ipaddress(ipaddress)
        ipaddress = data['ipaddress']
        switch = data['switch']

        # Connect on MongoDB Database
        try:
            connection = Connection(host, port)
            DBCON = connection[db_name]
            # DBCON.authenticate(user, password)
        except ConnectionFailure, e:
            sys.stderr.write("Could not connect to MongoDB: %s - %s" % (e, ipaddress))
            sys.exit(1)

        # Connect to Mongo
        importcdr_handler = DBCON[table_name]

        # Start import for this mongoDB
        aggregate_freeswitch_cdr(shell, importcdr_handler, switch, ipaddress)
