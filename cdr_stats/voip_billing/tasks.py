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
from celery.task import Task
from cdr.import_cdr_freeswitch_mongodb import create_analytic,\
    calculate_call_cost
from bson import ObjectId
import logging
import time

cdr_data = settings.DBCON[settings.MONGO_CDRSTATS['CDR_COMMON']]


def _rebilling_call(voipplan_id, call):
    """Perform call re-billing

    **Attributes**:

        * ``voipplan_id`` - frontend/cdr_graph_concurrent_calls.html
        * ``call`` - ConcurrentCallForm
        * ``cdr_data`` - MONGO_CDRSTATS['CDR_COMMON'] (cdr_common collection)

    **Logic Description**:

        get call record & voipplan_id to re-bill
    """
    new_rate =\
        calculate_call_cost(voipplan_id, call['destination_number'], call['billsec'])

    # Update cdr_common buy_cost/sell_cost
    cdr_data.update({"_id": ObjectId(call['_id'])}, {
        "$set": {
            "buy_rate": new_rate['buy_rate'],
            "buy_cost": new_rate['buy_cost'],
            "sell_rate": new_rate['sell_rate'],
            "sell_cost": new_rate['sell_cost']
        }
    })
    # cdr_data.find_one({"_id": ObjectId(call['_id'])})
    return True


class RebillingTask(Task):
    """
    Re-billing for VoIPCall

    **Usage**:

        RebillingTask.delay(start_date, end_date, voipplan_id)
    """

    def run(self, calls_kwargs, voipplan_id, **kwargs):
        logging.debug("Start re-billing calls.")

        call_rebill = cdr_data.find(calls_kwargs)

        for call in call_rebill:
            _rebilling_call(voipplan_id, call)

        logging.debug("End re-billing calls.")
        return True


class ReaggregateTask(Task):
    """
    Re-aggregate voip calls for daily/monthly analytics

    **Usage**:

        ReaggregateTask.delay(start_date, end_date)
    """

    def run(self, daily_query_var, monthly_query_var, call_kwargs, **kwargs):
        logging.debug("About to re-aggregate voip calls for daily/monthly analytics.")

        #1) remove daily/monthly aggregate
        daily_data = settings.DBCON[settings.MONGO_CDRSTATS['DAILY_ANALYTIC']]
        daily_data.remove(daily_query_var)
        monthly_data = settings.DBCON[settings.MONGO_CDRSTATS['MONTHLY_ANALYTIC']]
        monthly_data.remove(monthly_query_var)

        #2) Re-create daily/monthly analytic
        PAGE_SIZE = 1000
        record_count = cdr_data.find(call_kwargs).count()
        total_pages = int(record_count / PAGE_SIZE) + 1 if (record_count % PAGE_SIZE) != 0 else 0

        for PAGE_NUMBER in range(1, total_pages + 1):

            SKIP_NO = PAGE_SIZE * (PAGE_NUMBER - 1)
            # create analytic in chunks
            rebilled_call = cdr_data.find(call_kwargs).skip(SKIP_NO).limit(PAGE_SIZE)

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
