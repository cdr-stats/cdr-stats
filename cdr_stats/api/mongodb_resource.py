from bson import ObjectId

from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.conf import settings

from tastypie.bundle import Bundle
from tastypie.resources import Resource
from pymongo import Connection
from cdr.import_cdr_freeswitch_mongodb import common_function_to_create_analytic


class Document(dict):
    # dictionary-like object for mongodb documents.
    __getattr__ = dict.get


class MongoDBResource(Resource):
    """
    A base resource that allows to make CRUD operations for mongodb.
    """
    def get_collection(self):
        """
        Encapsulates collection name.
        """
        try:            
            return settings.DBCON[self._meta.collection]
        except AttributeError:
            raise ImproperlyConfigured("Define a collection in your resource.")

    def obj_get_list(self, request=None, **kwargs):
        """
        Maps mongodb documents to Document class.
        """             
        return map(Document, self.get_collection().find())

    def obj_get(self, request=None, **kwargs):
        """
        Returns mongodb document from provided id.
        """        
        return Document(self.get_collection().find_one({
            "_id": ObjectId(kwargs.get("pk"))
        }))

    def obj_create(self, bundle, **kwargs):
        """
        Creates mongodb document from POST data.
        """            
        self.get_collection().insert(bundle.data)

        # To create daily / monthly analytic        
        date_start_uepoch = bundle.data.get('date_start_uepoch')   
        start_uepoch = bundle.data.get('start_uepoch')     
        switch_id = int(bundle.data.get('switch_id'))
        country_id = bundle.data.get('country_id')
        accountcode = bundle.data.get('accountcode')
        hangup_cause_id = bundle.data.get('hangup_cause_id')        
        duration = bundle.data.get('duration')
        buy_cost = bundle.data.get('buy_cost')
        sell_cost = bundle.data.get('sell_cost')
        retail_plan_id = bundle.data.get('retail_plan_id')        
        common_function_to_create_analytic(date_start_uepoch, start_uepoch, switch_id,
            country_id, accountcode, hangup_cause_id, duration,
            buy_cost, sell_cost, retail_plan_id)
        
        return bundle

    def obj_update(self, bundle, request=None, **kwargs):
        """
        Updates mongodb document.
        """
        self.get_collection().update({
            "_id": ObjectId(kwargs.get("pk"))
        }, {
            "$set": bundle.data
        })
        return bundle

    def obj_delete(self, request=None, **kwargs):
        """
        Removes single document from collection
        """
        self.get_collection().remove({ "_id": ObjectId(kwargs.get("pk")) })

    def obj_delete_list(self, request=None, **kwargs):
        """
        Removes all documents from collection
        """
        self.get_collection().remove()

    def get_resource_uri(self, bundle_or_obj):
        """
        Returns resource URI for bundle or object.
        """   
        kwargs = {
            'resource_name': self._meta.resource_name,
        }

        if isinstance(bundle_or_obj, Bundle):
            if bundle_or_obj.obj._id is None:
                kwargs['pk'] = bundle_or_obj.data['_id']
            else:
                kwargs['pk'] = bundle_or_obj.obj._id
        else:
            kwargs['pk'] = bundle_or_obj.id

        if self._meta.api_name is not None:
            kwargs['api_name'] = self._meta.api_name

        return self._build_reverse_url("api_dispatch_detail", kwargs=kwargs)
