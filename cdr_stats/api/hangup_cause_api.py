from tastypie.resources import ModelResource
from tastypie.throttle import BaseThrottle
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import Authorization

from cdr.models import HangupCause


class HangupCauseResource(ModelResource):
    """
    **Attributes Details**:

        * ``code`` - ITU-T Q.850 Code.
        * ``enumeration`` - Enumeration
        * ``cause`` - cause
        * ``description`` - cause description

    **Read**:

        CURL Usage::

            curl -u username:password -H 'Accept: application/json' -X GET http://localhost:8000/api/v1/hangup_cause/?format=json

    """
    class Meta:
        queryset = HangupCause.objects.all()
        resource_name = 'hangup_cause'
        authorization = Authorization()
        authentication = BasicAuthentication()
        list_allowed_methods = ['get', 'post', 'put', 'delete']
        detail_allowed_methods = ['get', 'post', 'put', 'delete']
        throttle = BaseThrottle(throttle_at=1000, timeframe=3600)  # default 1000 calls / hour