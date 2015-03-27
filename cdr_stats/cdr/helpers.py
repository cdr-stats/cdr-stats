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

from cdr.models import Switch, CDR
from aggregator.aggregate_cdr import custom_sql_aggr_top_hangup_last24hours, \
    custom_sql_matv_voip_cdr_aggr_last24hours
from aggregator.aggregate_cdr import custom_sql_aggr_top_country_last24hours
from cdr.functions_def import calculate_act_acd
from common.helpers import trunc_date_start, trunc_date_end
from datetime import date, timedelta


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


def get_cdr_mail_report(user):
    """
    General function to get previous day CDR report
    """
    # Get yesterday's CDR-Stats Mail Report
    yesterday = date.today() - timedelta(1)
    start_date = trunc_date_start(yesterday)
    end_date = trunc_date_end(yesterday)

    # Build filter for CDR.object
    kwargs = {}
    if start_date:
        kwargs['starting_date__gte'] = start_date

    if end_date:
        kwargs['starting_date__lte'] = end_date

    # user are restricted to their own CDRs
    if not user.is_superuser:
        kwargs['user_id'] = user.id

    cdrs = CDR.objects.filter(**kwargs)[:10]

    # Get list of calls/duration for each of the last 24 hours
    (calls_hour_aggr, total_calls, total_duration, total_billsec, total_buy_cost, total_sell_cost) = custom_sql_matv_voip_cdr_aggr_last24hours(user, switch_id=0)

    # Get top 5 of country calls for last 24 hours
    country_data = custom_sql_aggr_top_country_last24hours(user, switch_id=0, limit=5)

    # Get top 10 of hangup cause calls for last 24 hours
    hangup_cause_data = custom_sql_aggr_top_hangup_last24hours(user, switch_id=0)

    # Calculate the Average Time of Call
    metric_aggr = calculate_act_acd(total_calls, total_duration)

    mail_data = {
        'yesterday_date': start_date,
        'rows': cdrs,
        'total_duration': total_duration,
        'total_calls': total_calls,
        'total_buy_cost': total_buy_cost,
        'total_sell_cost': total_sell_cost,
        'metric_aggr': metric_aggr,
        'country_data': country_data,
        'hangup_cause_data': hangup_cause_data,
    }
    return mail_data
