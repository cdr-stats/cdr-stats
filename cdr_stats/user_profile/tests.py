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
from django.contrib.auth.forms import PasswordChangeForm
from user_profile.models import UserProfile
from user_profile.forms import UserChangeDetailForm, \
    UserChangeDetailExtendForm
from user_profile.views import customer_detail_change
from common.utils import BaseAuthenticatedClient

#from django.contrib import admin
#admin.site.register(User)


class UserProfileAdminView(BaseAuthenticatedClient):
    """Test Function to check UserProfile Admin pages"""

    def test_admin_staff_view_list(self):
        """Test Function to check admin staff list"""
        response = self.client.get("/admin/auth/staff/")
        self.assertEqual(response.status_code, 200)

    def test_admin_staff_view_add(self):
        """Test Function to check admin staff add"""
        response = self.client.get("/admin/auth/staff/add/")
        self.assertEqual(response.status_code, 200)

    def test_admin_customer_view_list(self):
        """Test Function to check admin customer list"""
        response = self.client.get("/admin/auth/customer/")
        self.assertEqual(response.status_code, 200)

    def test_admin_customer_view_add(self):
        """Test Function to check admin customer add"""
        response = self.client.get("/admin/auth/customer/add/")
        self.assertEqual(response.status_code, 200)


class UserProfileCustomerView(BaseAuthenticatedClient):
    """Test Function to check UserProfile Customer pages"""

    fixtures = ['auth_user.json', 'notification.json']

    def test_user_settings(self):
        """Test Function to check User settings"""
        response = self.client.get('/user_detail_change/')
        self.assertTrue(response.context['user_detail_form'],
                        UserChangeDetailForm(self.user))
        self.assertTrue(response.context['user_detail_extened_form'],
                        UserChangeDetailExtendForm(self.user))
        self.assertTrue(response.context['user_password_form'],
                        PasswordChangeForm(self.user))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
            'frontend/registration/user_detail_change.html')

        request = self.factory.get('/user_detail_change/')
        request.user = self.user
        request.session = {}
        response = customer_detail_change(request)
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/user_detail_change/?action=tabs-1',
                {'form-type': 'change-detail',
                 'first_name': 'admin',
                 'phone_no': '9324552563'})
        self.assertTrue(response.context['user_detail_form'],
            UserChangeDetailForm(self.user))
        self.assertTrue(response.context['user_detail_extened_form'],
            UserChangeDetailExtendForm(self.user))

        response = self.client.post('/user_detail_change/?action=tabs-2',
                {'form-type': ''})
        self.assertTrue(response.context['user_password_form'],
            PasswordChangeForm(self.user))


class UserProfileModel(TestCase):
    """Test UserProfile Model"""
    fixtures = ['auth_user.json']

    def setUp(self):
        self.user = User.objects.get(username='admin')

        self.user_profile = UserProfile(
            user=self.user,
        )
        self.user_profile.save()

    def test_user_profile_forms(self):
        self.assertEqual(self.user_profile.user, self.user)

        form = UserChangeDetailForm(self.user)
        form.user.last_name = "Test"
        form.user.first_name = "Test"
        form.user.save()

        form = UserChangeDetailExtendForm(self.user)
        form.user.address = "test address"
        form.user.save()

    def teardown(self):
        self.user_profile.delete()
