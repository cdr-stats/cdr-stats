from django.conf import settings
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
                return None
        except ConnectionFailure:
            return HttpResponseRedirect('/?db_error=closed')


