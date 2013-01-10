from django.conf.urls import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication
from piston.doc import documentation_view
from handlers import *
from django.views.decorators.cache import cache_page


auth = HttpBasicAuthentication(realm='VoipBilling Application')

billvoipcall_handler = Resource(BillVoIPCallHandler, authentication=auth)

urlpatterns = patterns('',


    url(r'^bill_voipcall[/]$', billvoipcall_handler),

    # automated documentation
    url(r'^doc[/]$', documentation_view),
)
