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
import logging


class VoIPbilling(Task):
    """
    Billing for VoIPCall
    """

    def run(self, voipcall_id, voipplan_id, **kwargs):
        logging.debug("About to bill a message.")

        #TODO : rewrite task for billing     

        #logging.debug("Done billing call.")
        return response
