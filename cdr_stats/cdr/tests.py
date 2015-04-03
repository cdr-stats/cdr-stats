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
    cdr_country_report, mail_report, world_map_view,\
    cdr_detail
from cdr.functions_def import get_hangupcause_name,\
    get_hangupcause_id, get_country_id_prefix
from cdr.templatetags.cdr_tags import hangupcause_name_with_title
from datetime import datetime

csv_file = open(
    settings.APPLICATION_DIR + '/cdr/fixtures/import_cdr.txt', 'r'
)


class CdrAdminInterfaceTestCase(BaseAuthenticatedClient):

    """Test cases for Cdr-Stats Admin Interface."""

    fixtures = ['auth_user.json', 'switch.json']

    def test_admin_switch_list(self):
        """Test Function to check admin switch list"""
        response = self.client.get('/admin/cdr/switch/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/cdr/switch/cdr_view/')
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
            },
            follow=True)
        self.assertEqual(response.status_code, 200)

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
        self.assertEqual(response.status_code, 302)


class CdrStatsCustomerInterfaceTestCase(BaseAuthenticatedClient):

    """Test cases for Cdr-Stats Customer Interface."""

    fixtures = ['auth_user.json', 'switch.json',
                'country_dialcode.json', 'hangup_cause.json',
                'notice_type.json', 'notification.json',
                'voip_gateway.json', 'voip_provider.json',
                'voip_billing.json', 'user_profile.json']

    # def test_mgt_command(self):
    # Test mgt command
    #    call_command('generate_cdr',
    #        '--number-cdr=10', '--delta-day=1', '--duration=10')
    #    call_command('generate_cdr',
    #        '--number-cdr=10', '--delta-day=0', '--duration=0')
    #    call_command('generate_cdr', '--number-cdr=10', '--delta-day=0')
    #    call_command('generate_cdr', '--number-cdr=10')
    #    call_command('sync_cdr_freeswitch', '--apply-index')
    #    call_command('sync_cdr_freeswitch')
    # call_command('sync_cdr_asterisk', '--apply-index')
    # call_command('sync_cdr_asterisk')

    def test_dashboard(self):
        """Test Function to check customer dashboard"""
        response = self.client.get('/dashboard/')
        #self.assertTemplateUsed(response, 'cdr/dashboard.html')
        self.assertEqual(response.status_code, 200)

        request = self.factory.get('/dashboard/')
        request.user = self.user
        request.session = {}
        response = cdr_dashboard(request)
        self.assertEqual(response.status_code, 200)

        data = {'switch_id': 1}
        response = self.client.post('/dashboard/', data)
        #self.assertTrue(response.context['form'], SwitchForm(data))
        #self.assertTrue('total_calls' in response.context)
        self.assertEqual(response.status_code, 200)

        request = self.factory.post('/dashboard/', data)
        request.user = self.user
        request.session = {}
        response = cdr_dashboard(request)
        self.assertEqual(response.status_code, 200)

    def test_cdr_view(self):
        """Test Function to check cdr_view"""
        response = self.client.get('/cdr_view/')
        #self.assertTrue(response.context['form'], CdrSearchForm())
        #self.assertTemplateUsed(response, 'cdr/list.html')
        self.assertEqual(response.status_code, 200)

        request = self.factory.get('/cdr_view/')
        request.user = self.user
        request.session = {}
        response = cdr_view(request)
        self.assertEqual(response.status_code, 200)

        data = {
            'switch_id': 1,
            'from_date': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'to_date': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'destination': '91',
            'destination_type': 1,
            'accountcode': '123',
            'caller': 'abc',
            'hangup_cause_id': 1,
            'result': 1,
            'records_per_page': 10
        }
        response = self.client.post('/cdr_view/', data)
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/cdr_view/?page=1')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/cdr_view/?page=1&sort_by=-caller_id_number')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/cdr_view/?page=1&sort_by=caller_id_number')
        self.assertEqual(response.status_code, 200)

        request = self.factory.post('/cdr_view/', data)
        request.user = self.user
        request.session = {}
        response = cdr_view(request)
        self.assertEqual(response.status_code, 200)

        now = datetime.today()
        start_date = datetime(now.year, now.month, 1, 0, 0, 0, 0)
        end_date = datetime(now.year, now.month, now.day, 23, 59, 59, 99999)
        request.session['query_var'] = {
            'start_uepoch': {'$gte': start_date, '$lt': end_date}
        }

        #response = self.client.get('/cdr_export_csv/?format=csv')
        #self.assertEqual(response.status_code, 200)

        #response = self.client.get('/cdr_export_csv/?format=xls')
        #self.assertEqual(response.status_code, 200)

        #response = self.client.get('/cdr_export_csv/?format=json')
        #self.assertEqual(response.status_code, 200)

    def test_cdr_detail(self):
        """Test Function to check cdr_detail"""
        request = self.factory.post('/cdr_detail/')
        request.user = self.user
        request.session = {}
        #self.assertEqual(response.status_code, 200)

    def test_cdr_overview(self):
        """Test Function to check cdr_overview"""
        response = self.client.get('/overview/')
        #self.assertTrue(response.context['form'], CdrOverviewForm())
        #self.assertTemplateUsed(response, 'cdr/overview.html')
        self.assertEqual(response.status_code, 200)

        request = self.factory.get('/overview/')
        request.user = self.user
        request.session = {}
        response = cdr_overview(request)
        self.assertEqual(response.status_code, 200)

        data = {'switch_id': 1,
                'from_date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'to_date': datetime.now().strftime("%Y-%m-%d %H%M")}
        response = self.client.post('/overview/', data)
        #self.assertTrue(response.context['form'], CdrOverviewForm(data))
        self.assertEqual(response.status_code, 200)

        request = self.factory.post('/overview/', data)
        request.user = self.user
        request.session = {}
        response = cdr_overview(request)
        self.assertEqual(response.status_code, 200)

        data = {'switch_id': 0,
                'from_date': '',
                'to_date': ''}
        request = self.factory.post('/overview/', data)
        request.user = self.user
        request.session = {}
        response = cdr_overview(request)
        self.assertEqual(response.status_code, 200)

    def test_cdr_hourly_report(self):
        """Test Function to check cdr hourly report"""
        response = self.client.get('/daily_comparison/')
        #self.assertTemplateUsed(response, 'cdr/daily_comparison.html')
        self.assertEqual(response.status_code, 200)

        request = self.factory.get('/daily_comparison/')
        request.user = self.user
        request.session = {}
        response = cdr_daily_comparison(request)
        self.assertEqual(response.status_code, 200)

        data = {'switch_id': 0,
                'from_date': datetime.now().strftime("%Y-%m-%d"),
                'compare_days': 2,
                'graph_view': 1,
                'compare_type': 1}
        response = self.client.post('/daily_comparison/', data)
        #self.assertTrue(response.context['form'], CompareCallSearchForm(data))
        self.assertEqual(response.status_code, 200)

        data = {'switch_id': 0,
                'from_date': datetime.now().strftime("%Y-%m-%d"),
                'compare_days': 2,
                'graph_view': 2,
                'compare_type': 2}
        request = self.factory.post('/daily_comparison/', data)
        request.user = self.user
        request.session = {}
        response = cdr_daily_comparison(request)
        self.assertEqual(response.status_code, 200)

        data = {'switch_id': 0,
                'from_date': datetime.now().strftime("%Y-%m-%d"),
                'compare_days': 10,
                'graph_view': 3,
                'compare_type': 7}
        request = self.factory.post('/daily_comparison/', data)
        request.user = self.user
        request.session = {}
        response = cdr_daily_comparison(request)
        self.assertEqual(response.status_code, 200)

    def test_cdr_country_report(self):
        """Test Function to check country report"""
        response = self.client.get('/country_report/')
        #self.assertTemplateUsed(response, 'cdr/country_report.html')
        self.assertEqual(response.status_code, 200)

        request = self.factory.get('/country_report/')
        request.user = self.user
        request.session = {}
        response = cdr_country_report(request)
        self.assertEqual(response.status_code, 200)

        data = {'switch_id': 1,
                'from_date': datetime.now().strftime("%Y-%m-%d"),
                'to_date': datetime.now().strftime("%Y-%m-%d"),
                'duration': 10,
                'duration_type': 1,
                'country_id': 1}
        response = self.client.post('/country_report/', data)
        self.assertEqual(response.status_code, 200)

    def test_cdr_mail_report(self):
        """Test Function to check mail report"""
        response = self.client.get('/mail_report/')
        #self.assertTemplateUsed(response, 'cdr/mail_report.html')
        self.assertEqual(response.status_code, 200)

        data = {'multiple_email': 'abc@localhost.com,xyzlocalhost.com'}
        request = self.factory.post('/mail_report/', data)
        request.user = self.user
        request.session = {}
        #response = mail_report(request)
        #self.assertEqual(response.status_code, 200)

    def test_cdr_world_map(self):
        """Test Function to check world map"""
        response = self.client.get('/world_map/')
        #self.assertTemplateUsed(response, 'cdr/world_map.html')
        self.assertEqual(response.status_code, 200)

        request = self.factory.get('/world_map/')
        request.user = self.user
        request.session = {}
        response = world_map_view(request)
        self.assertEqual(response.status_code, 200)

        data = {'switch_id': 1}
        response = self.client.post('/world_map/', data)
        self.assertEqual(response.status_code, 200)

        data = {'switch_id': -1,
                'from_date': '',
                'to_date': ''}
        request = self.factory.post('/world_map/', data)
        request.user = self.user
        request.session = {}
        response = world_map_view(request)
        self.assertEqual(response.status_code, 200)


class CdrStatsTaskTestCase(TestCase):

    fixtures = ['auth_user.json', 'switch.json',
                'country_dialcode.json', 'hangup_cause.json',
                'voip_gateway.json', 'voip_provider.json',
                'voip_billing.json', 'user_profile.json']

    def test_sync_cdr_pending(self):
        """Test task : sync_cdr_pending"""
        #result = sync_cdr_pending().run()
        # self.assertTrue(result)


class CdrModelTestCase(BaseAuthenticatedClient):

    """Test Switch, Alarm, HangupCause models"""

    fixtures = ['auth_user.json', 'hangup_cause.json']

    def setUp(self):
        """Create model object"""
        self.user = User.objects.get(pk=1)

        # Switch model
        self.switch = Switch(
            name='localhost',
            ipaddress='127.0.0.1'
        )
        self.switch.save()
        self.assertTrue(self.switch.__unicode__())

        self.hangupcause = HangupCause(
            code=700,
            enumeration='UNALLOCATED_NUMBER'
        )
        self.hangupcause.save()
        self.assertTrue(self.hangupcause.__unicode__())

    def test_functions(self):
        get_switch_list()
        get_hangupcause_name(self.hangupcause.pk)
        get_hangupcause_name(2)

        get_hangupcause_id(self.hangupcause.code)

        # Template tags
        hangupcause_name_with_title(self.hangupcause.pk)
        get_country_id_prefix(['44', '442'])

    def test_cdr_search_form(self):
        data = {'switch_id': 1,
                'from_date': datetime.now().strftime("%Y-%m-%d"),
                'to_date': datetime.now().strftime("%Y-%m-%d"),
                'destination': 'abc',
                'destination_type': 1,
                'accountcode': 'abc',
                'caller': 'abc',
                'duration': 'abc',
                'duration_type': '>',
                'direction': 'INBOUND',
                'hangup_cause': 1,
                'result': 1,
                'records_per_page': 10}
        form = CdrSearchForm(data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form["duration"].errors, ['abc is not a valid duration.'])
        #self.assertEqual(form["accountcode"].errors, ['abc is not a valid accountcode.'])

    def test_email_report_form(self):
        data = {'multiple_email': 'abc@localhost.com,xyzlocalhost.com'}
        form = EmailReportForm(self.user, data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form["multiple_email"].errors,
                         ['xyzlocalhost.com is not a valid e-mail address.'])

        data = {'multiple_email': 'abc@localhost.com,xyz@localhost.com'}
        form = EmailReportForm(self.user, data)
        self.assertTrue(form.is_valid())

    def test_model_value(self):
        """Create model object value"""
        self.assertEquals(self.switch.name, 'localhost')
        self.assertEquals(self.hangupcause.enumeration, 'UNALLOCATED_NUMBER')

    def tearDown(self):
        """Delete created object"""
        self.switch.delete()
        self.hangupcause.delete()
