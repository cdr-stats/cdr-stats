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
from cdr.import_cdr_freeswitch_mongodb import common_function_to_create_analytic
import logging
import time

cdr_data = settings.DBCON[settings.MONGO_CDRSTATS['CDR_COMMON']]

class VoIPbilling(Task):
    """
    Billing for VoIPCall
    """

    def run(self, voipcall_id, voipplan_id, **kwargs):
        logging.debug("About to bill a message.")

        #TODO : rewrite task for billing or do we need task

        #logging.debug("Done billing call.")
        return ''


class Reaggregate_call(Task):
    """
    Re-aggregate voip calls for daily/monthly analytics
    """

    def run(self, start_date, end_date, **kwargs):
        logging.debug("About to re-aggregate voip calls for daily/monthly analytics.")

        #1) remove daily/monthly aggregate
        daily_query_var = {}
        daily_query_var['metadata.date'] = {'$gte': start_date.strftime('%Y-%m-%d'),
                                            '$lt': end_date.strftime('%Y-%m-%d')}
        daily_data = settings.DBCON[settings.MONGO_CDRSTATS['DAILY_ANALYTIC']]
        daily_data.remove(daily_query_var)

        monthly_query_var = {}
        monthly_query_var['metadata.date'] = {'$gte': start_date.strftime('%Y-%m'),
                                              '$lt': end_date.strftime('%Y-%m')}
        monthly_data = settings.DBCON[settings.MONGO_CDRSTATS['MONTHLY_ANALYTIC']]
        monthly_data.remove(monthly_query_var)

        #2) Recreate daily/monthly analytic
        kwargs = {}
        kwargs['start_uepoch'] = {'$gte': start_date, '$lt': end_date}
        rebilled_call  = cdr_data.find(kwargs)
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

            common_function_to_create_analytic(str(date_start_uepoch),
                start_uepoch, switch_id, country_id, accountcode,
                hangup_cause_id, duration, buy_cost, sell_cost)

        logging.debug("Done re-aggregate")
        return True