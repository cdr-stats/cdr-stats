from django.conf.urls.defaults import *
from django.conf import settings
from cdr.views import *


# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()



urlpatterns = patterns('',
    
    # redirect
    ('^$', 'django.views.generic.simple.redirect_to', {'url': '/cdr/'}),

    # Example:
    # (r'^stats/', include('stats.foo.urls')),
    #( r'^/resources/(?P<path>.*)$', 'django.views.static.serve',  { 'document_root': settings.MEDIA_ROOT } ),
	(r'^cdr/', include('cdr.urls')),
	
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
	
	(r'^show_jqgrid/$',   'cdr.views.show_jqgrid'),
	
	
	(r'^show_graph_examples/$',   'cdr.views.show_graph'),
    (r'^show_graph_by_hour/$',   'cdr.views.show_graph_by_hour'),
	
	# Pages
	(r'^login/$',   'cdr.views.login'),
	(r'^index/$',   'cdr.views.index'),
	
)

