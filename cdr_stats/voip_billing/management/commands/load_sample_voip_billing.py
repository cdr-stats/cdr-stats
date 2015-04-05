# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.core.management import call_command
import inspect
import os


class Command(BaseCommand):
    args = ' '
    help = "Load sample data for VoIP Billing\n"\
           "---------------------------------\n"\
           "python manage.py load_sample_voip_billing"

    option_list = BaseCommand.option_list

    def handle(self, *args, **options):
        script_directory = os.path.dirname(inspect.getfile(inspect.currentframe()))

        fixture_list = [
            # '1_example_user.json',
            '2_example_voipplan.json',
            '3_example_voipcarrierplan.json',
            '4_example_voipcarrier_rate.json',
            '5_example_voipretailplan.json',
            '6_example_voipretailrate.json',
            '7_example_voipplan_voipretail_plan.json',
            '8_example_voipplan_voipcarrierplan.json',
            # 'voip_billing.json',
        ]

        i = 0
        for fix in fixture_list:
            i += 1
            fixture_file = '%s/../../fixtures/%s' % (script_directory, fix)
            print "%d) This fixture is going to be loaded: %s" % (i, fixture_file)
            call_command('loaddata', fixture_file)
