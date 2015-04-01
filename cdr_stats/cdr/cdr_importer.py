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
from cdr.models import CDR
from import_cdr.models import CDRImport
from cdr.helpers import print_shell, chk_ipaddress
from cdr.functions_def import remove_prefix, prefix_list_string, get_country_id_prefix
from voip_billing.rate_engine import calculate_call_cost
from cdr_alert.functions_blacklist import verify_auth_dest_number
from user_profile.models import UserProfile


def get_dialcode(destination_number, dialcode):
    """
    Retrieve the correct dialcode for a destination_number
    """
    if dialcode and len(dialcode) > 0:
        return dialcode
    else:
        # remove prefix
        sanitized_destination = remove_prefix(destination_number, settings.PREFIX_TO_IGNORE)
        prefix_list = prefix_list_string(sanitized_destination)

        if len(sanitized_destination) > settings.PN_MAX_DIGITS and not sanitized_destination[:1].isalpha():
            # International call
            (country_id, prefix_id) = get_country_id_prefix(prefix_list)
            dialcode = prefix_id
        else:
            dialcode = ''
    return dialcode


def import_cdr(shell=False):
    """
    Connect to the `import_cdr` Database and import the new CDRs
    """
    count_imported = 0

    # Each time the task is running we will only take 5000 records to import
    # This define the max speed of import, this limit could be changed
    new_CDRs = CDRImport.objects.filter(imported=False)[:5000]

    for call in new_CDRs:
        # TODO: Store cdr in list to insert by bulk
        #
        dialcode = get_dialcode(call.destination_number, call.dialcode)
        switch_info = chk_ipaddress(call.switch)
        cdr_json = call.extradata

        # Check Destination number
        if len(call.destination_number) <= settings.INTERNAL_CALL or call.destination_number[:1].isalpha():
            authorized = 1
            country_id = 999
        else:
            # TODO: rename verify_auth_dest_number verify_auth_dest_number
            destination_data = verify_auth_dest_number(call.destination_number)
            authorized = destination_data['authorized']
            country_id = destination_data['country_id']

        # Retrieve VoipPlan
        try:
            voipplan_id = UserProfile.objects.get(accountcode=call.accountcode).voipplan_id
        except:
            voipplan_id = False
            print_shell(shell, "No VoipPlan created for this user/accountcode")

        try:
            user = UserProfile.objects.get(accountcode=call.accountcode).user
        except:
            # Cannot assign accountcode to an existing user
            # we will then assign to admin
            user = User.objects.filter(is_superuser=True)[0]

        if call.buy_rate or call.buy_cost or call.sell_rate or call.sell_cost:
            buy_rate = call.buy_rate
            buy_cost = call.buy_cost
            sell_rate = call.sell_rate
            sell_cost = call.sell_cost
        else:
            call_rate = calculate_call_cost(voipplan_id, call.destination_number, call.billsec)
            buy_rate = call_rate['buy_rate']
            buy_cost = call_rate['buy_cost']
            sell_rate = call_rate['sell_rate']
            sell_cost = call_rate['sell_cost']

        # Create the new CDR
        new_cdr = CDR(
                      user=user,
                      switch=switch_info['switch'],
                      cdr_source_type=call.cdr_source_type,
                      callid=call.callid,
                      caller_id_number=call.callerid_number,
                      destination_number=call.destination_number,
                      dialcode_id=dialcode,
                      starting_date=call.starting_date,
                      duration=call.duration,
                      billsec=call.billsec,
                      progresssec=call.progresssec,
                      answersec=call.answersec,
                      waitsec=call.waitsec,
                      hangup_cause=call.hangup_cause_id,
                      direction=call.direction,
                      country_id=country_id,
                      authorized=authorized,
                      accountcode=call.accountcode,
                      buy_rate=buy_rate,
                      buy_cost=buy_cost,
                      sell_rate=sell_rate,
                      sell_cost=sell_cost,
                      data=cdr_json)
        new_cdr.save()

        count_imported = count_imported + 1

    return count_imported
