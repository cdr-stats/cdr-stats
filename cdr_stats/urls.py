from django.conf.urls.defaults import *
from django.conf import settings
from cdr.views import *
from django.conf.urls.i18n import *

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

    (r'^i18n/', include('django.conf.urls.i18n')),
    
    ( r'^resources/(?P<path>.*)$',
      'django.views.static.serve',
      { 'document_root': settings.MEDIA_ROOT } ),
    
    # Jqgrid
    
    url (r'^examplegrid/$', grid_handler, name='grid_handler'),
    url (r'^examplegrid/cfg/$', grid_config, name='grid_config'),
	
	(r'^show_cdr/$',              'cdr.views.show_cdr'),
	(r'^show_stats_by_month/$',   'cdr.views.show_graph_by_month'),
    (r'^show_stats_by_day/$',     'cdr.views.show_graph_by_day'),
    (r'^show_stats_by_hour/$',    'cdr.views.show_graph_by_hour'),
	(r'^export_csv/$',            'cdr.views.export_to_csv'),

    # Pages
	(r'^login/$',   'cdr.views.login_view'),
    (r'^logout/$',  'cdr.views.logout_view'),
	(r'^index/$',   'cdr.views.index'),
	(r'^pleaselog/$',   'cdr.views.pleaselog'),
	
)

