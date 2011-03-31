from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication
from piston.doc import documentation_view
from handlers import *
#from django.views.decorators.cache import cache_page


class CsrfExemptResource(Resource):
    """A Custom Resource that is csrf exempt"""
    def __init__(self, handler, authentication=None):
        super(CsrfExemptResource, self).__init__(handler, authentication)
        self.csrf_exempt = getattr(self.handler, 'csrf_exempt', True)

auth = HttpBasicAuthentication(realm='CDR-Stats Application')

cdr_handler = CsrfExemptResource(cdrHandler, authentication=auth)


urlpatterns = patterns('',

    url(r'^cdr[/]$', cdr_handler),
    url(r'^cdr/(?P<uniqueid>[^/]+)', cdr_handler),

    # automated documentation
    url(r'^doc[/]$', documentation_view),
)

