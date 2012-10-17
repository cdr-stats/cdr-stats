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
#from tastypie.test import ResourceTestCase
import simplejson


class ApiTestCase(BaseAuthenticatedClient):
    """Test cases for CDR-Stats API."""
    fixtures = ['auth_user.json', 'hangup_cause.json']

    def test_cdr_api(self):
        """Test Function cdr api"""
        data = {"switch_id": 1,
                "caller_id_number": 12345,
                "caller_id_name": "xyz",
                "destination_number": 9972374874,
                "duration": 12,
                "billsec": 15,
                "hangup_cause_q850": 16,
                "accountcode": 32523,
                "direction": "IN",
                "uuid": "e8fee8f6-40dd-11e1-964f-000c296bd875",
                "remote_media_ip": "127.0.0.1",
                "start_uepoch": "2012-02-20 12:23:34",
                "answer_uepoch": "2012-02-20 12:23:34",
                "end_uepoch": "2012-02-20 12:23:34",
                "mduration": 32,
                "billmsec": 43,
                "read_codec": "xyz",
                "write_codec": "abc",
                "cdr_type": 1}
        response = self.client.post('/api/v1/cdr/',
            data, content_type='application/json', **self.extra)
        self.assertEqual(response.status_code, 200)

    def test_cdr_daily_api(self):
        """Test Function cdr daily api"""
        data = {"start_uepoch": "2012-02-15",
                "switch_id": 1,
                "destination_number": 3000,
                "accountcode": 123
        }
        response = self.client.post('/api/v1/cdr_daily_report/', data,
            content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_hangupcause(self):
        """Test Function to create a hangup_cause"""
        # Create
        data = simplejson.dumps({"code": "700", "enumeration": "NORMAL_CLEARING"})
        response = self.client.post('/api/v1/hangup_cause/', data,
            content_type='application/json', **self.extra)
        self.assertEqual(response.status_code, 201)

        # Read
        response = self.client.get('/api/v1/hangup_cause/?format=json', **self.extra)
        self.assertEqual(response.status_code, 200)

        # Update
        #data = simplejson.dumps({"code": "16", "enumeration": "NORMAL_CLEARING"})
        #response = self.client.put('/api/v1/hangup_cause/1/',
        #    data, content_type='application/json', **self.extra)
        #self.assertEqual(response.status_code, 204)

        # Delete
        #response =\
        #    self.client.delete('/api/v1/hangup_cause/', **self.extra)
        #self.assertEqual(response.status_code, 204)

    def test_switch(self):
        """Test Function to create a switch"""
        # Create
        data = simplejson.dumps({"name": "localhost", "ipaddress": "127.0.0.1"})
        response = self.client.post('/api/v1/switch/', data,
            content_type='application/json', **self.extra)
        self.assertEqual(response.status_code, 201)

        # Read
        response = self.client.get('/api/v1/switch/?format=json', **self.extra)
        self.assertEqual(response.status_code, 200)

        # Update
        data = simplejson.dumps({"name": "localhost", "ipaddress": "127.0.0.1"})
        response = self.client.put('/api/v1/switch/1/', data,
            content_type='application/json', **self.extra)
        self.assertEqual(response.status_code, 204)

        # Delete
        response = self.client.delete('/api/v1/switch/1/', **self.extra)
        self.assertEqual(response.status_code, 204)

    def test_playground_view(self):
        """Test Function to create a api list view"""
        response = self.client.get("/explorer/")
        self.assertEqual(response.status_code, 200)