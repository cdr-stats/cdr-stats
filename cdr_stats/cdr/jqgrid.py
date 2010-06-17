# Copyright (c) 2009, Gerry Eisenhaur
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    1. Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#    3. Neither the name of the project nor the names of its contributors may
#       be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
import operator
from django.db import models
from django.core.exceptions import FieldError, ImproperlyConfigured
from django.core.paginator import Paginator, InvalidPage
from django.utils import simplejson as json
from django.utils.encoding import smart_str
from django.http import Http404
#from util.json import json_encode
from cdr_stats.helpers import json_encode
from cdr.models import CDR
from django.core.urlresolvers import reverse

class JqGrid(object):
    queryset = None
    model = None
    fields = []
    allow_empty = True

    pager_id = '#pager'
    url = None
    caption = None
    colmodel_overrides = {}
    
    def get_queryset(self, request):
        if hasattr(self, 'queryset') and self.queryset is not None:
            queryset = self.queryset._clone()        
        elif hasattr(self, 'model') and self.model is not None:
            queryset = self.model.objects.values(*self.get_field_names())
        else:
            raise ImproperlyConfigured("No queryset or model defined.")

        self.queryset = queryset        
        return self.queryset

    def get_model(self):
        if hasattr(self, 'model') and self.model is not None:
            model = self.model
        elif hasattr(self, 'queryset') and self.queryset is not None:
            model = self.queryset.model
            self.model = model
        else:
            raise ImproperlyConfigured("No queryset or model defined.")
        
        return model

    def get_items(self, request):
        items = self.get_queryset(request)
        items = self.filter_items(request, items)
        items = self.sort_items(request, items)
        paginator, page, items = self.paginate_items(request, items)
        return (paginator, page, items)

    def get_filters(self, request):
        _search = request.GET.get('_search')
        filters = None

        if _search == 'true':
            _filters = request.GET.get('filters')
            try:
                filters = _filters and json.loads(_filters)
            except ValueError:
                return None

            if filters is None:
                field = request.GET.get('searchField')
                op = request.GET.get('searchOper')
                data = request.GET.get('searchString')

                if all([field, op, data]):
                    filters = {
                        'groupOp': 'AND',
                        'rules': [{ 'op': op, 'field': field, 'data': data }]
                    }
        return filters

    def filter_items(self, request, items):
        # TODO: Add option to use case insensitive filters
        # TODO: Add more support for RelatedFields (searching and displaying)
        # FIXME: Validate data types are correct for field being searched.
        filter_map = {
            # jqgrid op: (django_lookup, use_exclude)
            'ne': ('%(field)s__exact', True),
            'bn': ('%(field)s__startswith', True),
            'en': ('%(field)s__endswith',  True),
            'nc': ('%(field)s__contains', True),
            'ni': ('%(field)s__in', True),
            'in': ('%(field)s__in', False),
            'eq': ('%(field)s__exact', False),
            'bw': ('%(field)s__startswith', False),
            'gt': ('%(field)s__gt', False),
            'ge': ('%(field)s__gte', False),
            'lt': ('%(field)s__lt', False),
            'le': ('%(field)s__lte', False),
            'ew': ('%(field)s__endswith', False),
            'cn': ('%(field)s__contains', False)
        }
        _filters = self.get_filters(request)
        if _filters is None:
            return items

        q_filters = []
        for rule in _filters['rules']:
            op, field, data = rule['op'], rule['field'], rule['data']
            # FIXME: Restrict what lookups performed against RelatedFields
            field_class = self.model._meta.get_field_by_name(field)[0]
            if isinstance(field_class, models.related.RelatedField):
                op = 'eq'
            filter_fmt, exclude = filter_map[op]
            filter_str = smart_str(filter_fmt % {'field': field})
            if filter_fmt.endswith('__in'):
                d_split = data.split(',')
                filter_kwargs = {filter_str: data.split(',')}
            else:
                filter_kwargs = {filter_str: smart_str(data)}

            if exclude:
                q_filters.append(~models.Q(**filter_kwargs))
            else:
                q_filters.append(models.Q(**filter_kwargs))

        if _filters['groupOp'].upper() == 'OR':
            filters = reduce(operator.ior, q_filters)
        else:
            filters = reduce(operator.iand, q_filters)
        return items.filter(filters)

    def sort_items(self, request, items):
        sidx = request.GET.get('sidx')
        sord = request.GET.get('sord')
        order_by = '%s%s' % (sord == 'desc' and '-' or '', sidx)
        try:
            items = items.order_by(order_by)
        except FieldError:
            pass
        return items

    def get_paginate_by(self, request):
        rows = request.GET.get('rows', 10)
        try:
            paginate_by = int(rows)
        except ValueError:
            paginate_by = 10
        return paginate_by

    def paginate_items(self, request, items):
        paginate_by = self.get_paginate_by(request)
        if not paginate_by:
            return (None, None, items)

        paginator = Paginator(items, paginate_by,
                              allow_empty_first_page=self.allow_empty)
        page = request.GET.get('page', 1)

        try:
            page_number = int(page)
            page = paginator.page(page_number)
        except (ValueError, InvalidPage):
            page = paginator.page(1)
        return (paginator, page, page.object_list)

    def get_json(self, request):
        paginator, page, items = self.get_items(request)
        return json_encode({
            'page': page.number,
            'total': paginator.num_pages,
            'rows': items,
            'records': paginator.count
        })

    def get_default_config(self):
        config = {'mtype':'GET',
            'datatype': 'json',
            'autowidth': True,
            'forcefit': True,
            'shrinkToFit': True,
            'jsonReader': { 'repeatitems': False  },
            'rowNum': 10,
            'rowList': [10, 25, 50, 100],
            #'sortname': 'id',
            'viewrecords': True,
            #'sortorder': "asc",
            'pager': self.pager_id,
            'altRows': True,
            'gridview': True,
            'height': 'auto',
            #'multikey': 'ctrlKey',
            #'multiboxonly': True,
            #'multiselect': True,
            #'toolbar': [False, 'bottom'],
            #'userData': None,
            #'rownumbers': True,
        }
        return config

    def get_url(self):
        #return self.url
        return reverse('grid_handler')

    def get_caption(self):
        if self.caption is None:
            opts = self.get_model()._meta
            self.caption = opts.verbose_name_plural.capitalize()
        return self.caption

    def get_config(self, as_json=True):
        config = self.get_default_config()
        config.update({
            'url': self.get_url(),
            'caption': self.get_caption(),
            'colModel': self.get_colmodels(),            
        })
        if as_json:
            config = json_encode(config)
        return config

    def get_colmodels(self):
        colmodels = []
        opts = self.get_model()._meta
        for field_name in self.get_field_names():
            (field, model, direct, m2m) = opts.get_field_by_name(field_name)
            colmodel = self.field_to_colmodel(field)
            override = self.colmodel_overrides.get(field.name)

            if override:
                colmodel.update(override)
            colmodels.append(colmodel)
        return colmodels

    def get_field_names(self):
        fields = self.fields
        if not fields:
            fields = [f.name for f in self.get_model()._meta.local_fields]
        return fields

    def field_to_colmodel(self, field):
        colmodel = {
            'name': field.name,
            'index': field.name,
            'label': field.verbose_name,
            'editable': True
        }
        return colmodel
