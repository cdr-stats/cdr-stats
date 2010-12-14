from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response
from django.db.models import *
from django.template.context import RequestContext
from cdr.forms import *
from cdr.models import *
from grid import ExampleGrid
from datetime import *
from dateutil import parser
from dateutil.relativedelta import *
from sets import *
from django.db.models.loading import get_model
from operator import *
from cdr_stats.helpers import json_encode
from uni_form.helpers import FormHelper, Submit, Reset
from django.utils.translation import gettext as _
import calendar
import time
import operator
import string
import csv, codecs
from operator import itemgetter
from inspect import stack, getmodule

DISPOSITION = (
    (1, _('ANSWER')),
    (2, _('BUSY')),
    (3, _('NOANSWER')),
    (4, _('CANCEL')),
    (5, _('CONGESTION')),
    (6, _('CHANUNAVAIL')),
    (7, _('DONTCALL')),
    (8, _('TORTURE')),
    (9, _('INVALIDARGS')),
)


# Create your views here.
@login_required
def grid_handler(request):
    # handles pagination, sorting and searching
    grid = ExampleGrid()

    # To add dynamic query set
    grid.queryset  = request.session['cdr_queryset']

    return HttpResponse(grid.get_json(request), mimetype="application/json")

@login_required
def grid_config(request):
    # build a config suitable to pass to jqgrid constructor
    grid = ExampleGrid()

    # To add dynamic query set
    grid.queryset  = request.session['cdr_queryset']

    return HttpResponse(grid.get_config(), mimetype="application/json")


@login_required
def show_cdr(request): 

    kwargs = {}
    if request.method == 'POST':
        if "from_date" in request.POST:
            # From
            from_date = request.POST['from_date']
            start_date = datetime(int(from_date[0:4]), int(from_date[5:7]), int(from_date[8:10]), 0, 0, 0, 0)

            # To
            to_date = request.POST['to_date']
            end_date = datetime(int(to_date[0:4]), int(to_date[5:7]), int(to_date[8:10]), 23, 59, 59, 999999)
    
    try:
        from_date
    except NameError:
        tday = datetime.today()
        from_date = tday.strftime('%Y-%m-01')
        last_day = ((datetime(tday.year, tday.month, 1, 23, 59, 59, 999999) + relativedelta(months=1)) - relativedelta(days=1)).strftime('%d')
        to_date = tday.strftime('%Y-%m-'+last_day)
        
        start_date = datetime(int(from_date[0:4]), int(from_date[5:7]), int(from_date[8:10]), 0, 0, 0, 0)
        end_date = datetime(int(to_date[0:4]), int(to_date[5:7]), int(to_date[8:10]), 23, 59, 59, 999999)
        
    kwargs[ 'start__range' ] = (start_date, end_date)
    
    result = variable_value(request,'result')
    if result == '':
        result = '1'
    request.session['cdr_queryset'] = ''

    #select_data = {"start": "strftime('%%Y-%%m-%%d', start)"}
    select_data = {"start": "SUBSTR(CAST(start as CHAR(30)),1,10)"}
    
    if not request.user.is_superuser:
        kwargs[ 'accountcode' ] = request.user.get_profile().accountcode
    
    queryset = CDR.objects.values('start', 'channel', 'src', 'clid', 'dst', 'disposition', 'duration', 'accountcode').filter(**kwargs).order_by('-start')
    total_data = CDR.objects.extra(select=select_data).values('start').filter(**kwargs).annotate(Count('start')).annotate(Sum('duration')).annotate(Avg('duration')).order_by('-start')
    form = CdrSearchForm(initial={'from_date':from_date,'to_date':to_date,'result':result,'export_csv_queryset':'0'})
    
    count = 0
    if result == '1':
        for i in queryset:
            queryset[count]['duration'] = int_convert_to_minute(int(i['duration']))
            count +=1
    
    count = 0
    for i in queryset:
        disposition = ''
        for d in DISPOSITION:
            if d[0] == i['disposition']:
                disposition = d[1]
        queryset[count]['disposition'] = disposition
        count +=1
    
    request.session['cdr_queryset'] = queryset
    
    if total_data.count() != 0:
        max_duration = max([x['duration__sum'] for x in total_data])
        total_duration = sum([x['duration__sum'] for x in total_data])
        total_calls = sum([x['start__count'] for x in total_data])
        total_avg_duration = (sum([x['duration__avg'] for x in total_data]))/total_data.count()
    else:
        max_duration = 0
        total_duration = 0
        total_calls = 0
        total_avg_duration = 0

    variables = RequestContext(request, { 'module': current_view(request),
                                          'form': form,
                                          'queryset': request.session['cdr_queryset'],
                                          'total_data':total_data.reverse(),
                                          'total_duration':total_duration,
                                          'total_calls':total_calls,
                                          'total_avg_duration':total_avg_duration,
                                          'max_duration':max_duration,
                                        })
                                             
    return render_to_response('cdr/show_jqgrid.html', variables,
           context_instance = RequestContext(request))

