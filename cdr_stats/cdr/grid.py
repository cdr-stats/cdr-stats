from django.core.urlresolvers import reverse
from cdr.models import CDR
from jqgrid import JqGrid




class ExampleGrid(JqGrid):
    model = CDR # could also be a queryset
    #fields = ['id', 'first_name', 'email'] # optional 
    #url = reverse('grid_handler')
    url = '/examplegrid'
    caption = 'My First Grid' # optional
    colmodel_overrides = {
        'id': { 'editable': False, 'width':10 },
    }


