from jqgrid import *
#from cdr import backend
from cdr.views import *
from django.utils.translation import gettext as _


class ExampleGrid(JqGrid):
    #cdr_backend = backend.get_cdr_backend(settings.VOIP_PLATFORM)
    #queryset = CDR.objects.values('calldate','channel', 'src','clid', 'dst','disposition','duration').all()#filter(duration='30')
    fields = ['calldate','channel', 'src','clid', 'dst','disposition','duration', 'accountcode'] # optional
    caption = _('Call Detail Records') # optional
    colmodel_overrides = {
        'calldate'   :{'label': _('Call Date'), 'width':50 },
        'channel'    :{'label': _('Channel'), 'width':50  },
        'src'        :{'label': _('Source'), 'width':50  },
        'clid'       :{'label': _('Clid'), 'width':50  },
        'dst'        :{'label': _('Destination'), 'width':50 },
        'disposition':{'label': _('Disposition'), 'width':50 },
        'duration'   :{'label': _('Duration'), 'width':50  },
        'accountcode':{'label': _('Accountcode'), 'width':50  },
    }