def export_to_csv(request):
    # get the response object, this can be used as a stream.
    response = HttpResponse(mimetype='text/csv')
    # force download.
    response['Content-Disposition'] = 'attachment;filename=export.csv'
    # the csv writer
    writer = csv.writer(response)
    qs = request.session['cdr_queryset']
    writer.writerow(['start', 'Channel', 'Source', 'Clid','Destination','Disposition','Duration', 'AccountCode'])
    for cdr in qs:
        writer.writerow([cdr['start'], cdr['channel'].encode("utf-8"), cdr['src'].encode("utf-8"), cdr['clid'].encode("utf-8"), cdr['dst'].encode("utf-8"), cdr['disposition'], cdr['duration'].encode("utf-8"), cdr['accountcode']])
    return response



@login_required
def show_graph_by_month(request):
    
    kwargs = {}
    if request.method == 'POST':
        if "from_month_year" in request.POST:
            from_month_year = request.POST['from_month_year']
            from_year       = int(request.POST['from_month_year'][0:4])
            from_month      = int(request.POST['from_month_year'][5:7])
        else:
            from_month_year = ''
            from_year       = ''
            from_month      = ''

        comp_months = variable_value(request,'comp_months')
        destination = variable_value(request,'destination')
        destination_type = variable_value(request,'destination_type')
        source = variable_value(request,'source')
        source_type = variable_value(request,'source_type')
        channel = variable_value(request,'channel')

        dst = source_desti_field_chk(destination,destination_type,'dst')
        for i in dst:
            kwargs[i] = dst[i]

        src = source_desti_field_chk(source,source_type,'src')
        for i in src:
            kwargs[i] = src[i]

        if channel!='':
            kwargs[ 'channel' ] = channel

        if comp_months != '':
            from_day = validate_days(from_year,from_month,31)
            end_date = datetime(from_year, from_month, from_day)
            cp_month = int(comp_months) + 1
            start_date= end_date + relativedelta(months = -int(cp_month), days = +relative_days(from_day,from_year))
            kwargs[ 'start__range' ] = (start_date,end_date)

        form = MonthLoadSearchForm(initial={'from_month_year':from_month_year,'comp_months':comp_months,'destination':destination,'destination_type':destination_type,'source':source,'source_type':source_type,'channel':channel,})

    if len(kwargs) == 0:
        tday = datetime.today()
        from_year = tday.year
        from_month = tday.month
        from_day = validate_days(from_year,from_month,31)
        comp_months = 2
        cp_month = comp_months + 1
        form = MonthLoadSearchForm(initial={'from_month_year':tday.strftime("%Y-%m"),'comp_months':comp_months,'destination_type':1,'source_type':1,})
        end_date = datetime(from_year, from_month, from_day)
        start_date = end_date + relativedelta(months = -int(cp_month), days = +relative_days(from_day,from_year))
        kwargs[ 'start__range' ] = (start_date,end_date)


    total_month_list = []
    e_month=int(end_date.month)
    e_year=int(end_date.year)
    for i in range(cp_month):
        if e_month <= 12:
            total_month_list.append((e_month,e_year))
            e_month=e_month-1
            if e_month==0:
                e_month=12
                e_year=e_year-1
                
    if not request.user.is_superuser:
        kwargs[ 'accountcode' ] = request.user.get_profile().accountcode
    
    if kwargs:
        select_data = {"subdate": "SUBSTR(CAST(start as CHAR(30)),1,7)"}
        calls_min = CDR.objects.filter(**kwargs).extra(select=select_data).values('subdate').annotate(Sum('duration'))

        total_record = []
        m_list = []
        r_list = []
        n_list = []

        x=0
        for a in total_month_list:
            m_list.append((total_month_list[x][0]))
            x=x+1

        for b in calls_min:
            r_list.append((int(b['subdate'][6:8])))
            
        for c in m_list:
            if c not in r_list:
                n_list.append((c))
                
        x=0
        for j in total_month_list:
            if total_month_list[x][0] in n_list :
                total_record.append((total_month_list[x][0],total_month_list[x][1],0))
            x=x+1

        for j in calls_min:
            total_record.append(( int(j['subdate'][6:8]),int(j['subdate'][0:4]),j['duration__sum']))

        #print sorted(total_record, key=lambda total: total[1])
        variables = RequestContext(request,
                            {'module': current_view(request),
                             'form': form,
                             'result':'min',
                             'total_record':sorted(total_record, key=lambda total: total[1]),
                             'comp_months':comp_months,
                             'calls_min':calls_min,
                            })
                            
        return render_to_response('cdr/show_graph_by_month.html', variables,
               context_instance = RequestContext(request))

