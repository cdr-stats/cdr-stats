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

from mongodb_connection import mongodb
from cdr.helpers import print_shell
import datetime
import random

random.seed()


def apply_index(shell):
    """Apply index on cdr-stats mongodb collections"""
    mongodb.cdr_common.ensure_index([
        ("start_uepoch", -1),
        ("caller_id_number", 1),
        ("destination_number", 1),
        ("duration", 1),
        ("billsec", 1),
        ("hangup_cause_id", 1)])
    mongodb.daily_analytic.ensure_index([
        ("metadata.date", -1),
        ("metadata.switch_id", 1),
        ("metadata.country_id", 1),
        ("metadata.accountcode", 1)])
    mongodb.monthly_analytic.ensure_index([
        ("metadata.date", -1),
        ("metadata.switch_id", 1),
        ("metadata.country_id", 1),
        ("metadata.accountcode", 1)])

    print_shell(shell, "Index applied on collection")
    return True


def create_daily_analytic(daily_date, switch_id, country_id,
                          accountcode, hangup_cause_id, duration,
                          buy_cost, sell_cost):
    """Create mongodb.daily_analytic"""
    print (switch_id, accountcode, country_id, hangup_cause_id)
    if not country_id:
        country_id = 0
    id_daily = daily_date.strftime('%Y%m%d') + "/%d/%s/%d/%d" % \
        (switch_id, accountcode, country_id, hangup_cause_id)

    hour = daily_date.hour
    minute = daily_date.minute
    # Get a datetime that only include date info
    d = datetime.datetime.combine(daily_date.date(), datetime.time.min)

    mongodb.daily_analytic.update(
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

                # for billing
                "buy_cost_daily": float(buy_cost),
                "buy_cost_hourly.%d" % (hour,): float(buy_cost),
                "buy_cost_minute.%d.%d" % (hour, minute,): float(buy_cost),

                "sell_cost_daily": float(sell_cost),
                "sell_cost_hourly.%d" % (hour,): float(sell_cost),
                "sell_cost_minute.%d.%d" % (hour, minute,): float(sell_cost),
            }
        }, upsert=True)

    return True


def create_monthly_analytic(daily_date, start_uepoch, switch_id,
                            country_id, accountcode, duration,
                            buy_cost, sell_cost):
    """Create mongodb.daily_analytic"""
    # Get a datetime that only include year-month info
    d = datetime.datetime.strptime(str(start_uepoch)[:7], "%Y-%m")
    if not country_id:
        country_id = 0

    id_monthly = daily_date.strftime('%Y%m') + "/%d/%s/%d" %\
        (switch_id, accountcode, country_id)

    mongodb.monthly_analytic.update(
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

                # for billing
                "buy_cost_monthly": float(buy_cost),
                "sell_cost_monthly": float(sell_cost),
            }
        }, upsert=True)

    return True


def generate_global_cdr_record(switch_id, caller_id_number, caller_id_name, dest_number,
                               duration, billsec, hangup_cause_id, accountcode, direction,
                               uuid, remote_media_ip, start_uepoch, answer_uepoch, end_uepoch,
                               mduration, billmsec, read_codec, write_codec, cdr_type,
                               cdr_object_id, country_id, authorized,
                               buy_rate, buy_cost, sell_rate, sell_cost):
    """
    Common function to create global cdr record
    """
    cdr_record = {
        'switch_id': switch_id,
        'caller_id_number': caller_id_number,
        'caller_id_name': caller_id_name,
        'destination_number': dest_number,
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

        # For billing
        'buy_rate': buy_rate,
        'buy_cost': buy_cost,
        'sell_rate': sell_rate,
        'sell_cost': sell_cost,
    }
    return cdr_record


def create_analytic(date_start_uepoch, start_uepoch, switch_id,
                    country_id, accountcode, hangup_cause_id, duration,
                    buy_cost, sell_cost):
    """
    Common function to create mongodb.daily_analytic, mongodb.monthly_analytic
    """
    # mongodb.daily_analytic
    daily_date = datetime.datetime.fromtimestamp(int(str(date_start_uepoch)[:10]))

    # insert daily analytic record
    create_daily_analytic(
        daily_date, switch_id, country_id, accountcode,
        hangup_cause_id, duration, buy_cost, sell_cost)

    # mongodb.monthly_analytic
    # insert monthly analytic record
    create_monthly_analytic(daily_date, start_uepoch, switch_id, country_id,
                            accountcode, duration, buy_cost, sell_cost)
    return True
