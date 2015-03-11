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

from cdr.models import Switch
from voip_billing.rate_engine import rate_engine


def print_shell(shell, message):
    """ helper to print to shell"""
    if shell:
        print message


def set_int_default(val, default):
    """val if not int set default"""
    try:
        return int(val)
    except:
        return default


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


def calculate_call_cost(voipplan_id, dest_number, billsec):
    """
    Calcultate the cost of the call, based on the voip plan and the destination
    """
    rates = rate_engine(voipplan_id=voipplan_id, dest_number=dest_number)
    buy_rate = 0.0
    buy_cost = 0.0
    sell_rate = 0.0
    sell_cost = 0.0
    if rates:
        buy_rate = float(rates[0].carrier_rate)
        sell_rate = float(rates[0].retail_rate)
        buy_cost = buy_rate * float(billsec) / 60
        sell_cost = sell_rate * float(billsec) / 60

    data = {
        'buy_rate': buy_rate,
        'buy_cost': round(buy_cost, 4),
        'sell_rate': sell_rate,
        'sell_cost': round(sell_cost, 4),
    }
    return data
