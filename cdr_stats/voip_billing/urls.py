from django.conf.urls import patterns


urlpatterns = patterns('voip_billing.views',
    (r'^retail_rate/$', 'retail_rate_view'),
    (r'^simulator/$', 'simulator'),
    (r'^daily_billing_report/$', 'daily_billing_report'),
    (r'^hourly_billing_report/$', 'hourly_billing_report'),
    #(r'^api/', include('voip2bill.voip_billing.api.urls')),
)
