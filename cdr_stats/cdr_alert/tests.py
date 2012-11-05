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
from common.utils import BaseAuthenticatedClient
from cdr_alert.models import AlertRemovePrefix, \
                             Alarm, \
                             AlarmReport, \
                             Blacklist, \
                             Whitelist
from cdr_alert.tasks import send_cdr_report, \
                            blacklist_whitelist_notification, \
                            chk_alarm
from cdr_alert.forms import BWCountryForm
from cdr_alert.functions_blacklist import chk_destination
from user_profile.constants import NOTICE_TYPE
from country_dialcode.models import Country
from datetime import timedelta


class CdrAlertAdminInterfaceTestCase(BaseAuthenticatedClient):
    """Test cases for Cdr-Stats Admin Interface."""

    fixtures = ['auth_user.json', 'country_dialcode.json',
                'blacklist_prefix.json', 'whitelist_prefix.json'
               ]

    def test_admin_alarm_list(self):
        """Test Function to check alarm list"""
        response = self.client.get('/admin/cdr_alert/alarm/')
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_alarm_add(self):
        """Test Function to check alarm add"""
        response = self.client.get('/admin/cdr_alert/alarm/add/')
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_alarm_report(self):
        """Test Function to check alarm report"""
        response = self.client.get('/admin/cdr_alert/alarmreport/')
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_alert_remove_prefix_list(self):
        """Test Function to check alert remove prefix list"""
        response = self.client.get('/admin/cdr_alert/alertremoveprefix/')
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_alert_remove_prefix_add(self):
        """Test Function to check alert remove prefix list"""
        response = self.client.get('/admin/cdr_alert/alertremoveprefix/add/')
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_alert_whitelist_list(self):
        """Test Function to check alert whitelist list"""
        response = self.client.get('/admin/cdr_alert/whitelist/')
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_alert_whitelist_by_country(self):
        """Test Function to check alert whitelist by country"""
        response = self.client.get(
            '/admin/cdr_alert/whitelist/whitelist_by_country/')
        self.assertTrue(response.context['form'], BWCountryForm())
        self.assertTemplateUsed(
            response,
            'admin/cdr_alert/whitelist/whitelist_by_country.html')
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.post(
            '/admin/cdr_alert/whitelist/whitelist_by_country/',
                {'country': 198,
                 'whitelist_country': [],
                 'select': [34]}, follow=True)
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.post(
            '/admin/cdr_alert/whitelist/whitelist_by_country/',
            {'country': 198,
             'whitelist_country': [198],
             'select': [34]}, follow=True)
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_alert_blacklist_list(self):
        """Test Function to check alert blacklist list"""
        response = self.client.get('/admin/cdr_alert/blacklist/')
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_alert_blacklist_by_country(self):
        """Test Function to check alert blacklist by country"""
        response = self.client.get(
            '/admin/cdr_alert/blacklist/blacklist_by_country/')
        self.assertTemplateUsed(
            response,
            'admin/cdr_alert/blacklist/blacklist_by_country.html')
        self.assertTrue(response.context['form'], BWCountryForm())
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.post(
            '/admin/cdr_alert/blacklist/blacklist_by_country/',
                {'country': 198,
                 'blacklist_country': [],
                 'select': [34]}, follow=True)
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.post(
            '/admin/cdr_alert/blacklist/blacklist_by_country/',
            {'country': 198,
             'blacklist_country': [1],
             'select': [34]})
        self.failUnlessEqual(response.status_code, 200)


class CdrAlertTaskTestCase(TestCase):

    fixtures = ['auth_user.json']

    def test_blacklist_whitelist_notification(self):
        """Test task : blacklist_whitelist_notification"""
        # notice_type = 3 blacklist
        result = blacklist_whitelist_notification.delay(NOTICE_TYPE.blacklist_prefix)
        self.assertEquals(result.get(), True)

        result = blacklist_whitelist_notification.delay(NOTICE_TYPE.whitelist_prefix)
        self.assertEquals(result.get(), True)

    def test_chk_alarm(self):
        """Test task : chk_alarm"""
        # PeriodicTask
        result = chk_alarm().run()
        self.assertEquals(result, True)

    def test_send_cdr_report(self):
        """Test task : send_cdr_report"""
        result = send_cdr_report().run()
        self.assertEqual(result, True)



class CdrAlertModelTestCase(TestCase):
    """Test AlertRemovePrefix, Alarm, AlarmReport,
    Blacklist, Whitelist models
    """

    # initial_data.json is taken from country_dialcode
    fixtures = ['auth_user.json', 'country_dialcode.json']

    def setUp(self):
        """Create model object"""
        # AlertRemovePrefix model
        self.alert_remove_prefix = AlertRemovePrefix(
            label='test',
            prefix=32
        )
        self.alert_remove_prefix.save()
        self.assertEquals(self.alert_remove_prefix.__unicode__(), 'test')

        # Alarm model
        self.alarm = Alarm(
            name='Alarm name',
            period=1,
            type=1,
            alert_condition=1,
            alert_value=10,
            alert_condition_add_on=1,
            status=1,
            email_to_send_alarm='localhost@cdr-stats.org'
            )
        self.alarm.save()
        self.assertEquals(self.alarm.__unicode__(), 'Alarm name')

        # AlarmReport model
        self.alarm_report = AlarmReport(
            alarm=self.alarm,
            calculatedvalue=10,
            status=1
            )
        self.alarm_report.save()
        self.assertEquals(self.alarm_report.__unicode__(), 'Alarm name')


        self.country = Country.objects.get(pk=198)
        # Blacklist model
        self.blacklist = Blacklist(
            phonenumber_prefix=32,
            country=self.country
            )
        self.blacklist.save()
        self.assertTrue(self.blacklist.__unicode__())

        # Whitelist model
        self.whitelist = Whitelist(
            phonenumber_prefix=32,
            country=self.country
        )
        self.whitelist.save()
        self.assertTrue(self.whitelist.__unicode__())
        chk_destination('9999787424')

    def test_model_value(self):
        """Create model object value"""
        self.assertEquals(self.alert_remove_prefix.label, 'test')
        self.assertNotEquals(self.alert_remove_prefix.id, None)

        self.assertEquals(self.alarm.name, 'Alarm name')
        self.assertEquals(self.alarm_report.alarm, self.alarm)

        self.assertEquals(self.blacklist.country, self.country)
        self.assertEquals(self.blacklist.phonenumber_prefix, 32)

        self.assertEquals(self.whitelist.country, self.country)
        self.assertEquals(self.whitelist.phonenumber_prefix, 32)

    def tearDown(self):
        """Delete created object"""
        self.alert_remove_prefix.delete()
        self.alarm.delete()
        self.alarm_report.delete()
        self.blacklist.delete()
        self.whitelist.delete()
