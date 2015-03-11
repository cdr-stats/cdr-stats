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

from django_lets_go.utils import BaseAuthenticatedClient


class VoipReportAdminInterfaceTestCase(BaseAuthenticatedClient):

    """
    Test cases for voip_billing Admin Interface.
    """
    fixtures = ['auth_user.json']

    def test_admin_voip_gateway(self):
        """
        Test Function to check voip_gateway Admin pages
        """
        # voip_gateway
        response = self.client.get('/admin/voip_gateway/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/voip_gateway/gateway/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/voip_gateway/provider/')
        self.failUnlessEqual(response.status_code, 200)
