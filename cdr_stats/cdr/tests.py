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
from datetime import datetime, timedelta
from common.utils import BaseAuthenticatedClient

from cdr.models import Switch, HangupCause
from cdr.tasks import sync_cdr_pending, get_channels_info

from cdr_alert.tasks import send_cdr_report, \
                            blacklist_whitelist_notification, \
                            chk_alarm


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

    fixtures = ['auth_user.json']

    def test_index(self):
        """Test Function to check customer index page"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cdr/index.html')
        response = self.client.get('/user_detail_change/')
        self.failUnlessEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cdr/registration/user_detail_change.html')

    def test_dashboard(self):
        """Test Function to check customer dashboard"""
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cdr/cdr_dashboard.html')
        self.assertTrue('total_calls' in response.context)
        response = self.client.post('/dashboard/', {'switch_id': 1})
        self.assertEqual(response.status_code, 200)

    def test_cdr_view(self):
        """Test Function to check cdr_view"""
        response = self.client.get('/cdr_view/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cdr/cdr_view.html')
        response = self.client.post('/cdr_view/', {'switch_id': 1,
                                                   'from_date': '2012-05-01',
                                                   'to_date': '2012-05-20',
                                                   'result': 1,
                                                   'records_per_page': 10})
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/cdr_overview/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cdr/cdr_overview.html')
        response = self.client.post('/cdr_overview/', {'switch_id': 1,
                                                       'from_date': '2012-05-01',
                                                       'to_date': '2012-05-20',})
        self.assertEqual(response.status_code, 200)

    def test_cdr_report_view(self):
        """Test Function to check cdr-stats view"""
        response = self.client.get('/hourly_report/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cdr/cdr_report_by_hour.html')
        response = self.client.post('/hourly_report/', {'switch_id': 1,
                                                        'from_date': '2012-05-01',
                                                        'comp_days': 2,
                                                        'graph_view': 1,
                                                        'check_days': 2,
                                                        'result': 'min'})
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/cdr_concurrent_calls/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cdr/cdr_graph_concurrent_calls.html')
        response = self.client.post('/cdr_concurrent_calls/', {'switch_id': 1,
                                                               'from_date': '2012-05-01'})
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/cdr_realtime/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cdr/cdr_graph_realtime.html')
        response = self.client.post('/cdr_realtime/', {'switch_id': 1})
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/country_report/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cdr/cdr_country_report.html')
        response = self.client.post('/country_report/', {'switch_id': 1,
                                                         'from_date': '2012-05-01',
                                                         'to_date': '2012-05-20',})
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/mail_report/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cdr/cdr_mail_report.html')

        response = self.client.get('/world_map/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cdr/world_map.html')
        response = self.client.post('/world_map/', {'switch_id': 1,
                                                    'from_date': '2012-05-01',
                                                    'to_date': '2012-05-20',})
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
