from django.conf.urls.defaults import *
from django.conf import settings
from cdr.views import *

urlpatterns = patterns('',
    (r'^$', 'cdr.views.index'),
    (r'^login/$',   'cdr.views.login'),
)

