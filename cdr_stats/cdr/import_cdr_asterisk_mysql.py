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
import MySQLdb as Database
from cdr.models import Switch, CDR_TYPE
from cdr.import_cdr_freeswitch_mongodb import apply_index,\
                                              CDR_COMMON,\
                                              CDR_ANALYTIC,\
                                              CDR_MONTHLY,\
                                              CDR_DAILY,\
                                              CDR_HOURLY,\
                                              CDR_COUNTRY_REPORT
from cdr.functions_def import get_hangupcause_id
from cdr_alert.functions_blacklist import chk_destination

import sys
from datetime import datetime
import random
import re

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
            'FAIL': 10, 'FAILED': 10}

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


def import_cdr_asterisk_mysql(shell=False):
    #TODO : dont use the args here
    # Browse settings.ASTERISK_MYSQL and for each IP
    # check if the IP exist in our Switch objects if it does we will
    # connect to that Database and import the data as we do below

    print_shell(shell, "Starting the synchronization...")

    if settings.LOCAL_SWITCH_TYPE != 'asterisk':
        print_shell(shell, "The switch is not configured to import Asterisk")
        return False

    #loop within the Mongo CDR Import List
    for ipaddress in settings.ASTERISK_MYSQL:
        #Select the Switch ID
        print_shell(shell, "Switch : %s" % ipaddress)

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
            print_shell(shell, "Error when adding new Switch!")
            raise SystemExit

        if DEV_ADD_IP:
            ipaddress = previous_ip

        #Connect on Mysql Database
        db_name = settings.ASTERISK_MYSQL[ipaddress]['db_name']
        table_name = settings.ASTERISK_MYSQL[ipaddress]['table_name']
        user = settings.ASTERISK_MYSQL[ipaddress]['user']
        password = settings.ASTERISK_MYSQL[ipaddress]['password']
        host = settings.ASTERISK_MYSQL[ipaddress]['host']
        try:
            connection = Database.connect(user=user, passwd=password, \
                                            db=db_name, host=host)
            cursor = connection.cursor()
            cursor_update = connection.cursor()
        except Exception, e:
            sys.stderr.write("Could not connect to Mysql: %s - %s" % \
                                                            (e, ipaddress))
            sys.exit(1)

        try:
            cursor.execute("SELECT VERSION() from %s WHERE import_cdr "\
                            "IS NOT NULL LIMIT 0,1" % table_name)
            row = cursor.fetchone()
        except Exception, e:
            #Add missing field to flag import
            cursor.execute("ALTER TABLE %s  ADD import_cdr TINYINT NOT NULL "\
                            "DEFAULT '0'" % table_name)
            cursor.execute("ALTER TABLE %s ADD INDEX (import_cdr)" % \
                            table_name)

        count_import = 0

        cursor.execute("SELECT dst, UNIX_TIMESTAMP(calldate), clid, channel," \
                    "duration, billsec, disposition, accountcode, uniqueid," \
                    " %s FROM %s WHERE import_cdr=0" % \
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
            try:
                duration = int(row[4])
            except:
                duration = 0
            try:
                billsec = int(row[5])
            except:
                billsec = 0
            ast_disposition = row[6]
            try:
                id_disposition = dic_disposition.get(
                                        ast_disposition.encode("utf-8"), 0)
                transdisposition = DISPOSITION_TRANSLATION[id_disposition]
            except:
                transdisposition = 0

            hangup_cause_id = get_hangupcause_id(transdisposition)

            try:
                accountcode = int(row[7])
            except:
                accountcode = ''

            uniqueid = row[8]
            start_uepoch = datetime.fromtimestamp(int(row[1]))
            answer_uepoch = start_uepoch
            end_uepoch = datetime.fromtimestamp(int(row[1]) + int(duration))

            # Check Destination number
            destination_number = row[0]

            destination_data = chk_destination(destination_number)
            authorized = destination_data['authorized']
            country_id = destination_data['country_id']

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
                'direction': "inbound",
                'uuid': uniqueid,
                'remote_media_ip': '',
                'start_uepoch': start_uepoch,
                'answer_uepoch': answer_uepoch,
                'end_uepoch': end_uepoch,
                'mduration': '',
                'billmsec': '',
                'read_codec': '',
                'write_codec': '',
                'channel': channel,
                'cdr_type': CDR_TYPE["asterisk"],
                'cdr_object_id': acctid,
                'country_id': country_id,
                'authorized': authorized,
            }

            # record global CDR
            CDR_COMMON.insert(cdr_record)

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
            count_import = count_import + 1

            # start_uepoch = row[1]
            daily_date = \
                datetime.datetime.fromtimestamp(int(row[1][:10]))

            id_daily = daily_date.strftime('%Y%m%d/') + "%d/%d" %\
                                                        (switch.id, country_id)
            hour = daily_date.hour
            minute = daily_date.minute
            # Get a datetime that only include date info
            d = datetime.datetime.combine(daily_date.date(), datetime.time.min)

            # preaggregate update
            CDR_ANALYTIC.update(
                    {
                    "_id": id_daily,
                    "metadata": {
                        "date": d,
                        "switch_id": switch.id,
                        "country_id": country_id,
                        "accountcode": accountcode,
                        },
                    },
                    {
                    "$inc": {
                        "call_daily": 1,
                        "call_hourly.%d" % (hour,): 1,
                        "call_minute.%d.%d" % (hour, minute): 1,
                        "duration_daily": duration,
                        "duration_hourly.%d" % (hour,): duration,
                        "duration_minute.%d.%d" % (hour, minute): duration,
                        }
                }, upsert=True)

            """
            # Store monthly cdr collection with unique import
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
                                 'duration': duration}
                        }, upsert=True)

            # Store daily cdr collection with unique import
            current_y_m_d = datetime.strptime(str(start_uepoch)[:10],
                                                            "%Y-%m-%d")
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
                             'duration': duration}
                    }, upsert=True)

            # Store hourly cdr collection with unique import
            current_y_m_d_h = datetime.strptime(str(start_uepoch)[:13],
                                                                "%Y-%m-%d %H")
            CDR_HOURLY.update(
                        {
                            'start_uepoch': current_y_m_d_h,
                            'destination_number': destination_number,
                            'hangup_cause_id': hangup_cause_id,
                            'accountcode': accountcode,
                            'switch_id': switch.id},
                        {
                            '$inc': {'calls': 1,
                                     'duration': duration}
                        }, upsert=True)

            # Country report collection
            current_y_m_d_h_m = datetime.strptime(str(start_uepoch)[:16],
                                                        "%Y-%m-%d %H:%M")
            CDR_COUNTRY_REPORT.update(
                                {
                                    'start_uepoch': current_y_m_d_h_m,
                                    'country_id': country_id,
                                    'accountcode': accountcode,
                                    'switch_id': switch.id},
                                {
                                    '$inc': {'calls': 1,
                                             'duration': duration}
                                }, upsert=True)
            """
            #Flag the CDR
            try:
                cursor_update.execute(
                        "UPDATE %s SET import_cdr=1 WHERE %s=%d" % \
                        (table_name, settings.ASTERISK_PRIMARY_KEY, acctid))
            except:
                print_shell(shell, "ERROR : Update failed (%s:%d)" % \
                                    (settings.ASTERISK_PRIMARY_KEY, acctid))

            #Fetch a other record
            row = cursor.fetchone()

        cursor.close()
        cursor_update.close()
        connection.close()

        if count_import > 0:
            apply_index()


        print_shell(shell, "Import on Switch(%s) - Record(s) imported:%d" % \
                            (ipaddress, count_import))
