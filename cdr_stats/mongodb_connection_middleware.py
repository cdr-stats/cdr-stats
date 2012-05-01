from django.conf import settings
from django import http
from django.http import HttpResponseRedirect
from pymongo.connection import Connection
from pymongo.errors import ConnectionFailure

class MongodbConnectionMiddleware(object):

    def process_request(self, request):
        try:
            connection = Connection(settings.CDR_MONGO_HOST, settings.CDR_MONGO_PORT)
            if connection.is_locked:
                if connection.unlock(): # if db gets unlocked
                    return None
                return HttpResponseRedirect('/?db_error=locked')
            else:
                #check if collection have any data
                #db = connection[settings.CDR_MONGO_DB_NAME]
                #collection = db[settings.CDR_MONGO_CDR_COMMON]
                #doc = collection.find_one()
                #if not doc:
                #    return http.HttpResponseForbidden('<h1>Error Import data</h1> Make sure you have existing data in your collections')
                #else:
                #    return None
                return None
        except ConnectionFailure:
            return HttpResponseRedirect('/?db_error=closed')