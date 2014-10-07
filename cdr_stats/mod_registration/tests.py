#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2014 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from django.test import TestCase


class FrontendForgotPassword(TestCase):
    """Test cases for CDR-Stats Customer Interface. for forgot password"""

    def test_check_password_reset(self):
        """Test Function to check password reset"""
        response = self.client.get('/password_reset/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mod_registration/password_reset_form.html')
        response = self.client.post('/password_reset/',
                                    {'email': 'admin@localhost.com'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/password_reset/done/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mod_registration/password_reset_done.html')

        """
        response = self.client.get('/reset/1-2xc-5791af4cc6b67e88ce8e/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'frontend/registration/password_reset_confirm.html')
        response = self.client.post('/reset/1-2xc-5791af4cc6b67e88ce8e/',
            {
                'new_password1': 'admin',
                'new_password2': 'admin'
            },
            follow=True)
        self.assertEqual(response.status_code, 200)
        """
        response = self.client.get('/reset/done/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mod_registration/password_reset_complete.html')
