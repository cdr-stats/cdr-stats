from django.conf.urls.defaults import *
from django.conf import settings
from cdr.views import *

urlpatterns = patterns('cdr.views',
    (r'^$', 'index'),
    (r'^map_view/$', 'map_view'),
)

