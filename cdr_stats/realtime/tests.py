#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2015 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#
from django.contrib.auth.models import User
from django.core.management import call_command
from django.conf import settings
from django.test import TestCase
from django_lets_go.utils import BaseAuthenticatedClient
from cdr.models import Switch, HangupCause
from cdr.forms import CdrSearchForm, CountryReportForm, CompareCallSearchForm,\
    ConcurrentCallForm, SwitchForm, WorldForm, EmailReportForm
from cdr.tasks import sync_cdr_pending, get_channels_info
from cdr.views import cdr_view, cdr_dashboard, cdr_overview, cdr_daily_comparison,\
    cdr_concurrent_calls, cdr_realtime, cdr_country_report, mail_report, world_map_view,\
    cdr_detail
from cdr.functions_def import get_switch_list, get_hangupcause_name,\
    get_hangupcause_id, get_country_id_prefix
from cdr.templatetags.cdr_tags import hangupcause_name_with_title, mongo_id
from bson.objectid import ObjectId
from datetime import datetime

csv_file = open(
    settings.APPLICATION_DIR + '/cdr/fixtures/import_cdr.txt', 'r'
)


class CdrStatsCustomerInterfaceTestCase(BaseAuthenticatedClient):
    """Test cases for Cdr-Stats Customer Interface."""

    fixtures = ['auth_user.json', 'switch.json',
                'country_dialcode.json', 'hangup_cause.json',
                'notice_type.json', 'notification.json',
                'voip_gateway.json', 'voip_provider.json',
                'voip_billing.json', 'user_profile.json']

    #def test_mgt_command(self):
    #    # Test mgt command
    #    call_command('generate_cdr',
    #        '--number-cdr=10', '--delta-day=1', '--duration=10')
    #    call_command('generate_cdr',
    #        '--number-cdr=10', '--delta-day=0', '--duration=0')
    #    call_command('generate_cdr', '--number-cdr=10', '--delta-day=0')
    #    call_command('generate_cdr', '--number-cdr=10')
    #    call_command('sync_cdr_freeswitch', '--apply-index')
    #    call_command('sync_cdr_freeswitch')
    #    #call_command('sync_cdr_asterisk', '--apply-index')
    #    #call_command('sync_cdr_asterisk')

    def test_cdr_concurrent_calls(self):
        """Test Function to check concurrent calls"""
        response = self.client.get('/concurrent_calls/')
        ##self.assertTemplateUsed(response, 'cdr/graph_concurrent_calls.html')
        self.assertEqual(response.status_code, 200)

        request = self.factory.get('/concurrent_calls/')
        request.user = self.user
        request.session = {}
        response = cdr_concurrent_calls(request)
        self.assertEqual(response.status_code, 200)

        data = {'switch_id': 1,
                'from_date': datetime.now().strftime("%Y-%m-%d")}
        response = self.client.post('/concurrent_calls/', data)
        #self.assertTrue(response.context['form'], ConcurrentCallForm(data))
        self.assertEqual(response.status_code, 200)

        request = self.factory.post('/concurrent_calls/', data)
        request.user = self.user
        request.session = {}
        response = cdr_concurrent_calls(request)
        self.assertEqual(response.status_code, 200)

    def test_cdr_realtime(self):
        """Test Function to check realtime calls"""
        response = self.client.get('/realtime/')
        #self.assertTemplateUsed(response, 'cdr/graph_realtime.html')
        self.assertEqual(response.status_code, 200)

        request = self.factory.get('/realtime/')
        request.user = self.user
        request.session = {}
        response = cdr_realtime(request)
        self.assertEqual(response.status_code, 200)

        data = {'switch_id': 1}
        response = self.client.post('/realtime/', data)
        self.assertEqual(response.status_code, 200)

        request = self.factory.post('/realtime/', data)
        request.user = self.user
        request.session = {}
        response = cdr_realtime(request)
        self.assertEqual(response.status_code, 200)


class CdrStatsTaskTestCase(TestCase):

    fixtures = ['auth_user.json', 'switch.json',
                'country_dialcode.json', 'hangup_cause.json',
                'voip_gateway.json', 'voip_provider.json',
                'voip_billing.json', 'user_profile.json']

    def test_get_channels_info(self):
        """Test task : get_channels_info"""
        #result = get_channels_info().run()
        #self.assertTrue(result)
