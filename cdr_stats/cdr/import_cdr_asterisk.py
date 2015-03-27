#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2015 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#
from django.conf import settings
from cdr.models import CDR_SOURCE_TYPE
from cdr.import_cdr_freeswitch_mongodb import create_analytic
from cdr.helpers import chk_ipaddress, set_int_default, print_shell
from voip_billing.rate_engine import calculate_call_cost
from cdr.functions_def import get_hangupcause_id
from cdr_alert.functions_blacklist import chk_destination
from user_profile.models import UserProfile
from datetime import datetime
from mongodb_connection import mongodb
import re
import sys
import random

random.seed()


DICT_DISPOSITION = {
    'ANSWER': 1, 'ANSWERED': 1,
    'BUSY': 2,
    'NOANSWER': 3, 'NO ANSWER': 3,
    'CANCEL': 4,
    'CONGESTION': 5,
    'CHANUNAVAIL': 6,
    'DONTCALL': 7,
    'TORTURE': 8,
    'INVALIDARGS': 9,
    'FAIL': 10, 'FAILED': 10
}

# Try to match the Asterisk Dialstatus against Q.850
DISPOSITION_TRANSLATION = {
    0: 0,
    1: 16,      # ANSWER
    2: 17,      # BUSY
    3: 19,      # NOANSWER
    4: 21,      # CANCEL
    5: 34,      # CONGESTION
    6: 47,      # CHANUNAVAIL
    # DONTCALL: Privacy mode, callee rejected the call
    # Specific to Asterisk
    7: 21,       # DONTCALL
    # TORTURE: Privacy mode, callee chose to send caller to torture menu
    # Specific to Asterisk
    8: 21,       # TORTURE
    # INVALIDARGS: Error parsing Dial command arguments
    # Specific to Asterisk
    9: 47,       # INVALIDARGS
    10: 41,     # FAILED
}


