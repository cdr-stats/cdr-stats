from django.core.mail import send_mail
from django.db import connection
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.db.models import *
from django.template.context import RequestContext
from cdr.forms import *
from cdr.models import *
from grid import ExampleGrid
from datetime import *
import time
from dateutil import parser
from dateutil.relativedelta import *
import calendar
from sets import *
import operator
import string 
from operator import *
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

def show_graph_by_month(request):
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
            cp_month=int(comp_months)+1
            start_date= end_date+relativedelta(months=-int(cp_month),days=+relative_days(from_day,from_year))
            kwargs[ 'calldate__range' ] = (start_date,end_date)
    
    form = MonthLoadSearchForm(initial={'from_month_year':from_month_year,'comp_months':comp_months,'destination':destination,'destination_type':destination_type,'source':source,'source_type':source_type,'channel':channel,})

    if len(kwargs) == 0:
        form = MonthLoadSearchForm(initial={'from_month_year':from_month_year,'comp_months':2,'destination':destination,'destination_type':1,'source':source,'source_type':1,'channel':channel,})
        tday=datetime.today()
        from_year=tday.year
        from_month= tday.month
        from_day = validate_days(tday.year,tday.month,31)
        comp_months=2
        cp_month=comp_months+1
        end_date = datetime(from_year, from_month, from_day)
        start_date= end_date+relativedelta(months=-int(cp_month),days=+relative_days(from_day,from_year))
        kwargs[ 'calldate__range' ] = (start_date,end_date)

    
    total_month_list = []
    e_month=int(end_date.month)
    e_year=int(end_date.year)
    for i in range(cp_month):
        if  e_month <= 12:
            total_month_list.append((e_month,e_year))
            e_month=e_month-1
            if e_month==0:
                e_month=12
                e_year=e_year-1

   
    
    if kwargs:
        select_data = {"subdate": "strftime('%%m/%%Y', calldate)"}
        calls_min = CDR.objects.filter(**kwargs).extra(select=select_data).values('subdate').annotate(Sum('duration'))
        
        total_record = []
        m_list = []
        r_list = []
        n_list = []
                
        x=0
        for a in total_month_list:
            m_list.append((total_month_list[x][0]))
            x=x+1
        
        y=0
        for b in calls_min:
            r_list.append((int(b['subdate'][0:2])))
            y=y+1
        
        for c in m_list:
            if c in r_list:
                continue
            else:
                n_list.append((c))
                
        x=0
        for j in total_month_list:
            if total_month_list[x][0] in n_list :
                total_record.append((total_month_list[x][0],total_month_list[x][1],0))

            x=x+1
        
        for j in calls_min:
            total_record.append(( int(j['subdate'][0:2]),int(j['subdate'][3:7]),j['duration__sum']))

        #print sorted(total_record, key=lambda total: total[1])
        variables = RequestContext(request,
                            {'form': form,
                             'result':'min',
                             'total_record':sorted(total_record, key=lambda total: total[1]),
                             'comp_months':comp_months,
                             'calls_min':calls_min,
                            })

        return render_to_response('cdr/show_graph_by_month.html', variables,
               context_instance = RequestContext(request))

