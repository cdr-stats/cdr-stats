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
    if request.method == 'GET':        
        if "from_day" in request.GET:
            # From
            from_day            = int(request.GET['from_day'])
            from_month_year     = request.GET['from_month_year']
            from_year           = int(request.GET['from_month_year'][0:4])
            from_month          = int(request.GET['from_month_year'][5:7])
            from_day            = validate_days(from_year, from_month, from_day)
            start_date          = datetime(from_year, from_month, from_day, 0, 0, 0, 0)

            # To
            to_day              = int(request.GET['to_day'])
            to_month_year       = request.GET['to_month_year']
            to_year             = int(request.GET['to_month_year'][0:4])
            to_month            = int(request.GET['to_month_year'][5:7])
            to_day              = validate_days(to_year, to_month, to_day)
            end_date            = datetime(to_year, to_month, to_day, 23, 59, 59, 999999)
    
    try:
        from_day
    except NameError:
        #print "well, it WASN'T defined after all!"
        tday = datetime.today()
        from_day = 1
        to_year = from_year = tday.year
        to_month = from_month = tday.month
        from_month_year = str(to_year) + '-' + str(to_month)
        to_month_year = str(to_year) + '-' + str(to_month)
        to_day = validate_days(tday.year,tday.month,31)
        
        start_date = datetime(from_year, from_month, from_day, 0, 0, 0, 0)
        end_date = datetime(to_year, to_month, to_day)
        
    kwargs[ 'calldate__range' ] = (start_date, end_date)
    
    result = variable_value(request,'result')
    if result == '':
        result = '1'
    request.session['cdr_queryset'] = ''

    select_data = {"calldate": "strftime('%%Y-%%m-%%d', calldate)"}
    
    request.session['cdr_queryset'] = CDR.objects.values('calldate', 'channel', 'src', 'clid', 'dst', 'disposition', 'duration').filter(**kwargs).order_by('-calldate')
    total_data = CDR.objects.extra(select=select_data).values('calldate').filter(**kwargs).annotate(Count('calldate')).annotate(Sum('duration')).annotate(Avg('duration')).order_by('-calldate')
    form = CdrSearchForm(initial={'from_day':from_day,'from_month_year':from_month_year,'to_day':to_day,'to_month_year':to_month_year,'result':result,'export_csv_queryset':'0'})
    
    if result == '1':
        for i in request.session['cdr_queryset']:
            i['duration'] = int_convert_to_minute(int(i['duration']))

    if total_data.count() != 0:
        max_duration = max([x['duration__sum'] for x in total_data])
        total_duration = sum([x['duration__sum'] for x in total_data])
        total_calls = sum([x['calldate__count'] for x in total_data])
        total_avg_duration = (sum([x['duration__avg'] for x in total_data]))/total_data.count()
    else:
        max_duration = 0
        total_duration = 0
        total_calls = 0
        total_avg_duration = 0

    variables = RequestContext(request, { 'form': form,
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
    writer.writerow(['Calldate', 'Channel', 'Source', 'Clid','Destination','Disposition','Duration'])
    for cdr in qs:
        writer.writerow([cdr['calldate'], cdr['channel'], cdr['src'], cdr['clid'], cdr['dst'], cdr['disposition'], cdr['duration']])
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
            kwargs[ 'calldate__range' ] = (start_date,end_date)

        form = MonthLoadSearchForm(initial={'from_month_year':from_month_year,'comp_months':comp_months,'destination':destination,'destination_type':destination_type,'source':source,'source_type':source_type,'channel':channel,})

    if len(kwargs) == 0:
        form = MonthLoadSearchForm(initial={'comp_months':2,'destination_type':1,'source_type':1,})
        tday = datetime.today()
        from_year = tday.year
        from_month = tday.month
        from_day = validate_days(from_year,from_month,31)
        comp_months = 2
        cp_month = comp_months + 1
        end_date = datetime(from_year, from_month, from_day)
        start_date = end_date + relativedelta(months = -int(cp_month), days = +relative_days(from_day,from_year))
        kwargs[ 'calldate__range' ] = (start_date,end_date)


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

    if kwargs:
        select_data = {"subdate": "strftime('%%m-%%Y', calldate)"}
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
            r_list.append((int(b['subdate'][0:2])))
            
        for c in m_list:
            if c not in r_list:
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

@login_required
def show_graph_by_day(request):

    kwargs = {}
    if request.method == 'POST':
        if "from_month_year" in request.POST:
            from_day        = int(request.POST['from_day'])
            from_month_year = request.POST['from_month_year']
            from_year       = int(request.POST['from_month_year'][0:4])
            from_month      = int(request.POST['from_month_year'][5:7])
        else:
            from_day        = ''
            from_month_year = ''
            from_year       = ''
            from_month      = ''

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

        if from_day != '':
            start_date = datetime(from_year,from_month,from_day,0,0,0,0)
            end_date = datetime(from_year,from_month,from_day,23,59,59,999999)
            kwargs[ 'calldate__range' ] = (start_date,end_date)


        form = DailyLoadSearchForm(initial={'from_day':from_day,'from_month_year':from_month_year,'destination':destination,'destination_type':destination_type,'source':source,'source_type':source_type,'channel':channel,})

    if len(kwargs) == 0:
        tday=datetime.today()
        from_day = validate_days(tday.year,tday.month,tday.day)
        form = DailyLoadSearchForm(initial={'from_day':tday.day,'destination_type':1,'source_type':1,})
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

@login_required
def show_graph_by_hour(request):

    kwargs = {}
    if request.method == 'POST':
        if "from_month_year" in request.POST:
            from_day        = int(request.POST['from_day'])
            from_month_year = request.POST['from_month_year']
            from_year       = int(request.POST['from_month_year'][0:4])
            from_month      = int(request.POST['from_month_year'][5:7])
        else:
            from_day        = ''
            from_month_year = ''
            from_year       = ''
            from_month      = ''

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
        form = CompareCallSearchForm(initial={'from_day':tday.day,'comp_days':2,'destination_type':1,'source_type':1,'graph_view':1})
        from_year=tday.year
        from_month= tday.month
        graph_view = 1

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
        'news':get_news(),
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
    
    # Create the form
    form = MonthLoadSearchForm()

    # create a formHelper
    helper = FormHelper()

    # Add in a class and id
    helper.form_id = 'this-form-rocks'
    helper.form_class = 'search'

    # add in a submit and reset button
    submit = Submit('search','search this site')
    helper.add_input(submit)
    reset = Reset('reset','reset button')
    helper.add_input(reset)
    helper.use_csrf_protection = True

    data = {
        'loginform' : loginform,
        'testform' : form,
        'testformhelper' : helper,
        'errorlogin' : errorlogin,
        'news':get_news(),
    }
    return render_to_response(template, data,
           context_instance = RequestContext(request))

