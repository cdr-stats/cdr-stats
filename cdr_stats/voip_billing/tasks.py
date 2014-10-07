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
from celery.task import Task
from cdr.import_cdr_freeswitch_mongodb import create_analytic,\
    calculate_call_cost
from mongodb_connection import mongodb
from bson import ObjectId
import logging
import time


def rebill_call(voipplan_id, call):
    """Perform call re-billing

    **Attributes**:

        * ``voipplan_id`` - frontend/cdr_graph_concurrent_calls.html
        * ``call`` - ConcurrentCallForm
        * ``mongodb.cdr_common`` - cdr_common collection

    **Logic Description**:

        get call record & voipplan_id to re-bill
    """
    new_rate = calculate_call_cost(voipplan_id, call['destination_number'], call['billsec'])

    # Update cdr_common buy_cost/sell_cost
    mongodb.cdr_common.update({"_id": ObjectId(call['_id'])}, {
        "$set": {
            "buy_rate": new_rate['buy_rate'],
            "buy_cost": new_rate['buy_cost'],
            "sell_rate": new_rate['sell_rate'],
            "sell_cost": new_rate['sell_cost']
        }
    })
    # mongodb.cdr_common.find_one({"_id": ObjectId(call['_id'])})
    return True


class RebillingTask(Task):
    """
    Re-billing for VoIPCall

    **Usage**:

        RebillingTask.delay(calls_kwargs, voipplan_id)
    """

    def run(self, calls_kwargs, voipplan_id, **kwargs):
        logging.debug("Start re-billing calls.")

        if not mongodb.cdr_common:
            logging.error("Error mongodb connection")
            return False

        call_rebill = mongodb.cdr_common.find(calls_kwargs)

        for call in call_rebill:
            rebill_call(voipplan_id, call)

        logging.debug("End re-billing calls.")
        return True


class ReaggregateTask(Task):
    """
    Re-aggregate voip calls for daily/monthly analytics

    **Usage**:

        ReaggregateTask.delay(daily_kwargs, monthly_kwargs, call_kwargs)
    """

    def run(self, daily_kwargs, monthly_kwargs, call_kwargs, **kwargs):
        logging.debug("About to re-aggregate voip calls for daily/monthly analytics.")

        if not mongodb.daily_analytic:
            logging.error("Error mongodb connection")
            return False

        #1) remove daily/monthly aggregate
        mongodb.daily_analytic.remove(daily_kwargs)
        mongodb.monthly_analytic.remove(monthly_kwargs)

        #2) Re-create daily/monthly analytic
        PAGE_SIZE = 1000
        record_count = mongodb.cdr_common.find(call_kwargs).count()
        total_pages = int(record_count / PAGE_SIZE) + 1 if (record_count % PAGE_SIZE) != 0 else 0

        for PAGE_NUMBER in range(1, total_pages + 1):

            SKIP_NO = PAGE_SIZE * (PAGE_NUMBER - 1)
            # create analytic in chunks
            rebilled_call = mongodb.cdr_common.find(call_kwargs).skip(SKIP_NO).limit(PAGE_SIZE)

            for call in rebilled_call:
                start_uepoch = call['start_uepoch']
                switch_id = int(call['switch_id'])
                country_id = call['country_id']
                accountcode = call['accountcode']
                hangup_cause_id = call['hangup_cause_id']
                duration = call['duration']
                buy_cost = call['buy_cost']
                sell_cost = call['sell_cost']

                date_start_uepoch = int(time.mktime(start_uepoch.timetuple()))

                create_analytic(str(date_start_uepoch),
                    start_uepoch, switch_id, country_id, accountcode,
                    hangup_cause_id, duration, buy_cost, sell_cost)

        logging.debug("Done re-aggregate")
        return True