@login_required
def show_graph_by_day(request):

    kwargs = {}
    tday = datetime.today()
    if request.method == 'POST':
        if "from_date" in request.POST:
            from_date        = datetime(int(request.POST['from_date'][0:4]), int(request.POST['from_date'][5:7]), int(request.POST['from_date'][8:10]), 0, 0, 0, 0)
        else:
            from_date        = tday

        destination = variable_value(request,'destination')
        destination_type = variable_value(request,'destination_type')
        source = variable_value(request,'source')
        source_type = variable_value(request,'source_type')
        channel = variable_value(request,'channel')

        dst = source_desti_field_chk(destination,destination_type,'dst')
        for i in dst:
            kwargs[i] = dst[i]

        src = source_desti_field_chk(source,source_type,'src')
        for i in src:
            kwargs[i] = src[i]

        if channel!='':
            kwargs[ 'channel' ] = channel

        if from_date != '':
            start_date = datetime(from_date.year,from_date.month,from_date.day,0,0,0,0)
            end_date = datetime(from_date.year,from_date.month,from_date.day,23,59,59,999999)
            kwargs[ 'start__range' ] = (start_date,end_date)


        form = DailyLoadSearchForm(initial={'from_date':from_date.strftime('%Y-%m-%d'),'destination':destination,'destination_type':destination_type,'source':source,'source_type':source_type,'channel':channel,})

    if len(kwargs) == 0:
        tday=datetime.today()
        from_day = validate_days(tday.year,tday.month,tday.day)
        form = DailyLoadSearchForm(initial={'from_date':tday.strftime('%Y-%m-%d'),'destination_type':1,'source_type':1,})
        from_year=tday.year
        from_month= tday.month
        start_date = datetime(from_year,from_month,from_day,0,0,0,0)
        end_date = datetime(from_year,from_month,from_day,23,59,59,999999)
        kwargs[ 'start__range' ] = (start_date,end_date)

    if not request.user.is_superuser:
        kwargs[ 'accountcode' ] = request.user.get_profile().accountcode

    if kwargs:
        select_data = {"called_time": "SUBSTR(CAST(start as CHAR(30)),12,2)"} # get Hour
        calls_in_day = CDR.objects.filter(**kwargs).extra(select=select_data).values('called_time').annotate(Count('start'))#.order_by('-start')#
        #calls_in_day = CDR.objects.filter(**kwargs).extra(select={'hour': "django_date_trunc('hour', %s.start)" % CDR._meta.db_table}).values('hour').annotate(Count('start'))#.order_by('-start')#

        total_record = []

        if calls_in_day.count()!=0:
            total_record = []
            list_of_hour = []
            for i in calls_in_day:
                list_of_hour.append((int(i['called_time'])))

            for i in range(0,24):
                if i not in list_of_hour:
                    total_record.append((i,0))

            for i in calls_in_day:
                total_record.append((int(i['called_time']),int(i['start__count']) ))

        variables = RequestContext(request,
                            {'module': current_view(request),
                             'form': form,
                             'result':'min',
                             'report_date':start_date,
                             'total_record':sorted(total_record, key=lambda total: total[0]),
                             'calls_in_day':calls_in_day,
                            })

        return render_to_response('cdr/show_graph_by_day.html', variables,
               context_instance = RequestContext(request))