def show_graph_by_day(request):
    kwargs = {}
    if request.method == 'GET':
        if "from_month_year" in request.GET:
            from_day        = int(request.GET['from_day'])            
            from_month_year = request.GET['from_month_year']
            from_year       = int(request.GET['from_month_year'][0:4])
            from_month      = int(request.GET['from_month_year'][5:7])
        else:
            from_day        = ''
            from_month_year = ''
            from_year       = ''
            from_month      = ''

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

        if from_day != '':
            start_date = datetime(from_year,from_month,from_day,0,0,0,0)
            end_date = datetime(from_year,from_month,from_day,23,59,59,999999)
            kwargs[ 'calldate__range' ] = (start_date,end_date)

    
    form = DailyLoadSearchForm(initial={'from_day':from_day,'from_month_year':from_month_year,'destination':destination,'destination_type':destination_type,'source':source,'source_type':source_type,'channel':channel,})

    if len(kwargs) == 0:
        tday=datetime.today()
        from_day = validate_days(tday.year,tday.month,tday.day)
        form = DailyLoadSearchForm(initial={'from_day':tday.day,'from_month_year':from_month_year,'destination':destination,'destination_type':1,'source':source,'source_type':1,'channel':channel,})
        from_year=tday.year
        from_month= tday.month
        start_date = datetime(from_year,from_month,from_day,0,0,0,0)
        end_date = datetime(from_year,from_month,from_day,23,59,59,999999)
        kwargs[ 'calldate__range' ] = (start_date,end_date)

    if kwargs:
        select_data = {"called_time": "strftime('%%H', calldate)"}#/%%M/%%S
        calls_in_day = CDR.objects.filter(**kwargs).extra(select=select_data).values('called_time').annotate(Count('calldate'))#.order_by('-calldate')#
        total_record = []
        if calls_in_day.count()!=0:
            total_record = []
            list_of_hour = []
            for i in calls_in_day:
                list_of_hour.append((int(i['called_time'])))
                #print list_of_hour
                
            for i in range(0,24):
                if i not in list_of_hour:
                    total_record.append((i,0))

            for i in calls_in_day:
                total_record.append((int(i['called_time']),int(i['calldate__count']) ))

        variables = RequestContext(request,
                            {'form': form,
                             'result':'min',
                             'report_date':start_date,
                             'total_record':sorted(total_record, key=lambda total: total[0]),
                             'calls_in_day':calls_in_day,
                            })

        return render_to_response('cdr/show_graph_by_day.html', variables,
               context_instance = RequestContext(request))

