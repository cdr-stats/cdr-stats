from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.db.models import *
from django.template.context import RequestContext
from cdr.forms import *
from cdr.models import *
from grid import ExampleGrid
from datetime import *
from time import *
from dateutil import parser
from dateutil.relativedelta import *
import calendar
from cdr_stats.helpers import json_encode


# Create your views here.

def grid_handler(request):
    # handles pagination, sorting and searching
    grid = ExampleGrid()
    return HttpResponse(grid.get_json(request), mimetype="application/json")

def grid_config(request):
    # build a config suitable to pass to jqgrid constructor   
    grid = ExampleGrid()
    return HttpResponse(grid.get_config(), mimetype="application/json")

def show_jqgrid(request):
    return render_to_response('cdr/show_jqgrid.html', None,
           context_instance = RequestContext(request))

def show_graph(request):
    kwargs = {}
    if request.method == 'GET':
        if "from_month_year" in request.GET:
            from_month_year = request.GET['from_month_year']
            from_year       = int(request.GET['from_month_year'][0:4])
            from_month      = int(request.GET['from_month_year'][5:7])
        else:
            from_month_year = ''
            from_year       = ''
            from_month      = ''

        if "comp_months" in request.GET:
            comp_months = request.GET['comp_months']
        else:
            comp_months = ''

        if "destination" in request.GET:
            destination = request.GET['destination']
        else:
            destination = ''

        if "destination_type" in request.GET:
            destination_type = request.GET['destination_type']
        else:
            destination_type = ''

        if destination != '':
            if destination_type == '1':
                kwargs[ 'dst__exact' ] = destination
            if destination_type == '2':
                kwargs[ 'dst__startswith' ] = destination
            if destination_type == '3':
                kwargs[ 'dst__contains' ] = destination
            if destination_type == '4':
                kwargs[ 'dst__endswith' ] = destination

        if "source" in request.GET:
            source = request.GET['source']
        else:
            source = ''

        if "source_type" in request.GET:
            source_type = request.GET['source_type']
        else:
            source_type = ''

        if source != '':
            if source_type == '1':
                kwargs[ 'src__exact' ] = source
            if source_type == '2':
                kwargs[ 'src__startswith' ] = source
            if source_type == '3':
                kwargs[ 'src__contains' ] = source
            if source_type == '4':
                kwargs[ 'src__endswith' ] = source

        if "channel" in request.GET:
            channel = request.GET['channel']
        else:
            channel = ''

        if channel!='':
            kwargs[ 'channel' ] = channel
        
        if comp_months != '':
            from_day = validate_days(from_year,from_month,31)
            end_date = datetime(from_year, from_month, from_day)
            start_date= end_date+relativedelta(months=-int(comp_months),days=+1)
            kwargs[ 'calldate__range' ] = (start_date,end_date)
    
    form = MonthLoadSearchForm(initial={'from_month_year':from_month_year,'comp_months':comp_months,'destination':destination,'destination_type':destination_type,'source':source,'source_type':source_type,'channel':channel,})

    if len(kwargs) == 0:
        form = MonthLoadSearchForm(initial={'from_month_year':from_month_year,'comp_months':2,'destination':destination,'destination_type':1,'source':source,'source_type':1,'channel':channel,})
        tday=datetime.today()
        from_year=tday.year
        from_month= tday.month
        from_day = validate_days(tday.year,tday.month,31)

        end_date = datetime(from_year, from_month, from_day)
        start_date= end_date+relativedelta(months=-2,days=+1)
        kwargs[ 'calldate__range' ] = (start_date,end_date)

    if kwargs:
        select_data = {"subdate": """strftime('%%m/%%d/%%Y', calldate)"""}
        calls_min = CDR.objects.filter(**kwargs).extra(select=select_data).values('subdate').annotate(Sum('duration'))
    
        variables = RequestContext(request,
                            {'form': form,
                             'result':'min',
                             'comp_months':comp_months,
                             'calls_min':calls_min,
                            })
        return render_to_response('cdr/show_graph.html', variables,
               context_instance = RequestContext(request))


def login(request):
    return render_to_response('cdr/login.html', None,
           context_instance = RequestContext(request))
           
def index(request):
    return render_to_response('cdr/index.html', None,
           context_instance = RequestContext(request))




