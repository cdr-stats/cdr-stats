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
from common.utils import BaseAuthenticatedClient
from cdr_alert.models import AlertRemovePrefix, \
                             Alarm, \
                             AlarmReport, \
                             Blacklist, \
                             Whitelist
from cdr_alert.tasks import send_cdr_report, \
                            blacklist_whitelist_notification, \
                            chk_alarm


class CdrStatsAdminInterfaceTestCase(BaseAuthenticatedClient):
    """Test cases for Cdr-Stats Admin Interface."""

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
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.post(
            '/admin/cdr_alert/whitelist/whitelist_by_country/',
            {'country': 198,})
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_alert_blacklist_list(self):
        """Test Function to check alert blacklist list"""
        response = self.client.get('/admin/cdr_alert/blacklist/')
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_alert_blacklist_by_country(self):
        """Test Function to check alert blacklist by country"""
        response = self.client.get('/admin/cdr_alert/blacklist/blacklist_by_country/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.post('/admin/cdr_alert/blacklist/blacklist_by_country/',
                {'country': 198,})
        self.failUnlessEqual(response.status_code, 200)