@login_required
def show_graph_by_hour(request):

    kwargs = {}
    graph_view = '1'
    tday = datetime.today()
    if request.method == 'POST':
        if "from_date" in request.POST:
            from_date        = request.POST['from_date']
            select_date = datetime(int(from_date[0:4]), int(from_date[5:7]), int(from_date[8:10]), 0, 0, 0, 0)
        else:
            from_date      = tday.strftime('%Y-%m-%d')
            select_date = tday

        comp_days = variable_value(request,'comp_days')
        destination = variable_value(request,'destination')
        destination_type = variable_value(request,'destination_type')
        source = variable_value(request,'source')
        source_type = variable_value(request,'source_type')
        channel = variable_value(request,'channel')
        graph_view = variable_value(request,'graph_view')
        
        dst = source_desti_field_chk(destination,destination_type,'dst')
        for i in dst:
            kwargs[i] = dst[i]
       
        src = source_desti_field_chk(source,source_type,'src')
        for i in src:
            kwargs[i] = src[i]

        if channel!='':
            kwargs[ 'channel' ] = channel

        if from_date != '':
            end_date = select_date
            start_date= end_date+relativedelta(days=-int(comp_days))
            start_date = datetime(start_date.year, start_date.month, start_date.day,0,0,0,0)
            end_date = datetime(end_date.year, end_date.month, end_date.day,23,59,59,999999)

            kwargs[ 'start__range' ] = (start_date,end_date)

        form = CompareCallSearchForm(initial={'select_date':from_date,'comp_days':comp_days,'destination':destination,'destination_type':destination_type,'source':source,'source_type':source_type,'channel':channel,'graph_view':graph_view,})

    if len(kwargs) == 0:
        tday = datetime.today()
        from_day = validate_days(tday.year,tday.month,tday.day)
        form = CompareCallSearchForm(initial={'from_date':tday.strftime('%Y-%m-%d'),'comp_days':2,'destination_type':1,'source_type':1,'graph_view':graph_view})
        from_year=tday.year
        from_month= tday.month

        end_date = datetime(from_year, from_month, from_day)
        start_date= end_date+relativedelta(days=-2)
        start_date = datetime(start_date.year, start_date.month, start_date.day,0,0,0,0)
        end_date = datetime(end_date.year, end_date.month, end_date.day,23,59,59,999999)

        kwargs[ 'start__range' ] = (start_date,end_date)

    if not request.user.is_superuser:
        kwargs[ 'accountcode' ] = request.user.get_profile().accountcode
    
    if kwargs:
        select_data = {"called_time": "SUBSTR(CAST(start as CHAR(30)),1,16)"} # Date without seconds
        if graph_view == '1':
            calls_in_day = CDR.objects.filter(**kwargs).extra(select=select_data).values('called_time').annotate(Count('start'))#.order_by('-start')#
        else:
            calls_in_day = CDR.objects.filter(**kwargs).extra(select=select_data).values('called_time').annotate(Sum('duration'))

        record_dates = []
        total_record = []
        total_call_count = []
        dateList = date_range( datetime(start_date.year, start_date.month,start_date.day), datetime(end_date.year, end_date.month, end_date.day))

        for i in calls_in_day:
            if datetime(int(i['called_time'][0:4]),int(i['called_time'][5:7]),int(i['called_time'][8:10])) in dateList:
                record_dates.append(( i['called_time'][0:4]+'-'+i['called_time'][5:7]+'-'+i['called_time'][8:10] ))
                if graph_view == '1':
                    total_record.append(( i['called_time'], i['start__count']))
                    total_call_count.append((i['start__count']))
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
                    string_date = i['called_time'][0:4]+'-'+i['called_time'][5:7]+'-'+i['called_time'][8:10]
                    if string_date == rd:
                        list_of_hour.append(int((i['called_time'][11:13])))
                        if graph_view == '1':
                            list_of_count.append((int(i['called_time'][11:13]),i['start__count']))
                            l_o_c[int(i['called_time'][11:13])]=i['start__count']
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
                sd=d.strftime('%Y-%m-%d')
                if sd not in record_dates:
                    for j in range(0,24):
                        total_record_final.append((sd,j,0))

            call_count_range=range(0,max(total_call_count)+1)
            call_count_range.reverse()
        else:
            call_count_range=[]
            total_record_final=[]

        datelist_final = []
        for i in dateList:  
            y =  str(i)
            datelist_final.append(( y[0:4]+'-'+y[5:7]+'-'+y[8:10] ))
        
        total_record = {}
        for i in total_record_final:
            if (i[0] in total_record.keys()) and (i[1] not in total_record[i[0]].keys()):
                total_record[i[0]][i[1]] = i[2]
            elif i[0] not in total_record.keys():
                total_record[i[0]] = {}
                total_record[i[0]][i[1]] = i[2]
        
        variables = RequestContext(request,
                            {'module': current_view(request),
                             'form': form,
                             'result':'min',
                             'record_dates':datelist_final,
                             'total_hour':range(0,24),
                             'graph_view':graph_view,
                             'call_count_range':call_count_range,
                             'total_record':total_record,
                             'calls_in_day':calls_in_day,
                            })

        return render_to_response('cdr/show_graph_by_hour.html', variables,
               context_instance = RequestContext(request))

def dictSort(d):
    """ returns a dictionary sorted by keys """
    our_list = d.items()
    our_list.sort()
    k = {}
    for item in our_list:
        k[item[0]] = item[1]
    return k
    
