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
from celery.task import Task
from voip_report.models import VoIPCall_Report
import logging


class VoIPbilling(Task):
    """
    Billing for VoIPCall
    """

    def run(self, voipcall_id, voipplan_id, **kwargs):
        logging.debug("About to bill a message.")

        voipcall_report = VoIPCall_Report()

        # Call is getting billed
        response = voipcall_report._bill(voipcall_id, voipplan_id)

        logging.debug("Done billing call.")
        return response
