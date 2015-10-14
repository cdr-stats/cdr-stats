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
from django.db import connections
from cdr.models import CDR, CALL_DIRECTION, CALL_TYPE
from import_cdr.models import CDRImport
from cdr.helpers import print_shell, chk_ipaddress
from cdr.functions_def import get_dialcode, get_hangupcause_id
from voip_billing.rate_engine import calculate_call_cost
from cdr_alert.functions_blacklist import verify_auth_dest_number
from user_profile.models import AccountCode
from user_profile.models import UserProfile
from django.db.utils import OperationalError
from django.db import ProgrammingError


def check_connection_sql():
    """
    check the import postgresql database is up and reachable
    """
    try:
        cursor = connections['import_cdr'].cursor()
        cursor.execute("SELECT 1 FROM cdr_import")
        row = cursor.fetchone()
        if row:
            return row[0] == 1
        else:
            return True
    except OperationalError:
        # Error Connection to CDR-Pusher
        return False
    except ProgrammingError:
        # Error Running SQL on CDR-Pusher
        return False
    except:
        raise


def get_to_import_cdr_count():
    """
    check the import postgresql database is up and reachable
    """
    cursor = connections['import_cdr'].cursor()
    # Get non imported cdrs
    cursor.execute("SELECT count(*) FROM cdr_import WHERE imported=False")
    row = cursor.fetchone()
    not_imported_cdr = row[0]
    # Get cdrs
    cursor.execute("SELECT count(*) FROM cdr_import")
    row = cursor.fetchone()
    total_cdr = row[0]
    return (total_cdr, not_imported_cdr)


def bulk_create_cdrs(list_newcdr, list_cdrid):
    """
    bulk_create_cdrs create in bulk the CDRs in the list 'list_newcdr'
    and it will update 'import_cdr' database with the imported CDRs
    """
    # Bulk Insert the new CDRs
    CDR.objects.bulk_create(list_newcdr)
    # Update the imported CDRs
    update_cdr = "UPDATE cdr_import SET imported=True WHERE id in (%s)" % ", ".join(list_cdrid)
    cursor = connections['import_cdr'].cursor()
    cursor.execute(update_cdr)


def log_print(logger, shell, msg):
    if logger:
        logger.info(msg)
    else:
        print_shell(shell, msg)


def import_cdr(shell=False, logger=False):
    """
    Connect to the `import_cdr` Database and import the new CDRs
    """
    count_imported = 0
    log_print(logger, shell, "in func import_cdr...")

    if not check_connection_sql():
        log_print(logger, shell, "check_connection_sql - Error Connection")
        return (False, "Error Connection")

    # Each time the task is running we will only take CDR_IMPORT_LIMIT records to import
    # This define the max speed of import, this limit could be changed
    new_CDRs = CDRImport.objects.using('import_cdr')\
        .filter(imported=False)\
        .order_by('-id')[:settings.CDR_IMPORT_LIMIT]

    (list_newcdr, list_cdrid) = ([], [])
    for call in new_CDRs:
        # Increment counter
        count_imported = count_imported + 1

        # Get the dialcode
        dialcode = get_dialcode(call.destination_number, call.dialcode)
        switch_info = chk_ipaddress(call.switch)

        # Check Destination number
        if len(call.destination_number) <= settings.INTERNAL_CALL or call.destination_number[:1].isalpha():
            authorized = 1
            country_id = None
            call_type = CALL_TYPE.INTERNAL
        else:
            # TODO: rename verify_auth_dest_number verify_auth_dest_number
            destination_data = verify_auth_dest_number(call.destination_number)
            authorized = destination_data['authorized']
            country_id = destination_data['country_id']
            call_type = CALL_TYPE.INTERNATIONAL

        # Sanitize direction
        if call.direction:
            direction = call.direction
        else:
            direction = CALL_DIRECTION.NOTDEFINED

        # Find the user for given accountcode
        try:
            user = AccountCode.objects.get(accountcode=call.accountcode).user
        except:
            # Cannot assign accountcode to an existing user, therefore we will assign to an Admin
            user = User.objects.filter(is_superuser=True)[0]

        try:
            user_profile = user.userprofile
        except:
            user_profile = UserProfile(user=user)
            user_profile.save()

        # Retrieve VoipPlan
        if user_profile:
            voipplan_id = user_profile.voipplan_id
        else:
            voipplan_id = False
            print_shell(shell, "VoipPlan doesn't exist for this user/accountcode (%s)" % call.accountcode)

        if call.buy_rate or call.buy_cost or call.sell_rate or call.sell_cost:
            buy_rate = call.buy_rate
            buy_cost = call.buy_cost
            sell_rate = call.sell_rate
            sell_cost = call.sell_cost
        elif voipplan_id:
            call_rate = calculate_call_cost(voipplan_id, call.destination_number, call.billsec)
            buy_rate = call_rate['buy_rate']
            buy_cost = call_rate['buy_cost']
            sell_rate = call_rate['sell_rate']
            sell_cost = call_rate['sell_cost']
        else:
            buy_rate = buy_cost = sell_rate = sell_cost = 0

        hangup_cause_id = get_hangupcause_id(call.hangup_cause_id)

        log_print(logger, shell, "Create new CDR -> date:%s - dst:%s - duration:%s - hangup_cause:%s - sell_cost:%s" %
                  (call.starting_date, call.destination_number, str(call.duration), str(hangup_cause_id), str(call.sell_cost)))

        # Create the new CDR
        newCDR = CDR(
                     user=user,
                     switch=switch_info['switch'],
                     cdr_source_type=call.cdr_source_type,
                     callid=call.callid,
                     caller_id_number=call.caller_id_number,
                     caller_id_name=call.caller_id_name,
                     destination_number=call.destination_number,
                     dialcode_id=dialcode,
                     starting_date=call.starting_date,
                     duration=call.duration,
                     billsec=call.billsec,
                     progresssec=call.progresssec,
                     answersec=call.answersec,
                     waitsec=call.waitsec,
                     hangup_cause_id=hangup_cause_id,
                     direction=direction,
                     country_id=country_id,
                     authorized=authorized,
                     accountcode='' if call.accountcode is None else call.accountcode,
                     buy_rate=buy_rate,
                     buy_cost=buy_cost,
                     sell_rate=sell_rate,
                     sell_cost=sell_cost,
                     call_type=call_type,
                     data='' if call.extradata is None else call.extradata)
        list_newcdr.append(newCDR)

        list_cdrid.append(str(call.id))
        if (count_imported % 100) == 0:
            bulk_create_cdrs(list_newcdr, list_cdrid)
            (list_newcdr, list_cdrid) = ([], [])

    # we exit the loop but we might still have some remaining CDRs to push
    if len(list_newcdr) > 0:
        bulk_create_cdrs(list_newcdr, list_cdrid)
        (list_newcdr, list_cdrid) = ([], [])

    log_print(logger, shell, 'TASK :: run_cdr_import -> func import_cdr count_imported:%d' % count_imported)

    return (True, count_imported)
