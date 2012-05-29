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
from django.test import TestCase, Client
from django.http import HttpRequest
from datetime import datetime, timedelta

from common.test_utils import build_test_suite_from

from cdr.models import Switch, HangupCause
from cdr.tasks import sync_cdr_pending, get_channels_info
from cdr_alert.models import AlertRemovePrefix, Alarm, AlarmReport, Blacklist, Whitelist
from cdr_alert.tasks import send_cdr_report, blacklist_whitelist_notification, chk_alarm

import base64
import simplejson


class BaseAuthenticatedClient(TestCase):
    """Common Authentication"""

    def setUp(self):
        """To create admin user"""
        self.client = Client()
        self.user = \
        User.objects.create_user('admin', 'admin@world.com', 'admin')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.is_active = True
        self.user.save()
        auth = '%s:%s' % ('admin', 'admin')
        auth = 'Basic %s' % base64.encodestring(auth)
        auth = auth.strip()
        self.extra = {
            'HTTP_AUTHORIZATION': auth,
        }
        login = self.client.login(username='admin', password='admin')
        self.assertTrue(login)


class CdrStatsTastypieApiTestCase(BaseAuthenticatedClient):
    """Test cases for Cdr-Stats API."""

    #def test_create_cdr(self):
    #    """Test Function to create a cdr"""
    #    data = simplejson.dumps({})
    #    response = self.client.post('/api/v1/cdr/',
    #    data, content_type='application/json', **self.extra)
    #    self.assertEqual(response.status_code, 201)

    #def test_create_cdr(self):
    #    """Test Function to create a CDR"""
    #    data = ('cdr=<?xml version="1.0"?><cdr><other></other><variables><plivo_request_uuid>e8fee8f6-40dd-11e1-964f-000c296bd875</plivo_request_uuid><duration>3</duration></variables><notvariables><plivo_request_uuid>TESTc</plivo_request_uuid><duration>5</duration></notvariables></cdr>')
    #    response = self.client.post('/api/v1/store_cdr/', data, content_type='application/json', **self.extra)
    #    self.assertEqual(response.status_code, 200)

    def test_hangupcause(self):
        """Test Function to create a hangup_cause"""
        # Create
        data = simplejson.dumps({"code": "16", "enumeration": "NORMAL_CLEARING"})
        response = self.client.post('/api/v1/hangup_cause/', data,
                                    content_type='application/json', **self.extra)
        self.assertEqual(response.status_code, 201)
        # Read
        response = self.client.get('/api/v1/hangup_cause/?format=json', **self.extra)
        self.assertEqual(response.status_code, 200)
        # Update
        data = simplejson.dumps({"code": "16", "enumeration": "NORMAL_CLEARING"})
        response = self.client.put('/api/v1/hangup_cause/1/',
                   data, content_type='application/json', **self.extra)
        self.assertEqual(response.status_code, 204)
        # Delete
        response = \
        self.client.delete('/api/v1/hangup_cause/1/', **self.extra)
        self.assertEqual(response.status_code, 204)

    def test_switch(self):
        """Test Function to create a switch"""
        # Create
        data = simplejson.dumps({"name": "localhost", "ipaddress": "127.0.0.1"})
        response = self.client.post('/api/v1/switch/', data,
                                    content_type='application/json', **self.extra)
        self.assertEqual(response.status_code, 201)
        # Read
        response = self.client.get('/api/v1/switch/?format=json', **self.extra)
        self.assertEqual(response.status_code, 200)
        # Update
        data = simplejson.dumps({"name": "localhost", "ipaddress": "127.0.0.1"})
        response = self.client.put('/api/v1/switch/1/', data,
                                   content_type='application/json', **self.extra)
        self.assertEqual(response.status_code, 204)
        # Delete
        response = self.client.delete('/api/v1/switch/1/', **self.extra)
        self.assertEqual(response.status_code, 204)


