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


class ApiTestCase(BaseAuthenticatedClient, ResourceTestCase):
    """Test cases for CDR-Stats API."""
    fixtures = ['auth_user.json', 'hangup_cause.json']

    #def test_create_cdr(self):
    #    """Test Function to create a cdr"""
    #    data = simplejson.dumps({})
    #    response = self.client.post('/api/v1/cdr/',
    #    data, content_type='application/json', **self.extra)
    #    self.assertEqual(response.status_code, 201)

    #def test_create_cdr(self):
    #    """Test Function to create a CDR"""
    #    data = ('cdr=<?xml version="1.0"?><cdr><other></other><variables><plivo_request_uuid>e8fee8f6-40dd-11e1-964f-000c296bd875</plivo_request_uuid><duration>3</duration></variables><notvariables><plivo_request_uuid>TESTc</plivo_request_uuid><duration>5</duration></notvariables></cdr>')
    #    response = self.client.post('/api/v1/store_cdr/', data, content_type='application/json', **self.extra)
    #    self.assertEqual(response.status_code, 200)

    def test_hangupcause(self):
        """Test Function to create a hangup_cause"""
        # Create
        data = simplejson.dumps({"code": "700", "enumeration": "NORMAL_CLEARING"})
        response = self.client.post('/api/v1/hangup_cause/', data,
            content_type='application/json', **self.extra)
        self.assertEqual(response.status_code, 201)

        resp = self.api_client.get('/api/v1/hangup_cause/',
            format='json')
        self.assertValidJSONResponse(resp)

        # Read
        response = self.client.get('/api/v1/hangup_cause/?format=json', **self.extra)
        self.assertEqual(response.status_code, 200)

        # Update
        data = simplejson.dumps({"code": "16", "enumeration": "NORMAL_CLEARING"})
        response = self.client.put('/api/v1/hangup_cause/1/',
            data, content_type='application/json', **self.extra)
        self.assertEqual(response.status_code, 204)

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