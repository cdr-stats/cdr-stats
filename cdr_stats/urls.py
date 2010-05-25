from django.conf.urls.defaults import *
from django.conf import settings
from cdr.views import *


# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()



urlpatterns = patterns('',
    # Example:
    # (r'^stats/', include('stats.foo.urls')),
    #( r'^/resources/(?P<path>.*)$', 'django.views.static.serve',  { 'document_root': settings.MEDIA_ROOT } ),
	(r'^projects/cdr/', include('cdr.urls')),
	
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
	
    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    
    ( r'^resources/(?P<path>.*)$',
      'django.views.static.serve',
      { 'document_root': settings.MEDIA_ROOT } ),
    
    # Jqgrid
    
    url (r'^examplegrid/$', grid_handler, name='grid_handler'),
	url (r'^examplegrid/cfg/$', grid_config, name='grid_config'),
		
	(r'^json/cdr/$',   'cdr.views.json_cdr'),
	(r'^show_cdr/$',   'cdr.views.show_cdr'),
	
)

