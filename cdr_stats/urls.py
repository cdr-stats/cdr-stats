#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2012 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from django.conf.urls.defaults import *
from django.conf import settings
from django.conf.urls.i18n import *

from tastypie.api import Api
from api.resources import *
from cdr.urls import urlpatterns as urlpatterns_cdr
from user_profile.urls import urlpatterns as urlpatterns_user_profile

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

# tastypie api
tastypie_api = Api(api_name='v1')
tastypie_api.register(UserResource())
tastypie_api.register(SwitchResource())
tastypie_api.register(HangupCauseResource())
tastypie_api.register(CdrDailyResource())
tastypie_api.register(CdrResource())


urlpatterns = patterns('',
	
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    #(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),

    (r'^i18n/', include('django.conf.urls.i18n')),
    
    (r'^admin_tools/', include('admin_tools.urls')),

    (r'^api/', include(tastypie_api.urls)),
    # Serve static
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': settings.STATIC_ROOT}),
)


urlpatterns += urlpatterns_cdr
urlpatterns += urlpatterns_user_profile

urlpatterns += patterns('',
    url("", include('django_socketio.urls')),
)