from django.conf.urls import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication
from piston.doc import documentation_view
from handlers import *
from django.views.decorators.cache import cache_page


auth = HttpBasicAuthentication(realm='VoipBilling Application')

voiprate_handler = Resource(VoIPRateHandler, authentication=auth)
billvoipcall_handler = Resource(BillVoIPCallHandler, authentication=auth)

urlpatterns = patterns('',

    url(r'^voiprate[/]$', cache_page(voiprate_handler, 60 * 15)),
    url(r'^voiprate/(?P<code>[^/]+)', cache_page(voiprate_handler, 60 * 15)),
    url(r'^bill_voipcall[/]$', billvoipcall_handler),

    # automated documentation
    url(r'^doc[/]$', documentation_view),
)