def show_graph_by_hour(request):
    kwargs = {}
    if request.method == 'GET':
        if "from_month_year" in request.GET:
            from_day        = int(request.GET['from_day'])
            from_month_year = request.GET['from_month_year']
            from_year       = int(request.GET['from_month_year'][0:4])
            from_month      = int(request.GET['from_month_year'][5:7])
        else:
            from_day        = ''
            from_month_year = ''
            from_year       = ''
            from_month      = ''

        if "comp_days" in request.GET:
            comp_days = request.GET['comp_days']
        else:
            comp_days = ''

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

        if "graph_view" in request.GET:
            graph_view = request.GET['graph_view']
        else:
            graph_view = ''

        if from_day != '':
            end_date = datetime(from_year, from_month, from_day)
            start_date= end_date+relativedelta(days=-int(comp_days))
            start_date = datetime(start_date.year, start_date.month, start_date.day,0,0,0,0)
            end_date = datetime(end_date.year, end_date.month, end_date.day,23,59,59,999999)

            kwargs[ 'calldate__range' ] = (start_date,end_date)


    form = CompareCallSearchForm(initial={'from_day':from_day,'from_month_year':from_month_year,'comp_days':comp_days,'destination':destination,'destination_type':destination_type,'source':source,'source_type':source_type,'channel':channel,'graph_view':graph_view,})

    if len(kwargs) == 0:
        tday=datetime.today()
        from_day = validate_days(tday.year,tday.month,tday.day)
        form = CompareCallSearchForm(initial={'from_day':tday.day,'from_month_year':from_month_year,'comp_days':2,'destination':destination,'destination_type':1,'source':source,'source_type':1,'channel':channel,'graph_view':1})
        from_year=tday.year
        from_month= tday.month

        end_date = datetime(from_year, from_month, from_day)
        start_date= end_date+relativedelta(days=-2)
        start_date = datetime(start_date.year, start_date.month, start_date.day,0,0,0,0)
        end_date = datetime(end_date.year, end_date.month, end_date.day,23,59,59,999999)

        kwargs[ 'calldate__range' ] = (start_date,end_date)

    if kwargs:
        select_data = {"called_time": "strftime('%%m/%%d/%%Y/%%H/%%M', calldate)"}#/%%M/%%S        
        if graph_view == '1':
            calls_in_day = CDR.objects.filter(**kwargs).extra(select=select_data).values('called_time').annotate(Count('calldate'))#.order_by('-calldate')#
        else:
            calls_in_day = CDR.objects.filter(**kwargs).extra(select=select_data).values('called_time').annotate(Sum('duration'))
        
        record_dates = []
        total_record = []
        total_call_count = []
        dateList = date_range( datetime(start_date.year, start_date.month,start_date.day), datetime(end_date.year, end_date.month, end_date.day))

        for i in calls_in_day:
            if datetime(int(i['called_time'][6:10]),int(i['called_time'][0:2]),int(i['called_time'][3:5])) in dateList:
                record_dates.append(( i['called_time'][6:10]+'-'+i['called_time'][0:2]+'-'+i['called_time'][3:5] ))
                if graph_view == '1':
                    total_record.append(( i['called_time'], i['calldate__count']))
                    total_call_count.append((i['calldate__count']))
                else:
                    total_record.append(( i['called_time'], i['duration__sum']))
                    total_call_count.append((i['duration__sum']))

        
        record_dates=list(set(record_dates))

        if calls_in_day.count()!=0:
            total_record_final = []

            for rd in record_dates:
                list_of_hour = []
                list_of_count= []
                l_o_c= {}
                for i in calls_in_day:
                    string_date = i['called_time'][6:10]+'-'+i['called_time'][0:2]+'-'+i['called_time'][3:5]
                    if string_date == rd:
                        list_of_hour.append(int((i['called_time'][11:13])))
                        if graph_view == '1':
                            list_of_count.append((int(i['called_time'][11:13]),i['calldate__count']))
                            l_o_c[int(i['called_time'][11:13])]=i['calldate__count']
                        else:
                            list_of_count.append((int(i['called_time'][11:13]),i['duration__sum']))
                            l_o_c[int(i['called_time'][11:13])]=i['duration__sum']

                x=0
                for j in range(0,24):
                    if j not in list_of_hour:
                        total_record_final.append((rd,j,0))
                    else:
                        total_record_final.append((rd,j,l_o_c[j]))
                        x=x+1


            for d in dateList:
                sd=str(d)
                date_string= sd[0:4]+'-'+sd[5:7]+'-'+sd[8:10]
                if date_string not in record_dates:
                    for j in range(0,24):
                        total_record_final.append((date_string,j,0))

            call_count_range=range(0,max(total_call_count)+1)
            call_count_range.reverse()
        else:
            call_count_range=[]
            total_record_final=[]

        datelist_final = []
        for i in dateList:
            y =  str(i)
            datelist_final.append(( y[0:4]+'-'+y[5:7]+'-'+y[8:10] ))

        if graph_view == '2':
            graph_view = ''
        variables = RequestContext(request,
                            {'form': form,
                             'result':'min',
                             'record_dates':datelist_final,
                             'total_hour':range(0,24),
                             'graph_view':graph_view,
                             'call_count_range':call_count_range,
                             'total_record':sorted(total_record_final, key=lambda total: total[0]),
                             'calls_in_day':calls_in_day,
                            })

        return render_to_response('cdr/show_graph_by_hour.html', variables,
               context_instance = RequestContext(request))
               
def login(request):
    return render_to_response('cdr/login.html', None,
           context_instance = RequestContext(request))

def index(request):
    template = 'cdr/index.html'
    
    errorlogin = False

    if request.method == 'POST':
        try:
            action = request.POST['action']
        except (KeyError):
            action = "login"
        
        if action=="logout":
            logout(request)
        else:
            loginform = loginForm(request.POST)
            if loginform.is_valid():
                cd = loginform.cleaned_data
                user = authenticate(username=cd['user'], password=cd['password'])
                if user is not None:
                    if user.is_active:
                        login(request, user)
                        # Redirect to a success page.
                    else:
                        # Return a 'disabled account' error message
                        errorlogin = True
                else:
                    # Return an 'invalid login' error message.
                    errorlogin = True

    loginform = loginForm()

    data = {
        'loginform' : loginform,
        'errorlogin' : errorlogin,
        #'is_authenticated' : request.user.is_authenticated()
    }
    
    return render_to_response(template, data,
           context_instance = RequestContext(request))
       
def index2(request):
    return render_to_response('cdr/index.html', None,
           context_instance = RequestContext(request))




