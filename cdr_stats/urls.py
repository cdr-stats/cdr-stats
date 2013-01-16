# -*- coding: utf-8 -*-
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

from django.conf.urls import url, patterns, include
from django.conf import settings
from tastypie.api import Api
from api.user_api import UserResource
from api.switch_api import SwitchResource
from api.cdr_daily_api import CdrDailyResource
from api.cdr_api import CdrResource
from api.voip_rate_api import VoipRateResource
from api.voip_call_billed import VoipCallBilledResource
from cdr.urls import urlpatterns as urlpatterns_cdr
from cdr_alert.urls import urlpatterns as urlpatterns_cdr_alert
from user_profile.urls import urlpatterns as urlpatterns_user_profile
from frontend.urls import urlpatterns as urlpatterns_frontend
from api.api_playgrounds.urls import urlpatterns as urlpatterns_api_playgrounds
from frontend_notification.urls import urlpatterns as urlpatterns_frontend_notification
#from voip_billing.urls import urlpatterns as urlpatterns_voip_billing

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from dajaxice.core import dajaxice_autodiscover
dajaxice_autodiscover()

try:
    admin.autodiscover()
except admin.sites.AlreadyRegistered:
    # nose imports the admin.py files during tests, so
    # the models have already been registered.
    pass
# tastypie api
tastypie_api = Api(api_name='v1')
tastypie_api.register(UserResource())
tastypie_api.register(SwitchResource())
tastypie_api.register(CdrDailyResource())
tastypie_api.register(CdrResource())
tastypie_api.register(VoipRateResource())
tastypie_api.register(VoipCallBilledResource())


urlpatterns = patterns('',

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    #(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),

    (r'^i18n/', include('django.conf.urls.i18n')),

    (r'^admin_tools/', include('admin_tools.urls')),

    (r'^api/', include(tastypie_api.urls)),

    #Add VoIP Billing
    (r'^voip_billing/', include('voip_billing.urls')),

    # Serve static
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.STATIC_ROOT}),

    (r'^favicon\.ico$', 'django.views.generic.simple.redirect_to',
        {'url': 'static/cdr_stats/images/favicon.ico'}),

    (r'^%s/' % settings.DAJAXICE_MEDIA_PREFIX, include('dajaxice.urls')),
)


urlpatterns += urlpatterns_cdr
urlpatterns += urlpatterns_cdr_alert
urlpatterns += urlpatterns_user_profile
urlpatterns += urlpatterns_frontend
urlpatterns += urlpatterns_api_playgrounds
urlpatterns += urlpatterns_frontend_notification
#urlpatterns += urlpatterns_voip_billing


urlpatterns += patterns('',
    url("", include('django_socketio.urls')),
)
