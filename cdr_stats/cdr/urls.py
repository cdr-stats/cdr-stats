from django.conf.urls.defaults import *
from django.conf import settings
from cdr.views import *


urlpatterns = patterns('',
    (r'^$', 'cdr.views.index'),
    
 	(r'^api/', include('cdr.api.urls')),
    #url (r'^examplegrid/$', grid_handler, name='grid_handler2'),
)

