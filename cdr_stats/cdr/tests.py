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
from datetime import datetime, timedelta
from common.utils import BaseAuthenticatedClient

from cdr.models import Switch, HangupCause
from cdr.tasks import sync_cdr_pending, get_channels_info
from cdr_alert.models import AlertRemovePrefix, Alarm, AlarmReport, Blacklist, Whitelist
from cdr_alert.tasks import send_cdr_report, blacklist_whitelist_notification, chk_alarm
from user_profile.models import UserProfile


class CdrStatsAdminInterfaceTestCase(BaseAuthenticatedClient):
    """Test cases for Cdr-Stats Admin Interface."""

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


class CdrStatsModelTestCase(BaseAuthenticatedClient):

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

    def testUserProfile(self):
        obj = UserProfile(user_id=1, address='xyz', city='abc')
        obj.save()
        self.assertEquals(1, obj.user_id)
        self.assertNotEquals(obj.id, None)
        obj.delete()
