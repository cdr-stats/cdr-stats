from celery.task import Task
from voip_billing.models import *
from voip_report.models import *
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
