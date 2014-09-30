# -*- coding: utf-8 -*-
#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2013 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#
from django.conf.urls import handler404, handler500, url, patterns, include
from django.conf import settings
from cdr.urls import urlpatterns as urlpatterns_cdr
from cdr_alert.urls import urlpatterns as urlpatterns_cdr_alert
from user_profile.urls import urlpatterns as urlpatterns_user_profile
from frontend.urls import urlpatterns as urlpatterns_frontend
from voip_billing.urls import urlpatterns as urlpatterns_voip_billing
from frontend_notification.urls import urlpatterns as urlpatterns_frontend_notification
from mod_registration.urls import urlpatterns as urlpatterns_mod_registration
from apirest.urls import urlpatterns as urlpatterns_apirest
from django.contrib import admin
from dajaxice.core import dajaxice_autodiscover
import os
dajaxice_autodiscover()

try:
    admin.autodiscover()
except admin.sites.AlreadyRegistered:
    # nose imports the admin.py files during tests, so
    # the models have already been registered.
    pass

js_info_dict = {
    'domain': 'djangojs',
    'packages': ('cdr', 'cdr_alert'),
}

urlpatterns = patterns('',

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    #(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^i18n/', include('django.conf.urls.i18n')),
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict),
    (r'^admin_tools/', include('admin_tools.urls')),

    # Serve static
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.STATIC_ROOT}),
    (r'^%s/' % settings.DAJAXICE_MEDIA_PREFIX, include('dajaxice.urls')),
)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('', url(r'^__debug__/', include(debug_toolbar.urls)),)

urlpatterns += urlpatterns_cdr
urlpatterns += urlpatterns_cdr_alert
urlpatterns += urlpatterns_user_profile
urlpatterns += urlpatterns_frontend
urlpatterns += urlpatterns_frontend_notification
urlpatterns += urlpatterns_voip_billing
urlpatterns += urlpatterns_mod_registration
urlpatterns += urlpatterns_apirest

# urlpatterns += patterns('',
#     url("", include('django_socketio.urls')),
# )

urlpatterns += patterns('',
    (r'^%s/(?P<path>.*)$' % settings.MEDIA_URL.strip(os.sep),
     'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
)

handler404 = 'cdr_stats.urls.custom_404_view'
handler500 = 'cdr_stats.urls.custom_500_view'


def custom_404_view(request, template_name='404.html'):
    """404 error handler which includes ``request`` in the context.

    Templates: `404.html`
    Context: None
    """
    from django.template import Context, loader
    from django.http import HttpResponseServerError

    t = loader.get_template('404.html')  # Need to create a 404.html template.
    return HttpResponseServerError(t.render(Context({
        'request': request,
    })))


def custom_500_view(request, template_name='500.html'):
    """500 error handler which includes ``request`` in the context.

    Templates: `500.html`
    Context: None
    """
    from django.template import Context, loader
    from django.http import HttpResponseServerError

    t = loader.get_template('500.html')  # Need to create a 500.html template.
    return HttpResponseServerError(t.render(Context({
        'request': request,
    })))
