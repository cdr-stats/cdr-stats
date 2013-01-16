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


class VoipReportAdminInterfaceTestCase(BaseAuthenticatedClient):
    """
    Test cases for voip_billing Admin Interface.
    """
    fixtures = ['auth_user.json']

    def test_admin_voip_report(self):
        """
        Test Function to check voip_report Admin pages
        """
        # voip_report
        response = self.client.get('/admin/voip_report/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/voip_report/voipcall_report/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/voip_report/voipcall_report/import_voip_report/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/voip_report/voipcall_report/export_voip_report/')
        self.failUnlessEqual(response.status_code, 200)