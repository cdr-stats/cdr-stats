from tastypie.resources import ModelResource
from tastypie.throttle import BaseThrottle
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import Authorization

from cdr.models import Switch


class SwitchResource(ModelResource):
    """
    **Attributes Details**:

        * ``name`` - Name of switch.
        * ``ipaddress`` - ipaddress

    **Create**:

        CURL Usage::

            curl -u username:password --dump-header - -H "Content-Type:application/json" -X POST --data '{"name": "192.168.1.3", "ipaddress": "192.168.1.3"}' http://localhost:8000/api/v1/switch/

        Response::

            HTTP/1.0 201 CREATED
            Date: Fri, 23 Sep 2011 06:08:34 GMT
            Server: WSGIServer/0.1 Python/2.7.1+
            Vary: Accept-Language, Cookie
            Content-Type: text/html; charset=utf-8
            Location: http://localhost:8000/api/app/switch/1/
            Content-Language: en-us

    **Read**:

        CURL Usage::

            curl -u username:password -H 'Accept: application/json' -X GET http://localhost:8000/api/v1/switch/?format=json

    """
    class Meta:
        queryset = Switch.objects.all()
        resource_name = 'switch'
        authorization = Authorization()
        authentication = BasicAuthentication()
        list_allowed_methods = ['get', 'post', 'put', 'delete']
        detail_allowed_methods = ['get', 'post', 'put', 'delete']
        throttle = BaseThrottle(throttle_at=1000, timeframe=3600)  # default 1000 calls / hour