def aggregate_asterisk_cdr(shell, table_name, db_engine, cursor, cursor_updated, switch, ipaddress):
    """
    function to import and aggreagate Asterisk CDR
    """
    count_import = 0

    # Each time the task is running we will only take 1000 records to import
    # This define the max speed of import, this limit could be changed
    if db_engine == 'mysql':
        cursor.execute("SELECT dst, UNIX_TIMESTAMP(calldate), clid, channel,"
                       "duration, billsec, disposition, accountcode, uniqueid,"
                       " %s FROM %s WHERE import_cdr=0 LIMIT 0, 1000" %
                       (settings.ASTERISK_PRIMARY_KEY, table_name))
    elif db_engine == 'pgsql':
        cursor.execute("SELECT dst, extract(epoch FROM calldate), clid, channel,"
                       "duration, billsec, disposition, accountcode, uniqueid,"
                       " %s FROM %s WHERE import_cdr=0 LIMIT 1000" %
                       (settings.ASTERISK_PRIMARY_KEY, table_name))
    row = cursor.fetchone()

    # Store cdr in list to insert by bulk
    cdr_bulk_record = []
    local_count_import = 0
    batch_count = 0
    acctid_list = ''

    while row is not None:
        destination_number = row[0]
        if not destination_number:
            continue

        acctid = row[9]
        callerid = row[2]
        try:
            m = re.search('"(.+?)" <(.+?)>', callerid)
            callerid_name = m.group(1)
            callerid_number = m.group(2)
        except:
            callerid_name = ''
            callerid_number = callerid

        channel = row[3]
        if not channel:
            channel = ''  # Set empty string for channel in case is None
        duration = set_int_default(row[4], 0)
        billsec = set_int_default(row[5], 0)
        ast_disposition = row[6]
        try:
            id_disposition = DICT_DISPOSITION.get(
                ast_disposition.encode("utf-8"), 0)
            transdisposition = DISPOSITION_TRANSLATION[id_disposition]
        except:
            transdisposition = 0

        hangup_cause_id = get_hangupcause_id(transdisposition)
        accountcode = row[7]
        uniqueid = row[8]
        start_uepoch = datetime.fromtimestamp(int(row[1]))

        # Check Destination number
        if len(destination_number) <= settings.INTERNAL_CALL or destination_number[:1].isalpha():
            authorized = 1
            country_id = 999
        else:
            destination_data = chk_destination(destination_number)
            authorized = destination_data['authorized']
            country_id = destination_data['country_id']

        # Option to get the direction from user_field
        direction = "unknown"

        try:
            voipplan_id = UserProfile.objects.get(accountcode=accountcode).voipplan_id
        except:
            voipplan_id = False
            print_shell(shell, "No VoipPlan created for this user/accountcode")

        call_rate = calculate_call_cost(voipplan_id, destination_number, billsec)
        buy_rate = call_rate['buy_rate']
        buy_cost = call_rate['buy_cost']
        sell_rate = call_rate['sell_rate']
        sell_cost = call_rate['sell_cost']

        # Sanitize callerid_number
        try:
            callerid_number = callerid_number.decode('utf-8', 'ignore')
        except AttributeError:
            callerid_number = ''
        # Sanitize callerid_name
        try:
            callerid_name = callerid_name.decode('utf-8', 'ignore')
        except AttributeError:
            callerid_name = ''
        # Sanitize destination_number
        try:
            destination_number = destination_number.decode('utf-8', 'ignore')
        except AttributeError:
            destination_number = ''
        # Sanitize channel
        try:
            channel = channel.decode('utf-8', 'ignore')
        except AttributeError:
            channel = ''

        # Prepare global CDR
        cdr_record = {
            'switch_id': switch.id,
            'caller_id_number': callerid_number,
            'caller_id_name': callerid_name,
            'destination_number': destination_number,
            'duration': duration,
            'billsec': billsec,
            'hangup_cause_id': hangup_cause_id,
            'accountcode': accountcode,
            'direction': direction,
            'uuid': uniqueid,
            'remote_media_ip': '',
            'start_uepoch': start_uepoch,
            # 'answer_uepoch': answer_uepoch,
            # 'end_uepoch': end_uepoch,
            # 'mduration': '',
            # 'billmsec': '',
            # 'read_codec': '',
            # 'write_codec': '',
            'channel': channel,
            'cdr_type': CDR_SOURCE_TYPE.ASTERISK,
            'cdr_object_id': acctid,
            'country_id': country_id,
            'authorized': authorized,

            # For billing
            'buy_rate': buy_rate,
            'buy_cost': buy_cost,
            'sell_rate': sell_rate,
            'sell_cost': sell_cost,
        }

        # Append cdr to bulk_cdr list
        cdr_bulk_record.append(cdr_record)
        count_import = count_import + 1
        local_count_import = local_count_import + 1
        batch_count = batch_count + 1

        """
        print_shell(shell, "Sync CDR (%s:%d, cid:%s, dest:%s, dur:%s, "\
                            "hg:%s, country:%s, auth:%s, calldate:%s)" % (
                                settings.ASTERISK_PRIMARY_KEY,
                                acctid,
                                callerid_number,
                                destination_number,
                                duration,
                                hangup_cause_id,
                                country_id,
                                authorized,
                                start_uepoch.strftime('%Y-%m-%d %M:%S'),))
        """
        date_start_uepoch = str(row[1])
        create_analytic(date_start_uepoch, start_uepoch, switch.id,
                        country_id, accountcode, hangup_cause_id, duration,
                        buy_cost, sell_cost)

        acctid_list += "%s, " % str(acctid)
        if batch_count == 100:
            acctid_list = acctid_list[:-2]  # trim last comma (,) from string
            # Postgresql
            # select * from table_name where id in (1,2,3);
            update_cdr = "UPDATE %s SET import_cdr=1 WHERE %s in (%s)" % \
                (table_name, settings.ASTERISK_PRIMARY_KEY, acctid_list)
            cursor_updated.execute(update_cdr)

            batch_count = 0
            acctid_list = ''

        # Fetch a other record
        row = cursor.fetchone()

    if len(acctid_list) > 0:
        acctid_list = acctid_list[:-2]  # trim last comma (,) from string
        # Postgresql
        # select * from table_name where id in (1,2,3);
        update_cdr = "UPDATE %s SET import_cdr=1 WHERE %s in (%s)" % \
            (table_name, settings.ASTERISK_PRIMARY_KEY, acctid_list)
        cursor_updated.execute(update_cdr)

    if local_count_import > 0:
        # Bulk cdr list insert into cdr_common
        mongodb.cdr_common.insert(cdr_bulk_record)
        # Reset counter to zero
        local_count_import = 0
        cdr_bulk_record = []

    return count_import


