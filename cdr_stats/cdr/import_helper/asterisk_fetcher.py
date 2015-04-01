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
from django.contrib.auth.models import User
from cdr.models import CDR_SOURCE_TYPE, CDR
from cdr.helpers import set_int_default, print_shell
from voip_billing.rate_engine import calculate_call_cost
from cdr_alert.functions_blacklist import verify_auth_dest_number
from cdr.import_helper.asterisk import translate_disposition
from user_profile.models import UserProfile
from datetime import datetime
import re
import sys


def sanitize_cdr_field(field):
    """
    Sanitize CDR fields
    """
    try:
        field = field.decode('utf-8', 'ignore')
    except AttributeError:
        field = ''

    return field


def push_asterisk_cdr(shell, table_name, db_engine, cursor, cursor_updated, switch, ipaddress):
    """
    function to import and aggreagate Asterisk CDR
    """
    cdr_source_type = CDR_SOURCE_TYPE.ASTERISK
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
    local_count_import = 0
    batch_count = 0
    acctid_list = ''

    while row is not None:
        destination_number = row[0]
        if not destination_number:
            # don't import CDR with no destination number
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
        hangup_cause_id = translate_disposition(row[6])

        accountcode = row[7]
        uniqueid = row[8]
        start_uepoch = datetime.fromtimestamp(int(row[1]))

        # Check Destination number
        if len(destination_number) <= settings.INTERNAL_CALL or destination_number[:1].isalpha():
            authorized = 1
            country_id = 999
        else:
            destination_data = verify_auth_dest_number(destination_number)
            authorized = destination_data['authorized']
            country_id = destination_data['country_id']

        # Option to get the direction from user_field
        direction = "unknown"

        try:
            voipplan_id = UserProfile.objects.get(accountcode=accountcode).voipplan_id
        except:
            voipplan_id = False
            print_shell(shell, "No VoipPlan created for this user/accountcode")

        try:
            user = UserProfile.objects.get(accountcode=accountcode).user
        except:
            # Cannot assign accountcode to an existing user
            # we will then assign to admin
            user = User.objects.filter(is_superuser=True)[0]

        call_rate = calculate_call_cost(voipplan_id, destination_number, billsec)
        buy_rate = call_rate['buy_rate']
        buy_cost = call_rate['buy_cost']
        sell_rate = call_rate['sell_rate']
        sell_cost = call_rate['sell_cost']

        # Sanitize
        callerid_number = sanitize_cdr_field(callerid_number)
        callerid_name = sanitize_cdr_field(callerid_name)
        destination_number = sanitize_cdr_field(destination_number)
        channel = sanitize_cdr_field(channel)

        cdr_json = {'channel': channel}
        dialcode = ''

        cdr = CDR(user=user, switch=switch, cdr_source_type=cdr_source_type,
                  callid=uniqueid, caller_id_number=callerid_number, destination_number=destination_number,
                  dialcode_id=dialcode, starting_date=start_uepoch, duration=duration,
                  billsec=billsec, hangup_cause=hangup_cause_id, direction=direction,
                  country_id=country_id, authorized=authorized, accountcode=accountcode,
                  buy_rate=buy_rate, buy_cost=buy_cost, sell_rate=sell_rate, sell_cost=sell_cost,
                  data=cdr_json)
        cdr.save()

        # Append cdr to bulk_cdr list
        count_import = count_import + 1
        local_count_import = local_count_import + 1
        batch_count = batch_count + 1

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

    return count_import


# This function is not used, it's replaced by cdr-pusher
# import Asterisk CDRs
def import_cdr_asterisk(shell=False):
    # connect to that Database and import the data as we do below

    # hardcode settings to import Asterisk
    db_engine = "pgsql"
    db_name = "cdr"
    table_name = "cdr"
    user = "postgres"
    password = "password"
    host = "localhost"
    port = "5432"

    if db_engine == 'mysql':
        import MySQLdb as Database
    elif db_engine == 'pgsql':
        import psycopg2 as PgDatabase
    else:
        sys.stderr.write("Wrong setting for db_engine: %s" % db_engine)
        sys.exit(1)

    ipaddress = "127.0.0.1"
    switch = 1  # do a lookup

    # Connect to Database
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

    count_import = push_asterisk_cdr(shell, table_name, db_engine, cursor, cursor_updated, switch, ipaddress)

    cursor_updated.close()
    cursor.close()
    connection.close()

    print_shell(shell, "Import on Switch(%s) - Record(s) imported:%d" %
                (ipaddress, count_import))
