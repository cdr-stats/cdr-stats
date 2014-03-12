#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2013 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django_lets_go.utils import BaseAuthenticatedClient
from cdr_alert.models import AlertRemovePrefix, Alarm, AlarmReport, Blacklist, Whitelist
from cdr_alert.tasks import send_cdr_report, blacklist_whitelist_notification, chk_alarm
from cdr_alert.forms import BWCountryForm
from cdr_alert.functions_blacklist import chk_destination
from cdr_alert.views import alarm_list, alarm_add, alarm_del, alarm_change,\
    trust_control, alert_report  # , alarm_test
from user_profile.constants import NOTICE_TYPE
from country_dialcode.models import Country
from cdr_alert.ajax import add_whitelist_country, add_whitelist_prefix, \
    add_blacklist_country, add_blacklist_prefix, delete_blacklist, delete_whitelist,\
    get_html_table


class CdrAlertAdminInterfaceTestCase(BaseAuthenticatedClient):
    """Test cases for Cdr-Stats Admin Interface."""

    fixtures = [
        'auth_user.json', 'country_dialcode.json',
        'blacklist_prefix.json', 'whitelist_prefix.json'
    ]

    def test_admin_alarm_list(self):
        """Test cases for Admin alarm list"""
        response = self.client.get('/admin/cdr_alert/alarm/')
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_alarm_add(self):
        """Test cases for Admin alarm add"""
        response = self.client.get('/admin/cdr_alert/alarm/add/')
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_alarm_report(self):
        """Test cases for Admin alarm report"""
        response = self.client.get('/admin/cdr_alert/alarmreport/')
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_alert_remove_prefix_list(self):
        """Test cases for Admin alarm remove prefix list"""
        response = self.client.get('/admin/cdr_alert/alertremoveprefix/')
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_alert_remove_prefix_add(self):
        """Test cases for Admin alarm remove prefix add"""
        response = self.client.get('/admin/cdr_alert/alertremoveprefix/add/')
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_alert_whitelist_list(self):
        """Test cases for Admin alert whitelist list"""
        response = self.client.get('/admin/cdr_alert/whitelist/')
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_alert_whitelist_by_country(self):
        """Test cases for Admin alert whitelist list by country"""
        response = self.client.get(
            '/admin/cdr_alert/whitelist/whitelist_by_country/')
        self.assertTemplateUsed(
            response,
            'admin/cdr_alert/whitelist/whitelist_by_country.html')
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.post(
            '/admin/cdr_alert/whitelist/whitelist_by_country/',
            {
                'country': 198,
                'whitelist_country': [],
                'select': [34]
            },
            follow=True)
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.post(
            '/admin/cdr_alert/whitelist/whitelist_by_country/',
            {'country': 198,
             'whitelist_country': [198],
             'select': [34]}, follow=True)
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_alert_blacklist_list(self):
        """Test cases for Admin alert blacklist list"""
        response = self.client.get('/admin/cdr_alert/blacklist/')
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_alert_blacklist_by_country(self):
        """Test cases for Admin alert blacklist list by country"""
        response = self.client.get('/admin/cdr_alert/blacklist/blacklist_by_country/')
        self.assertTemplateUsed(response, 'admin/cdr_alert/blacklist/blacklist_by_country.html')
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.post(
            '/admin/cdr_alert/blacklist/blacklist_by_country/',
            {
                'country': 198,
                'blacklist_country': [],
                'select': [34]
            },
            follow=True)
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.post(
            '/admin/cdr_alert/blacklist/blacklist_by_country/',
            {'country': 198,
             'blacklist_country': [1],
             'select': [34]})
        self.failUnlessEqual(response.status_code, 200)


