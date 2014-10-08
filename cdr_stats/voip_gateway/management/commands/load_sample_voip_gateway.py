# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.core.management import call_command
import inspect
import os


class Command(BaseCommand):
    args = ' '
    help = "Load Sample VoIP Gateway\n"

    option_list = BaseCommand.option_list

    def handle(self, *args, **options):
        script_directory = os.path.dirname(inspect.getfile(inspect.currentframe()))

        fixture_list = [
            'voip_gateway.json',
            'voip_provider.json',
        ]

        i = 0
        for fix in fixture_list:
            i += 1
            fixture_file = '%s/../../fixtures/%s' % (script_directory, fix)
            print "%d) This fixture is going to be loaded: %s" % (i, fixture_file)
            call_command('loaddata', fixture_file)
