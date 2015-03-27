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

from django_lets_go.utils import BaseAuthenticatedClient
from voip_billing.forms import BillingReportForm, \
    PrefixRetailRateForm
from voip_billing.views import billing_report, export_rate
from voip_billing.tasks import RebillingTask, ReaggregateTask
from dateutil.relativedelta import relativedelta
from datetime import datetime


class VoipBillingAdminInterfaceTestCase(BaseAuthenticatedClient):

    fixtures = ['auth_user.json', 'notice_type.json', 'notification.json',
                'country_dialcode.json', 'voip_gateway.json', 'voip_provider.json',
                'voip_billing.json', 'user_profile.json']

    def test_admin_voip_billing(self):

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
    fixtures = ['auth_user.json', 'notice_type.json', 'notification.json',
                'country_dialcode.json', 'voip_gateway.json', 'voip_provider.json',
                'voip_billing.json', 'user_profile.json']

    def test_rates_export_view(self):
        """
        Test Function to check rate for VoIP Call
        """
        request = self.factory.post('/export_rate/?format=csv')
        request.user = self.user
        request.session = {}
        response = export_rate(request)
        self.assertEqual(response.status_code, 200)

        request = self.factory.post('/export_rate/?format=json')
        request.user = self.user
        request.session = {}
        response = export_rate(request)
        self.assertEqual(response.status_code, 200)

        request = self.factory.post('/export_rate/?format=xls')
        request.user = self.user
        request.session = {}
        response = export_rate(request)
        self.assertEqual(response.status_code, 200)

    def test_simulator(self):
        """
        Test Function to check VoIP Call simulator
        """
        response = self.client.get('/simulator/')
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            '/simulator/',
            data={'destination_no': '123456789', 'plan_id': 1})
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/simulator/')
        self.assertEqual(response.status_code, 200)
        #self.assertTemplateUsed(response, 'voip_billing/simulator.html')

    def test_billing_report(self):
        """
        Test Function to check VoIP daily billing report
        """
        response = self.client.get('/billing_report/')
        #self.assertTrue(response.context['form'], BillingReportForm())
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            '/billing_report/',
            data={'plan_id': 1,
                  'from_date': datetime.now().strftime("%Y-%m-%d"),
                  'to_date': datetime.now().strftime("%Y-%m-%d")})
        self.assertEqual(response.status_code, 200)
        #self.assertTemplateUsed(response, 'voip_billing/billing_report.html')

        request = self.factory.get('/billing_report/')
        request.user = self.user
        request.session = {}
        response = billing_report(request)
        self.assertEqual(response.status_code, 200)

        data = {'plan_id': 1,
                'from_date': datetime.now().strftime("%Y-%m-%d"),
                'to_date': datetime.now().strftime("%Y-%m-%d")}
        request = self.factory.post('/billing_report/', data)
        request.user = self.user
        request.session = {}
        response = billing_report(request)
        self.assertEqual(response.status_code, 200)

    def test_rebilling(self):
        """Test task : RebillingTask"""
        tday = datetime.today()
        voipplan_id = 1
        end_date = datetime(tday.year, tday.month, tday.day,
                            tday.hour, tday.minute, tday.second, tday.microsecond)
        start_date = end_date + relativedelta(days=-1)
        call_kwargs = {}
        call_kwargs['start_uepoch'] = {'$gte': start_date, '$lt': end_date}
        result = RebillingTask.delay(call_kwargs, voipplan_id)
        #self.assertEqual(result.get(), True)

    def test_reaggregate(self):
        """Test task : ReaggregateTask"""
        call_kwargs = {}
        daily_query_var = {}
        monthly_query_var = {}

        tday = datetime.today()
        end_date = datetime(tday.year, tday.month, tday.day,
                            tday.hour, tday.minute, tday.second, tday.microsecond)
        start_date = end_date + relativedelta(days=-1)

        call_kwargs['start_uepoch'] = {'$gte': start_date, '$lt': end_date}
        daily_query_var['metadata.date'] = {'$gte': start_date.strftime('%Y-%m-%d'),
                                            '$lt': end_date.strftime('%Y-%m-%d')}
        monthly_query_var['metadata.date'] = {'$gte': start_date.strftime('%Y-%m'),
                                              '$lt': end_date.strftime('%Y-%m')}
        result = ReaggregateTask.delay(daily_query_var, monthly_query_var, call_kwargs)
        #self.assertEqual(result.get(), True)
