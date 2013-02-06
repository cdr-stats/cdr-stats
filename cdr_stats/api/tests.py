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
    fixtures = ['auth_user.json', 
                'hangup_cause.json', 'switch.json',
                'voip_gateway.json', 'voip_provider.json'                
                'user_profile.json' ]

    def test_switch(self):
        """Test Function to create a switch"""
        # Create
        data = simplejson.dumps({"name": "local", "ipaddress": "127.0.0.2"})
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

    def test_voip_rate(self):
        """Test Function to read voip rate"""        
        # Read
        response = self.client.get('/api/v1/voip_rate/?format=json', **self.extra)
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/api/v1/voip_rate/?dialcode=34&format=json', **self.extra)
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/api/v1/voip_rate/?recipient_phone_no=34650784355&format=json', **self.extra)
        self.assertEqual(response.status_code, 200)
        
    def test_voip_call(self):
        """Test Function to create a switch"""
        # Create
        data = simplejson.dumps({"accountcode":"1000", "answer_uepoch":"1359403221", 
            "billmsec":"12960", "billsec":"104", "caller_id_name":"29914046",
            "caller_id_number":"29914046", "destination_number":"032287971777",
            "direction":"inbound", "duration":"154.0", "end_uepoch":"1359403221", 
            "hangup_cause":"NORMAL_CLEARING", "mduration":"12960", "read_codec":"G711", 
            "remote_media_ip":"192.168.1.21", "resource_uri":"", "start_uepoch":"1359403221", 
            "switch_id":"1", "write_codec":"G711"})
        response = self.client.post('/api/v1/voip_call/', data,
            content_type='application/json', **self.extra)
        self.assertEqual(response.status_code, 201)

        # Read
        response = self.client.get('/api/v1/voip_call/?format=json', **self.extra)
        self.assertEqual(response.status_code, 200)
        
    def test_playground_view(self):
        """Test Function to create a api list view"""
        response = self.client.get("/api-explorer/")
        self.assertEqual(response.status_code, 200)
