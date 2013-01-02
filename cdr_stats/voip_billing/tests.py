from django.contrib.auth.models import User
from django.test import TestCase, Client
from voip2bill.voip_gateway.models import *
from voip2bill.voip_billing.models import *
from voip2bill.voip_billing.forms import *
from voip2bill.voip_billing.function_def import *
from voip2bill.voip_billing.test_utils import *
from voip2bill.voip_report.models import *
from voip2bill.user_profile.models import *
import base64

class BaseAuthenticatedClient(TestCase):
    """
    Common Authentication
    """

    def setUp(self):
        """
        To create admin user
        """
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
        voipplan = VoIPPlan.objects.get(id=1)
        up = UserProfile.objects.create(user=self.user, voipplan=voipplan)
        up.save()


class VoipBillingApiTestCase(BaseAuthenticatedClient):
    """
    Test cases for voip_billing API.
    """
    
    def test_voip_rate(self):
        """
        Test Function to get VoIP call rate
        """
        response = self.client.post('/voip_billing/api/voiprate/',
                   {"recipient_phone_no": "0044650355212", }, **self.extra)
        self.assertEqual(response.status_code, 200)        

    def test_voip_report_import(self):
        """
        Test Function to import data into VoIPCall report
        """
        response = self.client.post('/voip_billing/api/bill_voipcall/',
                   {"recipient_phone_no": "0044650355212",
                    "sender_phone_no": "0032650781232",
                    "status": "Failed",                    
                    "send_date": "2011-03-11 01:01:01"}, **self.extra)
        self.assertEqual(response.status_code, 200)

class VoipBillingAdminInterfaceTestCase(TestCase):
    """
    Test cases for voip_billing Admin Interface.
    """
    def setUp(self):
        """
        To create admin user
        """
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
        """
        Test Function to check Admin index page
        """
        response = self.client.get('/admin/')
        self.failUnlessEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/base_site.html')
        response = self.client.login(username=self.user.username,
                                     password='admin')
        self.assertEqual(response, True)

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
        response = \
        self.client.get('/admin/voip_billing/voipcarrierrate/import_cr/')
        self.failUnlessEqual(response.status_code, 200)
        response = \
        self.client.get('/admin/voip_billing/voipcarrierrate/export_cr/')
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get('/admin/voip_billing/voipretailplan/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.post('/admin/voip_billing/voipretailplan/add/',
        {'name': 'Test', 'description': 'XYZ', 'metric': '1',
         'voip_plan': '1'}, **self.extra)

        self.assertEqual(response.status_code, 200)
        response = self.client.get('/admin/voip_billing/voipretailrate/')
        self.failUnlessEqual(response.status_code, 200)
        response = \
        self.client.get('/admin/voip_billing/voipretailrate/import_rr/')
        self.failUnlessEqual(response.status_code, 200)
        response = \
        self.client.get('/admin/voip_billing/voipretailrate/export_rr/')
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
        response = self.client.get(
        '/admin/voip_report/voipcall_report/import_voip_report/'
        )
        self.failUnlessEqual(response.status_code, 200)
        

class VoipBillingCustomerInterfaceTestCase(BaseAuthenticatedClient):
    """
    Test cases for voip_billing Customer Interface.
    """

    def test_index(self):
        """
        Test Function to check customer index page
        """
        response = self.client.get('/voip_billing/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'voip_billing/index.html')
        response = self.client.post('/voip_billing/login/',
                    {'username': 'userapi',
                     'password': 'passapi'})
        self.assertEqual(response.status_code, 200)

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


test_cases = [
    VoipBillingApiTestCase,
    VoipBillingAdminInterfaceTestCase,
    VoipBillingCustomerInterfaceTestCase,
    VoipBillingCheckTestCase,
]


def suite():
    return build_test_suite_from(test_cases)