@login_required
def show_concurrent_calls(request):
    kwargs = {}
    graph_view = '1'
    
    if request.method == 'POST':        
        channel = variable_value(request,'channel')
        result = variable_value(request,'result')
    
    if ('result' not in vars()) or (result == ''):
        result = '1'
    
    now = datetime.now()
    if(result == '1'):
        start_date = datetime(now.year, now.month, now.day, 0, 0, 0, 0)
        end_date = datetime(now.year, now.month, now.day, 23, 59, 59, 0)
    elif(result == '2'):
        start_date = datetime(now.year, now.month, now.day, 0, 0, 0, 0) - relativedelta(days=1)
        end_date = datetime(now.year, now.month, now.day, 23, 59, 59, 0) - relativedelta(days=1)
    elif(result == '3'):
        start_date = datetime(now.year, now.month, now.day, 0, 0, 0, 0) - relativedelta(days=7)
        end_date = datetime(now.year, now.month, now.day, 23, 59, 59, 0)
    elif(result == '4'):
        start_date = datetime(now.year, now.month, now.day, 0, 0, 0, 0) - relativedelta(days=14)
        end_date = datetime(now.year, now.month, now.day, 23, 59, 59, 0) - relativedelta(days=7)
    elif(result == '5'):
        start_date = datetime(now.year, now.month, 1, 0, 0, 0, 0)
        end_date = datetime(now.year, now.month, now.day, 23, 59, 59, 0)
    elif(result == '6'):
        start_date = datetime(now.year, int(now.month), 1, 0, 0, 0, 0) - relativedelta(months=1)
        end_date = datetime(now.year, int(now.month), 1, 23, 59, 59, 0) - relativedelta(days=1)

    kwargs[ 'start__range' ] = (start_date,end_date)

    form = ConcurrentCallForm(initial={'result':result})

    if not request.user.is_superuser:
        kwargs[ 'accountcode' ] = request.user.get_profile().accountcode

    if kwargs:
        calls_in_day = CDR.objects.filter(**kwargs).values('start','duration').order_by('start')
        calls = {}

        time_calls = {}
        last_time = 0
        
        for data in calls_in_day:
            starttime = data['start']            
            int_starttime = int(starttime.strftime("%Y%m%d%H%M%S"))
            
            if int_starttime in time_calls.keys():
                time_calls[int_starttime] += 1
            else:
                time_calls[int_starttime] = 1
                
        concurrent_calls = {}
        for data in calls_in_day:
            starttime = data['start']
            endtime = starttime + timedelta(seconds=data['duration'])
            
            int_starttime = int(starttime.strftime("%Y%m%d%H%M%S"))
            int_endtime = int(endtime.strftime("%Y%m%d%H%M%S"))

            if int_starttime > last_time:
                for time in range(int_starttime, int_endtime - 1):
                    if int(result) < 5:
                        if time in time_calls.keys():
                            if str(time)[0:10] in concurrent_calls.keys():
                                if concurrent_calls[str(time)[0:10]] < time_calls[time]:
                                    concurrent_calls[str(time)[0:10]] = time_calls[time]
                            else:
                                concurrent_calls[str(time)[0:10]] = time_calls[time]
                    else:
                        if time in time_calls.keys():
                            if str(time)[0:8] in concurrent_calls.keys():
                                if concurrent_calls[str(time)[0:8]] < time_calls[time]:
                                    concurrent_calls[str(time)[0:8]] = time_calls[time]
                            else:
                                concurrent_calls[str(time)[0:8]] = time_calls[time]
                last_time = int_endtime

        maxconcurrent = 0
        total_call_count = 0
        for date in concurrent_calls:
            if (concurrent_calls[date] > maxconcurrent):
                maxconcurrent = concurrent_calls[date] 
        
        dates = date_range(start_date,end_date)
        dateList = []
        if result == '5':
            for i in range(1,now.day+1):
                if len(str(i)) <= 1:
                    j = '0' + str(i)
                else:
                    j = str(i)
                dateList.append(int(str(now.strftime("%Y%m") + j)))
        elif result == '6':
            for i in range(1,end_date.day+1):
                if len(str(i)) <= 1:
                    j = '0' + str(i)
                else:
                    j = str(i)
                dateList.append(int(str(start_date.strftime("%Y%m") + j)))
        else:
            for i in dates:
                for j in range(0,24):
                    if len(str(j)) <= 1:
                        j = '0' + str(j)
                    else:
                        j = str(j)
                        
                    dateList.append(int(i.strftime("%Y%m%d") + j))

        total_record = {}
        if int(result) < 5:
            for i in dateList:
                y =  str(i)[0:10]
                if y in concurrent_calls.keys():
                    if y[0:4]+'-'+y[4:6]+'-'+y[6:8] not in total_record.keys():
                        total_record[y[0:4]+'-'+y[4:6]+'-'+y[6:8]] = {int(y[8:10]): concurrent_calls[y]}
                    else:
                        total_record[y[0:4]+'-'+y[4:6]+'-'+y[6:8]][int(y[8:10])] = concurrent_calls[y]
                else:
                    if y[0:4]+'-'+y[4:6]+'-'+y[6:8] not in total_record.keys():
                        total_record[y[0:4]+'-'+y[4:6]+'-'+y[6:8]] = {int(y[8:10]): 0}
                    else:
                        total_record[y[0:4]+'-'+y[4:6]+'-'+y[6:8]][int(y[8:10])] = 0
        else:
            for i in dateList:
                y =  str(i)[0:8]
                month = _(datetime(int(y[0:4]), int(y[4:6]), int(y[6:8]), 0, 0, 0, 0).strftime("%B"))
                if y in concurrent_calls.keys():
                    if month not in total_record.keys():
                        total_record[month] = {int(y[6:8]): concurrent_calls[y]}
                    else:
                        total_record[month][int(y[6:8])] = concurrent_calls[y]
                else:
                    if month not in total_record.keys():
                        total_record[month] = {int(y[6:8]): 0}
                    else:
                        total_record[month][int(y[6:8])] = 0
        if int(result) < 5:
            graph_by = _('Hour')
        else:
            graph_by = _('Day')
            
        total_record_final = "["
        for dates in total_record:
            total_record_final += "{"
            total_record_final += "data: ["
            for hours in total_record[dates]:
                total_record_final += "[" + str(hours) + "," + str(total_record[dates][hours]) + "],"
            total_record_final += "],"
            date_string = _('%(month)s/%(day)s/%(year)s') % {'month':dates[5:7], 'day':dates[8:10], 'year':dates[0:4]}
            total_record_final += " label: \"" + date_string + "\""
            total_record_final += "},"
        total_record_final += "]"
        
        tickSize = 2
        if (maxconcurrent > 20):
            tickSize = 5
        elif (maxconcurrent > 100):
            tickSize = 10
        variables = RequestContext(request,
                            {'module': current_view(request),
                             'form': form,
                             'result': 'min',
                             'graph_view': graph_view,
                             'total_record': total_record_final,
                             'calls_in_day': calls_in_day,
                             'graph_by': graph_by,
                             'tickSize': tickSize,
                            })

    return render_to_response('cdr/show_graph_concurrent_calls.html', variables,
           context_instance = RequestContext(request))