class CdrAlertCustomerInterfaceTestCase(BaseAuthenticatedClient):
    """Test cases for Cdr-Stats Customer Interface."""

    fixtures = [
        'auth_user.json', 'country_dialcode.json', 'alarm.json',
        'blacklist_prefix.json', 'whitelist_prefix.json'
    ]

    def test_mgt_command(self):
        # Test mgt command
        call_command('send_daily_report')

    def test_alarm_list(self):
        """Test Function to check alarm list"""
        response = self.client.get('/alert/')
        self.failUnlessEqual(response.status_code, 200)

        request = self.factory.get('/alert/')
        request.user = self.user
        request.session = {}
        response = alarm_list(request)
        self.assertEqual(response.status_code, 200)

    def test_alarm_add(self):
        """Test Function to check add alarm"""
        request = self.factory.post(
            '/alert/add/',
            data={
                'name': 'My alarm',
                'value': '10',
                'email_to_send_alarm': 'admin@localhost.com'
            }, follow=True)
        request.user = self.user
        request.session = {}
        response = alarm_add(request)
        self.assertEqual(response.status_code, 200)

        resp = self.client.post(
            '/alert/add/',
            data={
                'name': '',
                'email_to_send_alarm': '',
            })
        self.assertEqual(resp.status_code, 200)

    def test_alarm_view_update(self):
        """Test Function to check update alarm"""
        response = self.client.get('/alert/1/')
        self.assertEqual(response.status_code, 200)

        request = self.factory.post('/alert/1/',
            data={
                'name': 'test',
            }, follow=True)
        request.user = self.user
        request.session = {}
        response = alarm_change(request, 1)
        self.assertEqual(response.status_code, 200)

        # delete alarm through alarm_change
        request = self.factory.post('/alert/2/',
            data={'delete': True}, follow=True)
        request.user = self.user
        request.session = {}
        response = alarm_change(request, 2)
        self.assertEqual(response.status_code, 302)

    #def test_alarm_status(self):
    #    """Test Function to check alarm status"""
    #
    #    request = self.factory.post('/alert/test/1/')
    #    request.user = self.user
    #    request.session = {}
    #    response = alarm_test(request, 1)
    #    self.assertEqual(response.status_code, 200)

    def test_alarm_view_delete(self):
        """Test Function to check delete alarm"""
        request = self.factory.post('/alert/del/1/')
        request.user = self.user
        request.session = {}
        response = alarm_del(request, 1)
        #self.assertEqual(response['Location'], '/alert/')
        self.assertEqual(response.status_code, 302)

        request = self.factory.post('/alert/del/', {'select': '1'})
        request.user = self.user
        request.session = {}
        response = alarm_del(request, 0)
        self.assertEqual(response.status_code, 302)

    def test_trust_control_view(self):
        """Test Function to check trust_control"""
        request = self.factory.get('/trust_control/')
        request.user = self.user
        request.session = {}
        response = trust_control(request)
        self.assertEqual(response.status_code, 200)

    def test_trust_control_ajax(self):
        from django.test.client import RequestFactory
        self.factory = RequestFactory(HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request = self.factory.get('/trust_control/')
        request.user = self.user
        #request.session = {}
        #response = add_whitelist_country(request, 198)
        #self.assertTrue(response)
        #response = get_html_table(request)
        #self.assertTrue(response)
        #response = get_html_table(request, 'whitelist')
        #self.assertTrue(response)

    def test_alert_report(self):
        """To test alarm report"""
        call_command('generate_alert', '--alert-no=10', '--delta-day=1')
        call_command('generate_alert', '--alert-no=10')
        request = self.factory.get('/alert_report/')
        request.user = self.user
        request.session = {}
        response = alert_report(request)
        self.assertEqual(response.status_code, 200)


class CdrAlertModelTestCase(TestCase):
    """Test AlertRemovePrefix, Alarm, AlarmReport,
    Blacklist, Whitelist models
    """
    # initial_data.json is taken from country_dialcode
    fixtures = ['auth_user.json', 'country_dialcode.json', 'notice_type.json',
                'notification.json']

    def setUp(self):
        """Create model object"""
        self.user = User.objects.get(username='admin')

        # AlertRemovePrefix model
        self.alert_remove_prefix = AlertRemovePrefix(
            label='test',
            prefix=32
        )
        self.alert_remove_prefix.save()
        self.assertEquals(self.alert_remove_prefix.__unicode__(), 'test')

        # Alarm model
        self.alarm = Alarm(
            user=self.user,
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

        self.alarm_new = Alarm(
            user=self.user,
            name='Alarm name new',
            period=1,
            type=1,
            alert_condition=2,
            alert_value=10,
            alert_condition_add_on=2,
            status=1,
            email_to_send_alarm='localhost@cdr-stats.org'
        )
        self.alarm_new.save()

        self.alarm_new = Alarm(
            user=self.user,
            name='Alarm name new',
            period=1,
            type=1,
            alert_condition=3,
            alert_value=10,
            alert_condition_add_on=1,
            status=1,
            email_to_send_alarm='localhost@cdr-stats.org'
        )
        self.alarm_new.save()

        self.alarm_new = Alarm(
            user=self.user,
            name='Alarm name new',
            period=1,
            type=1,
            alert_condition=4,
            alert_value=10,
            alert_condition_add_on=1,
            status=1,
            email_to_send_alarm='localhost@cdr-stats.org'
        )
        self.alarm_new.save()

        self.alarm_new = Alarm(
            user=self.user,
            name='Alarm name new',
            period=1,
            type=1,
            alert_condition=5,
            alert_value=10,
            alert_condition_add_on=1,
            status=1,
            email_to_send_alarm='localhost@cdr-stats.org'
        )
        self.alarm_new.save()

        self.alarm_new = Alarm(
            user=self.user,
            name='Alarm name new',
            period=1,
            type=1,
            alert_condition=6,
            alert_value=10,
            alert_condition_add_on=1,
            status=1,
            email_to_send_alarm='localhost@cdr-stats.org'
        )
        self.alarm_new.save()

        self.alarm_new = Alarm(
            user=self.user,
            name='Alarm name new',
            period=2,
            type=1,
            alert_condition=3,
            alert_value=10,
            alert_condition_add_on=2,
            status=1,
            email_to_send_alarm='localhost@cdr-stats.org'
        )
        self.alarm_new.save()

        self.alarm_new = Alarm(
            user=self.user,
            name='Alarm name new',
            period=2,
            type=1,
            alert_condition=4,
            alert_value=10,
            alert_condition_add_on=2,
            status=1,
            email_to_send_alarm='localhost@cdr-stats.org'
        )
        self.alarm_new.save()

        self.alarm_new = Alarm(
            user=self.user,
            name='Alarm name new',
            period=3,
            type=1,
            alert_condition=5,
            alert_value=10,
            alert_condition_add_on=2,
            status=1,
            email_to_send_alarm='localhost@cdr-stats.org'
        )
        self.alarm_new.save()

        self.alarm_new = Alarm(
            user=self.user,
            name='Alarm name new',
            period=3,
            type=1,
            alert_condition=6,
            alert_value=10,
            alert_condition_add_on=2,
            status=1,
            email_to_send_alarm='localhost@cdr-stats.org'
        )
        self.alarm_new.save()

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
            user=self.user,
            phonenumber_prefix=32,
            country=self.country
        )
        self.blacklist.save()
        self.assertTrue(self.blacklist.__unicode__())

        # Whitelist model
        self.whitelist = Whitelist(
            user=self.user,
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

    #def test_blacklist_whitelist_notification(self):
    #    """Test task : blacklist_whitelist_notification"""
    #    # notice_type = 3 blacklist
    #    result = blacklist_whitelist_notification.delay(NOTICE_TYPE.blacklist_prefix)
    #    self.assertTrue(result.get())
    #    result = blacklist_whitelist_notification.delay(NOTICE_TYPE.whitelist_prefix)
    #    self.assertTrue(result.get())

    #def test_chk_alarm(self):
    #    """Test task : chk_alarm"""
    #    result = chk_alarm.delay()
    #    self.assertTrue(result.get())

    def test_send_cdr_report(self):
        """Test task : send_cdr_report"""
        #result = send_cdr_report.delay()
        #self.assertTrue(result.get())
