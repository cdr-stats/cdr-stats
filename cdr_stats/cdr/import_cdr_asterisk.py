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
from cdr.models import CDR_TYPE
from cdr.import_cdr_freeswitch_mongodb import apply_index,\
    chk_ipaddress, CDR_COMMON, create_daily_analytic,\
    create_monthly_analytic, set_int_default
from cdr.functions_def import get_hangupcause_id
from cdr_alert.functions_blacklist import chk_destination
from datetime import datetime
import re
import sys
import random

random.seed()

HANGUP_CAUSE = ['NORMAL_CLEARING', 'NORMAL_CLEARING', 'NORMAL_CLEARING',
                'NORMAL_CLEARING', 'USER_BUSY', 'NO_ANSWER', 'CALL_REJECTED',
                'INVALID_NUMBER_FORMAT']

# value 0 per default
# 1 in process of import, 2 imported successfully and verified
STATUS_SYNC = {"new": 0, "in_process": 1, "verified": 2}

dic_disposition = {
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

#TODO: We should review the Asterisk Q.850 against this list
DISPOSITION_TRANSLATION = {
    0: 0,
    1: 16,      # ANSWER
    2: 17,      # BUSY
    3: 19,      # NOANSWER
    4: 21,      # CANCEL
    5: 34,      # CONGESTION
    6: 47,      # CHANUNAVAIL
    7: 0,       # DONTCALL
    8: 0,       # TORTURE
    9: 0,       # INVALIDARGS
    10: 41,     # FAILED
}


def print_shell(shell, message):
    if shell:
        print message


def import_cdr_asterisk(shell=False):
    #TODO : dont use the args here
    # Browse settings.CDR_BACKEND and for each IP
    # check if the IP exist in our Switch objects if it does we will
    # connect to that Database and import the data as we do below

    print_shell(shell, "Starting the synchronization...")

    if settings.CDR_BACKEND[settings.LOCAL_SWITCH_IP]['cdr_type'] != 'asterisk':
        print_shell(shell, "The switch is not configured to import Asterisk")
        return False

    #loop within the Mongo CDR Import List
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

        #Connect to Database
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
            #update cursor used as we update at the end and we need
            #to fetch on 1st cursor
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
            row = cursor.fetchone()
        except Exception, e:
            #Add missing field to flag import
            if db_engine == 'mysql':
                cursor.execute("ALTER TABLE %s ADD import_cdr TINYINT NOT NULL "
                    "DEFAULT '0'" % table_name)
            elif db_engine == 'pgsql':
                cursor.execute("ALTER TABLE %s ADD import_cdr SMALLINT NOT NULL "
                    "DEFAULT '0'" % table_name)
            cursor.execute("ALTER TABLE %s ADD INDEX (import_cdr)" %
                table_name)

        count_import = 0

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

        while row is not None:
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
                id_disposition = dic_disposition.get(
                    ast_disposition.encode("utf-8"), 0)
                transdisposition = DISPOSITION_TRANSLATION[id_disposition]
            except:
                transdisposition = 0

            hangup_cause_id = get_hangupcause_id(transdisposition)
            accountcode = row[7]
            uniqueid = row[8]
            start_uepoch = datetime.fromtimestamp(int(row[1]))

            # Check Destination number
            destination_number = row[0]
            if (len(destination_number) <= settings.INTERNAL_CALL
               or destination_number[:1].isalpha()):
                authorized = 1
                country_id = 999
            else:
                destination_data = chk_destination(destination_number)
                authorized = destination_data['authorized']
                country_id = destination_data['country_id']

            #Option to get the direction from user_field
            direction = "unknown"

            # Prepare global CDR
            cdr_record = {
                'switch_id': switch.id,
                'caller_id_number': callerid_number.decode('utf-8', 'ignore'),
                'caller_id_name': callerid_name.decode('utf-8', 'ignore'),
                'destination_number': destination_number.decode('utf-8', 'ignore'),
                'duration': duration,
                'billsec': billsec,
                'hangup_cause_id': hangup_cause_id,
                'accountcode': accountcode,
                'direction': direction,
                'uuid': uniqueid,
                'remote_media_ip': '',
                'start_uepoch': start_uepoch,
                #'answer_uepoch': answer_uepoch,
                #'end_uepoch': end_uepoch,
                #'mduration': '',
                #'billmsec': '',
                #'read_codec': '',
                #'write_codec': '',
                'channel': channel.decode('utf-8', 'ignore'),
                'cdr_type': CDR_TYPE["asterisk"],
                'cdr_object_id': acctid,
                'country_id': country_id,
                'authorized': authorized,
            }

            # record global CDR
            # TODO: implement Bulk insert
            CDR_COMMON.insert(cdr_record)
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
            count_import = count_import + 1
            daily_date = datetime.fromtimestamp(int(row[1]))
            # insert daily analytic record
            create_daily_analytic(daily_date, switch.id, country_id,
                                  accountcode, hangup_cause_id, duration)

            # insert monthly analytic record
            create_monthly_analytic(daily_date, start_uepoch, switch.id,
                                    country_id, accountcode, duration)

            #Flag the CDR
            try:
                #TODO: Build Update by batch of max 100
                cursor_updated.execute(
                    "UPDATE %s SET import_cdr=1 WHERE %s=%d" %
                    (table_name, settings.ASTERISK_PRIMARY_KEY, acctid))
            except:
                print_shell(shell, "ERROR : Update failed (%s:%d)" %
                    (settings.ASTERISK_PRIMARY_KEY, acctid))

            #Fetch a other record
            row = cursor.fetchone()

        cursor_updated.close()
        cursor.close()
        connection.close()

        if count_import > 0:
            #TODO: Apply index only if needed
            apply_index(shell)

        print_shell(shell, "Import on Switch(%s) - Record(s) imported:%d" %
            (ipaddress, count_import))
