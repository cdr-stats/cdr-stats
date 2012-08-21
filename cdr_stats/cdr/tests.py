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
from django.contrib.auth.models import User
from django.test import TestCase
from django.core.management import call_command
from common.utils import BaseAuthenticatedClient
from cdr.models import Switch, HangupCause
from cdr.forms import CdrSearchForm,\
                      CountryReportForm,\
                      CdrOverviewForm,\
                      CompareCallSearchForm,\
                      ConcurrentCallForm,\
                      SwitchForm,\
                      WorldForm,\
                      EmailReportForm
from cdr.tasks import sync_cdr_pending, get_channels_info
from cdr.views import cdr_view, cdr_dashboard, cdr_overview,\
                      cdr_report_by_hour, cdr_concurrent_calls,\
                      cdr_realtime, cdr_country_report, mail_report,\
                      world_map_view, index, cdr_detail
from bson.objectid import ObjectId
from datetime import datetime, timedelta


class CdrAdminInterfaceTestCase(BaseAuthenticatedClient):
    """Test cases for Cdr-Stats Admin Interface."""

    def test_admin_switch_list(self):
        """Test Function to check admin switch list"""
        response = self.client.get('/admin/cdr/switch/')
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_switch_add(self):
        """Test Function to check admin switch add"""
        response = self.client.get('/admin/cdr/switch/add/')
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.post(
            '/admin/cdr/switch/add/',
            data={
                "name": "localhost",
                "ipaddress": "127.0.0.1",
                }, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_admin_switch_import_cdr(self):
        """Test Function to check admin cdr import"""
        response = self.client.post('/admin/cdr/switch/import_cdr/',
                {'switch_id': 1,})
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_hangupcause_list(self):
        """Test Function to check admin hangupcause list"""
        response = self.client.get('/admin/cdr/hangupcause/')
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_hangupcause_add(self):
        """Test Function to check admin hangupcause add"""
        response = self.client.get('/admin/cdr/hangupcause/add/')
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.post(
            '/admin/cdr/hangupcause/add/',
            data={
                "code": "1",
                "enumeration": "UNALLOCATED_NUMBER",
                })
        self.assertEqual(response.status_code, 200)


class CdrStatsCustomerInterfaceTestCase(BaseAuthenticatedClient):
    """Test cases for Cdr-Stats Customer Interface."""

    fixtures = ['auth_user.json', 'switch.json']

    def test_index(self):
        """Test Function to check customer index page"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cdr/index.html')

        request = self.factory.get('/')
        request.user = self.user
        request.session = {}
        response = index(request)
        self.assertEqual(response.status_code, 200)


    def test_dashboard(self):
        """Test Function to check customer dashboard"""
        response = self.client.get('/dashboard/')
        self.assertTemplateUsed(response, 'cdr/cdr_dashboard.html')
        self.assertTrue(response.context['form'], SwitchForm())
        self.assertEqual(response.status_code, 200)

        request = self.factory.get('/dashboard/')
        request.user = self.user
        request.session = {}
        response = cdr_dashboard(request)
        self.assertEqual(response.status_code, 200)

        data = {'switch_id': 1}
        response = self.client.post('/dashboard/', data)
        self.assertTrue(response.context['form'],
                        SwitchForm(data))
        self.assertTrue('total_calls' in response.context)
        self.assertEqual(response.status_code, 200)

        request = self.factory.post('/dashboard/', data)
        request.user = self.user
        request.session = {}
        response = cdr_dashboard(request)
        self.assertEqual(response.status_code, 200)

    def test_cdr_view(self):
        """Test Function to check cdr_view"""
        response = self.client.get('/cdr_view/')
        self.assertTrue(response.context['form'], CdrSearchForm())
        self.assertTemplateUsed(response, 'cdr/cdr_view.html')
        self.assertEqual(response.status_code, 200)

        request = self.factory.get('/cdr_view/')
        request.user = self.user
        request.session = {}
        response = cdr_view(request)
        self.assertEqual(response.status_code, 200)

        data = {'switch_id': 1,
                'from_date': datetime.now().strftime("%Y-%m-%d"),
                'to_date': datetime.now().strftime("%Y-%m-%d"),
                'destination': '91',
                'destination_type': 1,
                'accountcode': '123',
                'caller': 'abc',
                'duration': '30',
                'duration_type': '>',
                'direction': 'INBOUND',
                'hangup_cause': 1,
                'result': 1,
                'records_per_page': 10}
        response = self.client.post('/cdr_view/', data)
        self.assertTrue(response.context['form'], CdrSearchForm(data))
        self.assertEqual(response.status_code, 200)

        request = self.factory.post('/cdr_view/', data)
        request.user = self.user
        request.session = {}
        response = cdr_view(request)
        self.assertEqual(response.status_code, 200)

    def test_cdr_detail(self):
        """Test Function to check cdr_detail"""
        request = self.factory.post('/cdr_detail/')
        request.user = self.user
        request.session = {}
        response = cdr_detail(request, ObjectId('503368721d41c818ee000000'), 1)
        self.assertEqual(response.status_code, 200)

    def test_cdr_overview(self):
        """Test Function to check cdr_overview"""
        response = self.client.get('/cdr_overview/')
        self.assertTrue(response.context['form'], CdrOverviewForm())
        self.assertTemplateUsed(response, 'cdr/cdr_overview.html')
        self.assertEqual(response.status_code, 200)

        request = self.factory.get('/cdr_overview/')
        request.user = self.user
        request.session = {}
        response = cdr_overview(request)
        self.assertEqual(response.status_code, 200)

        data = {'switch_id': 1,
                'from_date': datetime.now().strftime("%Y-%m-%d"),
                'to_date': datetime.now().strftime("%Y-%m-%d"),}
        response = self.client.post('/cdr_overview/', data)
        self.assertTrue(response.context['form'], CdrOverviewForm(data))
        self.assertEqual(response.status_code, 200)

        request = self.factory.post('/cdr_overview/', data)
        request.user = self.user
        request.session = {}
        response = cdr_overview(request)
        self.assertEqual(response.status_code, 200)

    def test_cdr_hourly_report(self):
        """Test Function to check cdr hourly report"""
        response = self.client.get('/hourly_report/')
        self.assertTrue(response.context['form'], CompareCallSearchForm())
        self.assertTemplateUsed(response, 'cdr/cdr_report_by_hour.html')
        self.assertEqual(response.status_code, 200)

        request = self.factory.get('/hourly_report/')
        request.user = self.user
        request.session = {}
        response = cdr_report_by_hour(request)
        self.assertEqual(response.status_code, 200)

        data = {'switch_id': 1,
                'from_date': datetime.now().strftime("%Y-%m-%d"),
                'comp_days': 2,
                'graph_view': 1,
                'check_days': 2,
                'result': 'min'}
        response = self.client.post('/hourly_report/', data)
        self.assertTrue(response.context['form'], CompareCallSearchForm(data))
        self.assertEqual(response.status_code, 200)

        request = self.factory.post('/hourly_report/', data)
        request.user = self.user
        request.session = {}
        response = cdr_report_by_hour(request)
        self.assertEqual(response.status_code, 200)

    def test_cdr_concurrent_calls(self):
        """Test Function to check concurrent calls"""
        response = self.client.get('/cdr_concurrent_calls/')
        self.assertTrue(response.context['form'], ConcurrentCallForm())
        self.assertTemplateUsed(response, 'cdr/cdr_graph_concurrent_calls.html')
        self.assertEqual(response.status_code, 200)

        request = self.factory.get('/cdr_concurrent_calls/')
        request.user = self.user
        request.session = {}
        response = cdr_concurrent_calls(request)
        self.assertEqual(response.status_code, 200)

        data = {'switch_id': 1,
                'from_date': datetime.now().strftime("%Y-%m-%d")}
        response = self.client.post('/cdr_concurrent_calls/', data)
        self.assertTrue(response.context['form'], ConcurrentCallForm(data))
        self.assertEqual(response.status_code, 200)

        request = self.factory.post('/cdr_concurrent_calls/', data)
        request.user = self.user
        request.session = {}
        response = cdr_concurrent_calls(request)
        self.assertEqual(response.status_code, 200)

    def test_cdr_realtime(self):
        """Test Function to check realtime calls"""
        response = self.client.get('/cdr_realtime/')
        self.assertTrue(response.context['form'], SwitchForm())
        self.assertTemplateUsed(response, 'cdr/cdr_graph_realtime.html')
        self.assertEqual(response.status_code, 200)

        request = self.factory.get('/cdr_realtime/')
        request.user = self.user
        request.session = {}
        response = cdr_realtime(request)
        self.assertEqual(response.status_code, 200)

        data = {'switch_id': 1}
        response = self.client.post('/cdr_realtime/', data)
        self.assertTrue(response.context['form'], SwitchForm(data))
        self.assertEqual(response.status_code, 200)

        request = self.factory.post('/cdr_realtime/', data)
        request.user = self.user
        request.session = {}
        response = cdr_realtime(request)
        self.assertEqual(response.status_code, 200)

    def test_cdr_country_report(self):
        """Test Function to check country report"""
        response = self.client.get('/country_report/')
        self.assertTrue(response.context['form'], CountryReportForm())
        self.assertTemplateUsed(response, 'cdr/cdr_country_report.html')
        self.assertEqual(response.status_code, 200)

        request = self.factory.get('/country_report/')
        request.user = self.user
        request.session = {}
        response = cdr_country_report(request)
        self.assertEqual(response.status_code, 200)

        data = {'switch_id': 1,
                'from_date': datetime.now().strftime("%Y-%m-%d"),
                'to_date': datetime.now().strftime("%Y-%m-%d"),}
        response = self.client.post('/country_report/', data)
        self.assertTrue(response.context['form'], CountryReportForm(data))
        self.assertEqual(response.status_code, 200)

        request = self.factory.post('/country_report/', data)
        request.user = self.user
        request.session = {}
        response = cdr_country_report(request)
        self.assertEqual(response.status_code, 200)

    def test_cdr_mail_report(self):
        """Test Function to check mail report"""
        response = self.client.get('/mail_report/')
        self.assertTrue(response.context['form'], EmailReportForm(self.user))
        self.assertTemplateUsed(response, 'cdr/cdr_mail_report.html')
        self.assertEqual(response.status_code, 200)

        request = self.factory.get('/mail_report/')
        request.user = self.user
        request.session = {}
        response = mail_report(request)
        self.assertEqual(response.status_code, 200)

    def test_cdr_world_map(self):
        """Test Function to check world map"""
        response = self.client.get('/world_map/')
        self.assertTemplateUsed(response, 'cdr/world_map.html')
        self.assertTrue(response.context['form'], WorldForm())
        self.assertEqual(response.status_code, 200)

        request = self.factory.get('/world_map/')
        request.user = self.user
        request.session = {}
        response = world_map_view(request)
        self.assertEqual(response.status_code, 200)


        data = {'switch_id': 1,
                'from_date': datetime.now().strftime("%Y-%m-%d"),
                'to_date': datetime.now().strftime("%Y-%m-%d"),}
        response = self.client.post('/world_map/', data)
        self.assertTrue(response.context['form'], WorldForm(data))
        self.assertEqual(response.status_code, 200)

        request = self.factory.post('/world_map/', data)
        request.user = self.user
        request.session = {}
        response = world_map_view(request)
        self.assertEqual(response.status_code, 200)


class CdrStatsTaskTestCase(TestCase):

    fixtures = ['auth_user.json']

    def test_get_channels_info(self):
        """Test task : get_channels_info"""
        delta = timedelta(seconds=1)
        self.assertEqual(get_channels_info().timedelta_seconds(delta), 1)

    def test_sync_cdr_pending(self):
        """Test task : sync_cdr_pending"""
        delta = timedelta(seconds=1)
        self.assertEqual(sync_cdr_pending().timedelta_seconds(delta), 1)


class CdrModelTestCase(TestCase):
    """Test Switch, Alarm, HangupCause models"""

    fixtures = ['hangup_cause.json']

    def setUp(self):
        """Create model object"""
        # Switch model
        self.switch = Switch(
            name='localhost',
            ipaddress='127.0.0.1'
            )
        self.switch.save()

        self.hangupcause = HangupCause(
            code=700,
            enumeration='UNALLOCATED_NUMBER'
            )
        self.hangupcause.save()


    def test_model_value(self):
        """Create model object value"""
        self.assertEquals(self.switch.name, 'localhost')
        self.assertEquals(self.hangupcause.enumeration, 'UNALLOCATED_NUMBER')

    def tearDown(self):
        """Delete created object"""
        self.switch.delete()
        self.hangupcause.delete()

    def test_mgt_command(self):
        # Test mgt command
        call_command("generate_cdr",
            "--number-cdr=100 --delta-day=0 --duration=10")

        call_command("sync_cdr_freeswitch", "--apply-index")

        call_command("sync_cdr_asterisk", "--apply-index")

        call_command("generate_concurrent_call", "--delta-day=0")

