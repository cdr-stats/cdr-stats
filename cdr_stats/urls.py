from django.conf.urls.defaults import *
from django.conf import settings

from cdr.urls import urlpatterns as urlpatterns_cdr

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()



urlpatterns = patterns('',

    # Example:
    # (r'^stats/', include('stats.foo.urls')),
    #( r'^/resources/(?P<path>.*)$', 'django.views.static.serve',  { 'document_root': settings.MEDIA_ROOT } ),
	
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
	
    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),

    # Serve static
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
    {'document_root': settings.STATIC_ROOT}),

)

urlpatterns += urlpatterns_cdr