@login_required
def show_global_report(request):
    template = 'cdr/show_global_report.html'
    kwargs = {}
    total_data = []

    if not request.user.is_superuser:
        kwargs[ 'accountcode' ] = request.user.get_profile().accountcode

    select_data = {"start": "SUBSTR(CAST(start as CHAR(30)),1,10)"}
    calls = CDR.objects.filter(**kwargs).extra(select=select_data).values('start').annotate(Sum('duration')).annotate(Avg('duration')).annotate(Count('start')).order_by('start')
    
    if calls:
        maxtime = datetime(int(calls[0]['start'][0:4]), int(calls[0]['start'][5:7]), int(calls[0]['start'][8:10]), 0, 0, 0, 0)
        mintime = datetime(int(calls[0]['start'][0:4]), int(calls[0]['start'][5:7]), int(calls[0]['start'][8:10]), 0, 0, 0, 0)
        calls_dict = {}
        
        for data in calls:
            time = datetime(int(data['start'][0:4]), int(data['start'][5:7]), int(data['start'][8:10]), 0, 0, 0, 0)
            if time > maxtime:
                maxtime = time
            elif time < mintime:
                mintime = time
            calls_dict[int(time.strftime("%Y%m%d"))] = {'start__count':data['start__count'], 'duration__sum':data['duration__sum'], 'duration__avg':data['duration__avg']}
        dateList = date_range(mintime, maxtime)
        
        
        i = 0
        for date in dateList:
            inttime = int(date.strftime("%Y%m%d"))
            name_date = _(date.strftime("%B")) + " " + str(date.day) + ", " + str(date.year)
            
            if inttime in calls_dict.keys():
                total_data.append({'count':i, 'day':date.day, 'month':date.month, 'year':date.year, 'date':name_date , 'start__count':calls_dict[inttime]['start__count'], 'duration__sum':calls_dict[inttime]['duration__sum'], 'duration__avg':calls_dict[inttime]['duration__avg']})
            else:
                total_data.append({'count':i, 'day':date.day, 'month':date.month, 'year':date.year, 'date':name_date , 'start__count':0, 'duration__sum':0, 'duration__avg':0})
            i += 1

    data = {'module': current_view(request),
            'total_data': total_data,
    }
    return render_to_response(template, data,context_instance = RequestContext(request))


@login_required
def show_dashboard(request):
    template = 'cdr/show_dashboard.html'
    debug = []
    kwargs = {}
    calls = ""
    
    now = datetime.now()
    
    start_date = datetime(now.year,now.month,now.day,0,0,0,0) - relativedelta(days=1)
    end_date = datetime(now.year,now.month,now.day,23,59,59,999999) - relativedelta(days=1)
    kwargs[ 'start__range' ] = (start_date,end_date)
    
    select_data = {"called_time": "SUBSTR(CAST(start as CHAR(30)),1,16)"} # Date without seconds
    calls = CDR.objects.filter(**kwargs).extra(select=select_data).values('called_time').annotate(Count('start')).annotate(Sum('duration'))#.order_by('-start')#
    
    total_calls = 0
    total_duration = 0
    total_record_final = []
    for data in calls:
        hour = float(data['called_time'][11:13])
        minute = math.ceil(float(data['called_time'][14:16])/60 * 100) / 100
        time = hour + minute
        total_record_final.append([str(time), data['start__count'], data['duration__sum']])
        total_calls += data['start__count']
        total_duration += data['duration__sum']
    
    ACT = math.floor(total_calls / 24)
    if total_calls==0:
        ACD = 0
    else:
        ACD = int_convert_to_minute(math.floor(total_duration / total_calls))
    
    label = start_date.strftime('%Y-%m-%d')
    
    
    

    variables = RequestContext(request,
                        {'module': current_view(request),
                         'label': label,
                         'total_calls': total_calls,
                         'total_duration': int_convert_to_minute(total_duration),
                         'ACT': ACT,
                         'ACD': ACD,
                         'total_record': total_record_final,
                        })

    return render_to_response(template, variables,
           context_instance = RequestContext(request))

