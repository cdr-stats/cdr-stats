from django.conf.urls import patterns


urlpatterns = patterns('voip_billing.views',
    (r'^retail_rate/$', 'retail_rate_view'),
    (r'^simulator/$', 'simulator'),
    #(r'^api/', include('voip2bill.voip_billing.api.urls')),
)
