from django.contrib.auth.models import User
from django.test import TestCase
from common.utils import BaseAuthenticatedClient
from voip_gateway.models import Gateway, Provider
from voip_billing.models import VoIPPlan
from voip_report.models import VoIPCall, VoIPCall_Report
from user_profile.models import UserProfile


class VoipBillingAdminInterfaceTestCase(BaseAuthenticatedClient):
    """
    Test cases for voip_billing Admin Interface.
    """
    fixtures = ['auth_user.json', 
                'voip_gateway.json', 'voip_provider.json'
                '2_example_voipplan.json', '3_example_voipcarrierplan.json',
                '4_example_voipcarrier_rate.json', '5_example_voipretailplan.json',
                '6_example_voipretailrate.json', '7_example_voipplan_voipretail_plan.json',
                '8_example_voipplan_voipcarrierplan.json', 'country_dialcode.json',]

    def test_admin_voip_billing(self):
        """
        Test Function to check voip_billing Admin pages
        """

        # voip_gateway
        response = self.client.get('/admin/voip_gateway/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/voip_gateway/gateway/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/voip_gateway/provider/')
        self.failUnlessEqual(response.status_code, 200)

        # voip_billing
        response = self.client.get('/admin/voip_billing/')
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get('/admin/voip_billing/voipcarrierplan/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.post('/admin/voip_billing/voipcarrierplan/add/',
            {'name': 'Test', 'description': 'XYZ', 'metric': '1',
             'messagesent': 'x', 'voip_provider_id': '1'}, **self.extra)
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/admin/voip_billing/voipcarrierrate/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/voip_billing/voipcarrierrate/import_cr/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/voip_billing/voipcarrierrate/export_cr/')
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get('/admin/voip_billing/voipretailplan/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.post('/admin/voip_billing/voipretailplan/add/',
            {'name': 'Test', 'description': 'XYZ', 'metric': '1',
             'voip_plan': '1'}, **self.extra)

        self.assertEqual(response.status_code, 200)
        response = self.client.get('/admin/voip_billing/voipretailrate/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/voip_billing/voipretailrate/import_rr/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/voip_billing/voipretailrate/export_rr/')
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get('/admin/voip_billing/voipplan/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.post('/admin/voip_billing/voipplan/add/',
            {'name': 'TEST', 'pubname': 'TT', 'lcrtype': '1', }, **self.extra)
        self.assertEqual(response.status_code, 200)
        response = self.client.post('/admin/voip_billing/voipplan/simulator/',
            {'destination_no': '123456789', 'plan_id': 1}, **self.extra)
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/admin/voip_billing/voipplan/export/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.post('/admin/voip_billing/voipplan/export/',
            {'plan_id': 1}, **self.extra)
        self.assertEqual(response.status_code, 200)
        
        # voip_report
        response = self.client.get('/admin/voip_report/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/voip_report/voipcall_report/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/voip_report/voipcall_report/import_voip_report/')
        self.failUnlessEqual(response.status_code, 200)
        

class VoipBillingCustomerInterfaceTestCase(BaseAuthenticatedClient):
    """
    Test cases for voip_billing Customer Interface.
    """
    fixtures = ['auth_user.json', 'user_profile.json',
                'voip_gateway.json', 'voip_provider.json'
                '2_example_voipplan.json', '3_example_voipcarrierplan.json',
                '4_example_voipcarrier_rate.json', '5_example_voipretailplan.json',
                '6_example_voipretailrate.json', '7_example_voipplan_voipretail_plan.json',
                '8_example_voipplan_voipcarrierplan.json']

    def test_retail_rate_view(self):
        """
        Test Function to check rate for VoIP Call
        """
        response = self.client.get('/voip_billing/retail_rate/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/voip_billing/retail_rate/')
        self.assertEqual(response.status_code, 200)

    def test_simulator(self):
        """
        Test Function to check VoIP Call simulator
        """
        response = self.client.post('/voip_billing/simulator/',
                   data={'destination_no': '123456789',
                         'plan_id': 1})
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/voip_billing/simulator/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'voip_billing/simulator.html')


class VoipBillingCheckTestCase(BaseAuthenticatedClient):
    """
    Test cases for VoIP billing Calculation.
    """
    fixtures = ['auth_user.json', 'user_profile.json',
                'voip_gateway.json', 'voip_provider.json'
                '2_example_voipplan.json', '3_example_voipcarrierplan.json',
                '4_example_voipcarrier_rate.json', '5_example_voipretailplan.json',
                '6_example_voipretailrate.json', '7_example_voipplan_voipretail_plan.json',
                '8_example_voipplan_voipcarrierplan.json']

    def test_check_voip_bill(self):
        """
        To check billing calculation
        """
        voipcall = VoIPCall.objects.create(recipient_number='44650355212',
                                callid=1,
                                callerid='32650841345',)
        
        voipcall.save()
        voipcall_report = VoIPCall_Report()
        response = voipcall_report._bill(voipcall_id=voipcall.id, voipplan_id=1)
        self.assertEquals(voipcall.id, response['voipcall_id'])