def login_view(request):
    template = 'cdr/index.html'
    errorlogin = ''
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
                        errorlogin = _('Disabled Account') #True
                else:
                    # Return an 'invalid login' error message.
                    errorlogin = _('Invalid Login.') #True
            else:
                return HttpResponseRedirect('/')
    else :
        loginform = None;

    data = {
        'loginform' : loginform,
        'errorlogin' : errorlogin,
        'news' : get_news(),
        'is_authenticated' : request.user.is_authenticated()
    }
    return render_to_response(template, data,context_instance = RequestContext(request))


def logout_view(request):
	logout(request)
	return HttpResponseRedirect('/')


def index(request):
    template = 'cdr/index.html'
    errorlogin = ''
    loginform = loginForm()
    
    data = {'module': current_view(request),
            'loginform' : loginform,
            'errorlogin' : errorlogin,
            'news' : get_news(),
    }
    return render_to_response(template, data,
           context_instance = RequestContext(request))


def pleaselog(request):
    template = 'cdr/index.html'
    loginform = loginForm()
    
    data = {
        'loginform' : loginform,
        'notlogged' : True,
        'news' : get_news(),
    }
    return render_to_response(template, data,
           context_instance = RequestContext(request))

def current_view(request):
    name = getmodule(stack()[1][0]).__name__
    return stack()[1][3]


from django.shortcuts import get_object_or_404
import locale
locale.setlocale( locale.LC_ALL, '' )
from xlwt import *

def excelHeadings(headings, ws, row=0):
    fnt = Font()
    fnt.height = 240 #  multiplying the point size by 20
    fnt.bold = True
    fnt.name = 'Times New Roman'
    styleheader = XFStyle()
    styleheader.font = fnt
    
    for i in range(0,len(headings)):
        ws.write(row,i, headings[i], styleheader)

def download_invoice(request, invoiceid):
    locale.setlocale( locale.LC_ALL, '' )
    invoice = get_object_or_404(Invoice, pk = invoiceid)
    wb = Workbook(encoding='utf-8')
    wb.country_code = 61
    
    # Set up the Styles that will be used
    styledate = XFStyle()
    styledate.num_format_str = 'DD/MM/YY h:mm:ss AM/PM'
    styledateHeading = XFStyle()
    styledateHeading.num_format_str = 'DD/MM/YY'
    styletime = XFStyle()
    styletime.num_format_str = 'h:mm:ss'
    stylemoney = XFStyle()
    stylemoney .num_format_str = '$0.00'
    fnt = Font()
    fnt.height = 240 #  multiplying the point size by 20
    fnt.bold = True
    fnt.name = 'Times New Roman'
    styleheader = XFStyle()
    styleheader.font = fnt
    
    # Create an invoice work sheet
    wst = wb.add_sheet('Invoice')
    wst.write(0,0,'Company', styleheader)
    wst.write(0,1, invoice.company.name, styleheader)
    wst.write(1,0, 'Period start',styleheader)
    wst.write(1,1, invoice.start,styledateHeading)
    wst.write(2,0, 'Period end',styleheader)
    wst.write(2,1, invoice.end,styledateHeading)    
    headings = ['Classification','Number of calls','Total Duration','Charges', 'Cost']
    for i in range(0,len(headings)):
        wst.write(4,i, headings[i], styleheader)
    
    # Get all of the unique classification objects that relate to this invoice
    ratetable = AccountCode.objects.filter(company=invoice.company).values('ratetable')
    rate = Rate.objects.filter(ratetable__in=ratetable).values('classification')
    rate = rate.distinct()
    clas = Classification.objects.filter(pk__in=rate)
    clas = clas.distinct()
    
    # For each classification create a new worksheet and add to invoice totals
    totalcnt = totaltime = totalcost = totalbill =  0
    wstpos = 1
    ws = []
    for c in clas:
       
       cdr = InvoiceDetail.objects.select_related(depth=2).filter(invoice=invoice, classification=c)
       subcost = subtime = subcount = subbill = 0
       if cdr:
           ws.append(wb.add_sheet(c.name))
           w = len(ws)-1
           headings = ['Account Code','Date Time','Source','Destination','Billed Time','Cost']
           for i in range(0,len(headings)):
               ws[w].write(0,i, headings[i], styleheader)
       
           for d in range(0,len(cdr)):
               # write the individual call detail
               ws[w].write(d+1,0,cdr[d].call.accountcode.accountcode)
               ws[w].write(d+1,1,cdr[d].call.start, styledate)
               ws[w].write(d+1,2,cdr[d].call.src)
               ws[w].write(d+1,3,cdr[d].call.dst)
               ws[w].write(d+1,4,time.strftime('%H:%M:%S', time.gmtime(cdr[d].call.billsec)),styletime)
               ws[w].write(d+1,5,locale.currency(cdr[d].bill, grouping=False, symbol=True),stylemoney)
               subcost += cdr[d].cost
               subtime += cdr[d].call.billsec
               subbill += cdr[d].bill
               totalcost += cdr[d].cost
               totaltime += cdr[d].call.billsec
               totalbill += cdr[d].bill

       wstpos += 1
       
       #Invoice sheet, populate the subtotals
       wst.write(wstpos+5,0, c.name)
       wst.write(wstpos+5,1, len(cdr) )
       wst.write(wstpos+5,2, time.strftime('%H:%M:%S', time.gmtime(subtime)),styletime)
       wst.write(wstpos+5,3, subbill, stylemoney)
       wst.write(wstpos+5,4, subcost, stylemoney)
       totalcnt += len(cdr)
       
    wstpos += 6
    # Invoice sheet, populate the Totals
    wst.write(wstpos,0, 'Total', styleheader)
    wst.write(wstpos,1, totalcnt)
    wst.write(wstpos,2, time.strftime('%H:%M:%S', time.gmtime(totaltime)),styletime)
    wst.write(wstpos,3, totalbill, stylemoney)
    wst.write(wstpos,4, totalcost, stylemoney)
    
    wb.save('callaccounting.xls') # TODO: should append the time stamp to file name to prevent 2nd request from smashing this one.  Liklyhood is small
    
    filename = "Invoice_{0}_ID_{1}.xls".format(invoice.company.name, invoice.id) 
    response = HttpResponse(open('callaccounting.xls','r').read(), mimetype='application/ms-excel')
    response['Content-Disposition'] = 'attachment;filename='+filename     # force download.
    return response


