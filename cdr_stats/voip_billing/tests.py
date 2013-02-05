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

from common.utils import BaseAuthenticatedClient
from voip_gateway.models import Gateway, Provider
from voip_billing.models import VoIPPlan
from voip_billing.views import voip_rates, export_rate, simulator, daily_billing_report, hourly_billing_report
from user_profile.models import UserProfile
from datetime import datetime


class VoipBillingAdminInterfaceTestCase(BaseAuthenticatedClient):
    """
    Test cases for voip_billing Admin Interface.
    """
    fixtures = ['auth_user.json', 'country_dialcode.json',
                'voip_gateway.json', 'voip_provider.json'
                'user_profile.json']

    def test_admin_voip_billing(self):
        """
        Test Function to check voip_billing Admin pages
        """

        # voip_billing
        response = self.client.get('/admin/voip_billing/')
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get('/admin/voip_billing/voipplan/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/voip_billing/voipplan/rebilling/')
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get('/admin/voip_billing/voipplan/export/')
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get('/admin/voip_billing/voipcarrierplan/')
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get('/admin/voip_billing/voipcarrierrate/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/voip_billing/voipcarrierrate/import_cr/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/voip_billing/voipcarrierrate/export_cr/')
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get('/admin/voip_billing/voipretailplan/')
        self.failUnlessEqual(response.status_code, 200)
        
        response = self.client.get('/admin/voip_billing/voipretailrate/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/voip_billing/voipretailrate/import_rr/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/voip_billing/voipretailrate/export_rr/')
        self.failUnlessEqual(response.status_code, 200)


class VoipBillingCustomerInterfaceTestCase(BaseAuthenticatedClient):
    """
    Test cases for voip_billing Customer Interface.
    """
    fixtures = ['auth_user.json', 'country_dialcode.json',
                'voip_gateway.json', 'voip_provider.json'                
                'user_profile.json',]

    def test_rates_view(self):
        """
        Test Function to check rate for VoIP Call
        """
        response = self.client.get('/rates/')
        self.assertEqual(response.status_code, 200)
        
    def test_simulator(self):
        """
        Test Function to check VoIP Call simulator
        """
        response = self.client.post('/simulator/',
            data={'destination_no': '123456789',
                  'plan_id': 1})
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/simulator/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'voip_billing/simulator.html')

    def test_daily_billing_report(self):
        """
        Test Function to check VoIP Call simulator
        """
        response = self.client.post('/daily_billing_report/',
            data={'plan_id': 1})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'voip_billing/daily_billing_report.html')

        request = self.factory.get('/daily_billing_report/')
        request.user = self.user
        request.session = {}
        response = daily_billing_report(request)
        self.assertEqual(response.status_code, 200)

    def test_hourly_billing_report(self):
        """
        Test Function to check VoIP Call simulator
        """
        response = self.client.post('/hourly_billing_report/',
            data={'plan_id': 1})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'voip_billing/hourly_billing_report.html')

        request = self.factory.get('/hourly_billing_report/')
        request.user = self.user
        request.session = {}
        response = hourly_billing_report(request)
        self.assertEqual(response.status_code, 200)