# aggregate_asterisk_cdr
def import_cdr_asterisk(shell=False):
    # Browse settings.CDR_BACKEND and for each IP
    # check if the IP exist in our Switch objects if it does we will
    # connect to that Database and import the data as we do below

    print_shell(shell, "Starting the synchronization...")

    if settings.CDR_BACKEND[settings.LOCAL_SWITCH_IP]['cdr_type'] != 'asterisk':
        print_shell(shell, "The switch is not configured to import Asterisk")
        return False

    # loop within the Mongo CDR Import List
    for ipaddress in settings.CDR_BACKEND:

        db_engine = settings.CDR_BACKEND[ipaddress]['db_engine']
        if db_engine == 'mysql':
            import MySQLdb as Database
        elif db_engine == 'pgsql':
            import psycopg2 as PgDatabase
        else:
            sys.stderr.write("Wrong setting for db_engine: %s" %
                             (str(db_engine)))
            sys.exit(1)

        data = chk_ipaddress(ipaddress)
        ipaddress = data['ipaddress']
        switch = data['switch']

        # Connect to Database
        db_name = settings.CDR_BACKEND[ipaddress]['db_name']
        table_name = settings.CDR_BACKEND[ipaddress]['table_name']
        user = settings.CDR_BACKEND[ipaddress]['user']
        password = settings.CDR_BACKEND[ipaddress]['password']
        host = settings.CDR_BACKEND[ipaddress]['host']
        port = settings.CDR_BACKEND[ipaddress]['port']
        try:
            if db_engine == 'mysql':
                connection = Database.connect(user=user, passwd=password,
                                              db=db_name, host=host, port=port)
                connection.autocommit(True)
            elif db_engine == 'pgsql':
                connection = PgDatabase.connect(user=user, password=password,
                                                database=db_name, host=host, port=port)
                connection.autocommit = True
            cursor = connection.cursor()
            # update cursor used as we update at the end and we need
            # to fetch on 1st cursor
            cursor_updated = connection.cursor()
        except Exception, e:
            sys.stderr.write("Could not connect to Database: %s - %s" %
                             (e, ipaddress))
            sys.exit(1)

        try:
            if db_engine == 'mysql':
                cursor.execute("SELECT VERSION() from %s WHERE import_cdr "
                               "IS NOT NULL LIMIT 0,1" % table_name)
            elif db_engine == 'pgsql':
                cursor.execute("SELECT VERSION() from %s WHERE import_cdr "
                               "IS NOT NULL LIMIT 1" % table_name)
            cursor.fetchone()
        except Exception, e:
            # Add missing field to flag import
            if db_engine == 'mysql':
                cursor.execute("ALTER TABLE %s ADD import_cdr TINYINT NOT NULL "
                               "DEFAULT '0'" % table_name)
            elif db_engine == 'pgsql':
                cursor.execute("ALTER TABLE %s ADD import_cdr SMALLINT NOT NULL "
                               "DEFAULT '0'" % table_name)
            cursor.execute("ALTER TABLE %s ADD INDEX (import_cdr)" %
                           table_name)

        count_import = aggregate_asterisk_cdr(shell, table_name, db_engine, cursor, cursor_updated, switch, ipaddress)

        cursor_updated.close()
        cursor.close()
        connection.close()

        print_shell(shell, "Import on Switch(%s) - Record(s) imported:%d" %
                    (ipaddress, count_import))
