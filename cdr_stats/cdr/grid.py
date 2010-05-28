from django.core.urlresolvers import reverse
from cdr.models import CDR
from jqgrid import JqGrid


class ExampleGrid(JqGrid):
    model = CDR # could also be a queryset
    #fields = ['id', 'first_name', 'email'] # optional 
    #url = reverse('grid_handler')
    url = 'http://127.0.0.1:8000/examplegrid/'
    caption = 'My First Grid' # optional
    colmodel_overrides = {
        'acctid': { 'editable': False, 'width':50 },
    }


