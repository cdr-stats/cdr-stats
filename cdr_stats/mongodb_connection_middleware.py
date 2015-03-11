# -*- coding: utf-8 -*-
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

from django.conf import settings
from django.http import HttpResponseForbidden
#from django.http import HttpResponseRedirect
from pymongo.connection import Connection
from pymongo.errors import ConnectionFailure


class MongodbConnectionMiddleware(object):

    """
    MIDDLEWARE for MongoDB connection
    """

    def process_request(self, request):
        try:
            connection = Connection(settings.MONGO_CDRSTATS['HOST'], settings.MONGO_CDRSTATS['PORT'])
            if connection.is_locked:
                if connection.unlock():  # if db gets unlocked
                    return None
                # return HttpResponseRedirect('/?db_error=locked')
                return HttpResponseForbidden('<h1>Error Connection MongoDB</h1>')
            else:
                # check if collection have any data
                #db = connection[settings.MONGO_CDRSTATS['DB_NAME']]
                #collection = db[settings.MONGO_CDRSTATS['CDR_COMMON']]
                #doc = collection.find_one()
                # if not doc:
                #    return http.HttpResponseForbidden('<h1>Error Import data</h1> Make sure you have existing data in your collections')
                # else:
                #    return None
                return None
        except ConnectionFailure:
            # return HttpResponseRedirect('/?db_error=closed')
            return HttpResponseForbidden('<h1>Error Connection MongoDB</h1>')
