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
from voip_billing.rate_engine import calculate_call_cost
from cdr.models import CDR
import logging


class RebillingTask(Task):

    """
    Re-billing for VoIPCall

    **Usage**:

        RebillingTask.delay(calls_kwargs, voipplan_id)
    """

    def run(self, calls_kwargs, voipplan_id, **kwargs):
        logging.debug("Start Calls Rebilling...")

        cdr_rebill = CDR.objects.filter(calls_kwargs)
        for cdr in cdr_rebill:
            new_rate = calculate_call_cost(voipplan_id, cdr['destination_number'], cdr['billsec'])
            cdr.buy_rate = new_rate['buy_rate']
            cdr.buy_cost = new_rate['buy_cost']
            cdr.sell_rate = new_rate['sell_rate']
            cdr.sell_cost = new_rate['sell_cost']
            cdr.save()

        logging.debug("End Calls Rebilling...")
        return True