def calculate_call_cost(call, rate):
    """ returns the calculated call cost """
    cost = 0.00
    if call.billsec > 0:
        if rate.flagfall: cost = float(rate.flagfall)
        if rate.firstrate: cost += float(rate.firstrate)
        if rate.interval: # incase the interval has not been specified
            if call.billsec > rate.interval :
                 cost += float(
                    ((call.billsec / rate.interval) - 1 + bool(call.billsec % rate.interval)) * rate.remainingrate 
                    )
    else:
        cost = 0
    return cost


def generate_invoice(request, invoiceid):
    """ Generates invoice details by populating the InvoiceDetail object with billing data for the supplied invoice"""
    response = "<h1> Results from invoice generation</h1>"
    callcnt = 0
    # determin what classification objects are used with the customer
    invoice = Invoice.objects.get(pk = invoiceid)
    ratetable = AccountCode.objects.filter(company=invoice.company).values('ratetable')
    rate = Rate.objects.filter(ratetable__in=ratetable).values('classification')
    rate = rate.distinct()
    classes = Classification.objects.filter(pk__in=rate)
    classes = classes.distinct()
    
    #for each classification, find calls that match it, determine call cost and populate InvoiceDetail
    for clas in classes:
        response +=  "Classification: {0}".format(clas)
        # Note: we are ignoring the AMAflag as it often is not populated correctly. Instead if the call goes out via the selected channel in the Classification object, bill it.  Less stuff ups this way
        cdrfilter = {'dst__regex':clas.regex, 'dstchannel__startswith':clas.channel,'start__gt':invoice.start, 'start__lt':invoice.end, 'accountcode__company':invoice.company,'disposition':1 }
        cdrdata = CDR.objects.filter(**cdrfilter)
        response += "Calls found {0} <br>".format(len(cdrdata))
        for call in cdrdata:
            billrate = Rate.objects.get(ratetable=call.accountcode.ratetable, classification=clas) # might get more then one response!
            if not billrate:
                response += "No rate for this call! Classification: {0}, account code: {0}<br>".format(clas.name, call.accountcode)
                bill = 0
            else:
                bill = calculate_call_cost(call, billrate)
                costrate = CostRateTable.objects.filter(classification=clas)
                if not costrate:
                    cost = 0
                else:
                    cost = calculate_call_cost(call, costrate[0])
            # check if the call has already been added
            oldcall= InvoiceDetail.objects.filter(call=call, invoice=invoice)
            if oldcall:
                # Allows running the invoice again if the rates were updated.
                oldcall[0].cost = "%.15g" % cost
                oldcall[0].bill = "%.15g" % bill
                oldcall[0].save()
            else:                
                newcall = InvoiceDetail(call=call, invoice=invoice, classification=clas, cost="%.15g" % cost, bill="%.15g" % bill)
                newcall.save()
            callcnt += 1
    response += "Completed. {0} calls processed".format(callcnt)
    # TODO show calls that do not have a classification therfor missing in the invoice
    return HttpResponse(response)


def clear_invoice(request, invoiceid):
    """ deletes all date for the invoice """
    invoice = Invoice.objects.get(pk = invoiceid)
    cnt = InvoiceDetail.objects.filter(invoice=invoice).count()
    InvoiceDetail.objects.filter(invoice=invoice).delete()
    response = "<h1> Completed</h1> Cleared {0} calls from this invoice, its now empty".format(cnt)
    return HttpResponse(response)


