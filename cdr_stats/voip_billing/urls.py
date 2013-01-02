from django.conf.urls.defaults import *
from django.conf import settings
from voip2bill.voip_billing.views import *


urlpatterns = patterns('',
    (r'^$', 'voip2bill.voip_billing.views.index'),
    (r'^login/$', 'voip2bill.voip_billing.views.login_view'),
    (r'^logout/$', 'voip2bill.voip_billing.views.logout_view'),
    (r'^index/$', 'voip2bill.voip_billing.views.index'),
    (r'^retail_rate/$', 'voip2bill.voip_billing.views.retail_rate_view'),
    (r'^simulator/$', 'voip2bill.voip_billing.views.simulator'),
    (r'^api/', include('voip2bill.voip_billing.api.urls')),
)
