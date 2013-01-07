from django.conf.urls import patterns


urlpatterns = patterns('voip_billing.views',
    (r'^$', 'index'),
    (r'^login/$', 'login_view'),
    (r'^logout/$', 'logout_view'),
    (r'^index/$', 'index'),
    (r'^retail_rate/$', 'retail_rate_view'),
    (r'^simulator/$', 'simulator'),
    #(r'^api/', include('voip2bill.voip_billing.api.urls')),
)