class CdrStatsAdminInterfaceTestCase(TestCase):
    """Test cases for Cdr-Stats Admin Interface."""

    def setUp(self):
        """To create admin user"""
        self.client = Client()
        self.user = \
        User.objects.create_user('admin', 'admin@world.com', 'admin')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.is_active = True
        self.user.save()
        auth = '%s:%s' % ('admin', 'admin')
        auth = 'Basic %s' % base64.encodestring(auth)
        auth = auth.strip()
        self.extra = {
            'HTTP_AUTHORIZATION': auth,
        }

    def test_admin_index(self):
        """Test Function to check Admin index page"""
        response = self.client.get('/admin/')
        self.failUnlessEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/base_site.html')
        response = self.client.login(username=self.user.username,
                                     password='admin')
        self.assertEqual(response, True)

    def test_admin_cdrstats(self):
        """Test Function to check Cdr-Stats Admin pages"""
        response = self.client.get('/admin/auth/')
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get('/admin/cdr/switch/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/cdr/switch/add/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.post('/admin/cdr/switch/import_cdr/', {'switch_id': 1,})
        self.failUnlessEqual(response.status_code, 200)


        response = self.client.get('/admin/cdr/hangupcause/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/cdr/hangupcause/add/')
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get('/admin/cdr_alert/alarm/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/cdr_alert/alarm/add/')
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get('/admin/cdr_alert/alarmreport/')
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get('/admin/cdr_alert/alertremoveprefix/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/cdr_alert/alertremoveprefix/add/')
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get('/admin/cdr_alert/whitelist/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/cdr_alert/whitelist/whitelist_by_country/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.post('/admin/cdr_alert/whitelist/whitelist_by_country/',
                                    {'country': 198,})
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get('/admin/cdr_alert/blacklist/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/cdr_alert/blacklist/blacklist_by_country/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.post('/admin/cdr_alert/blacklist/blacklist_by_country/',
                                    {'country': 198,})
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get('/admin/country_dialcode/country/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/country_dialcode/country/add/')
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get('/admin/country_dialcode/prefix/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/country_dialcode/prefix/add/')
        self.failUnlessEqual(response.status_code, 200)


class CdrStatsCustomerInterfaceTestCase(BaseAuthenticatedClient):
    """Test cases for Cdr-Stats Customer Interface."""

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
        self.assertTemplateUsed(response, 'cdr/cdr_graph_by_hour.html')
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

        response = self.client.get('/global_report/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cdr/cdr_global_report.html')
        response = self.client.post('/global_report/', {'switch_id': 1})
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

    def testTask(self):
        # notice_type = 3 blacklist
        result = blacklist_whitelist_notification.delay(3)
        self.assertEquals(result.get(), True)
        # notice_type = 4 whitelist
        result = blacklist_whitelist_notification.delay(4)
        self.assertEquals(result.get(), True)

        # PeriodicTask
        result = chk_alarm().run()
        self.assertEquals(result, True)

        delta = timedelta(seconds=1)
        self.assertEqual(get_channels_info().timedelta_seconds(delta), 1)

        delta = timedelta(seconds=1)
        self.assertEqual(sync_cdr_pending().timedelta_seconds(delta), 1)

        delta = timedelta(seconds=1)
        self.assertEqual(send_cdr_report().timedelta_seconds(delta), 1)        


class CdrStatsModelTestCase(TestCase):

    def testSwitch(self):
        obj = Switch(name='localhost', ipaddress='127.0.0.1')
        obj.save()
        self.assertEquals('localhost', obj.name)
        self.assertNotEquals(obj.id, None)
        obj.delete()

    def testHangupCause(self):
        obj = HangupCause(code=1, enumeration='UNALLOCATED_NUMBER')
        obj.save()
        self.assertEquals(1, obj.code)
        self.assertNotEquals(obj.id, None)
        obj.delete()

    def testAlertRemovePrefix(self):
        obj = AlertRemovePrefix(label='test', prefix=32)
        obj.save()
        self.assertEquals('test', obj.label)
        self.assertNotEquals(obj.id, None)
        obj.delete()

    def testAlarm(self):
        obj = Alarm(name='Alarm name', period=1, type=1, alert_condition=1,
            alert_value=10, alert_condition_add_on=1, status=1,
            email_to_send_alarm='localhost@cdr-stats.org')
        obj.save()
        self.assertEquals('Alarm name', obj.name)
        self.assertNotEquals(obj.id, None)
        obj.delete()

    def testAlarmReport(self):
        obj = AlarmReport(alarm_id=1, calculatedvalue=10, status=1)
        obj.save()
        self.assertEquals(1, obj.alarm_id)
        self.assertNotEquals(obj.id, None)
        obj.delete()

    def testBlacklist(self):
        obj = Blacklist(phonenumber_prefix=32, country_id=198)
        obj.save()
        self.assertEquals(32, obj.phonenumber_prefix)
        self.assertNotEquals(obj.id, None)
        obj.delete()

    def testWhitelist(self):
        obj = Whitelist(phonenumber_prefix=32, country_id=198)
        obj.save()
        self.assertEquals(32, obj.phonenumber_prefix)
        self.assertNotEquals(obj.id, None)
        obj.delete()


test_cases = [
    CdrStatsTastypieApiTestCase,
    CdrStatsAdminInterfaceTestCase,
    CdrStatsCustomerInterfaceTestCase,
    CdrStatsTaskTestCase,
    CdrStatsModelTestCase,
]


def suite():
    return build_test_suite_from(test_cases)
