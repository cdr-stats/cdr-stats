from django.contrib.auth.models import User
from tastypie.resources import ModelResource
from tastypie.throttle import BaseThrottle


class UserResource(ModelResource):
    """User Model

    **Read**:

        CURL Usage::

            curl -u username:password -H 'Accept: application/json' http://localhost:8000/api/v1/user/?format=json
    """

    class Meta:
        allowed_methods = ['get']
        queryset = User.objects.all()
        resource_name = 'user'
        fields = ['username', 'first_name', 'last_name', 'last_login', 'id']
        filtering = {'username': 'exact'}
        throttle = BaseThrottle(throttle_at=1000, timeframe=3600)  # default 1000 calls / hour
