from django.core.urlresolvers import reverse
from cdr.models import CDR
from jqgrid import JqGrid

class ExampleGrid(JqGrid):
    #model = CDR # could also be a queryset
    #queryset = CDR.objects.values('calldate','channel', 'src','clid', 'dst','disposition','duration').filter(duration='30')
    fields = ['calldate','channel', 'src','clid', 'dst','disposition','duration'] # optional
    #url = reverse('grid_handler')
    url = 'http://127.0.0.1:8000/examplegrid/'
    caption = 'Call Detail Records' # optional
    colmodel_overrides = {
        'calldate'   :{'label':'Call Date', 'width':50 },
        'channel'    :{'label':'Channel', 'width':50  },
        'src'        :{'label':'Source', 'width':50  },
        'clid'       :{'label':'Clid', 'width':50  },
        'dst'        :{'label':'Destination', 'width':50 },
        'disposition':{'label':'Disposition', 'width':50 },
        'duration'   :{'label':'Duration', 'width':50  },

    }

