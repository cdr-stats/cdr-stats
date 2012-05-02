#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2012 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import password_reset, password_reset_done,\
password_reset_confirm, password_reset_complete
from django.db.models import *
from django.db.models.loading import get_model
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.core.mail import send_mail, mail_admins
from django.template.context import RequestContext
from django.utils.translation import gettext as _
from django.conf import settings
from common.common_functions import *
from cdr.forms import *
from cdr.models import *
from cdr.mapreduce import *

from pymongo import *
from pymongo.objectid import ObjectId

from datetime import *
from dateutil import parser
from dateutil.relativedelta import *

import operator
import calendar, time, string
import csv, codecs
import logging

TOTAL_GRAPH_COLOR = '#A61700'
DISPLAY_NO_OF_COUNTRY = 10

news_url = settings.NEWS_URL

cdr_data = settings.DB_CONNECTION[settings.CDR_MONGO_CDR_COMMON]
#db.cdr.ensureIndex({"variables.answer_stamp":1}, {background:true});


(map, reduce, finalize_fun, out) = mapreduce_cdr_view()


def common_send_notification(request, status, recipient=None):
    """User Notification (e.g. limit) needs to be saved.
    It is a common function for the admin and customer UI's

    **Attributes**:

        * ``request`` - primary key of the record
        * ``status`` - get label for notifications
        * ``recipient`` - receiver of notification

    **Logic Description**:

        get the notice label from stauts & send notification with
        recipient, from_user & sender detail
    """
    if not recipient:
        recipient = request.user
        sender = User.objects.get(is_superuser=1, username=recipient)
    else:
        if request.user.is_anonymous():
            sender = User.objects.get(is_superuser=1, username=recipient)
        else:
            sender = request.user

    if notification:
        note_label = notification.NoticeType.objects.get(default=status)
        notification.send([recipient],
                          note_label.label,
                          {"from_user": request.user},
                          sender=sender)
    return True


def check_cdr_data_exists(request):
    doc = cdr_data.find_one()
    if not doc:
        return False
    else:
        return True
    

def login_view(request):
    """Login view

    **Attributes**:

        * ``template`` - cdr/index.html
        * ``form`` - loginForm
    """

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
        'news' : get_news(news_url),
        'is_authenticated' : request.user.is_authenticated()
    }
    return render_to_response(template, data,context_instance = RequestContext(request))


def logout_view(request):
	logout(request)
	return HttpResponseRedirect('/')


@login_required
def cdr_view(request):
    """List of CDRs

    **Attributes**:

        * ``template`` - cdr/cdr_view.html
        * ``form`` - CdrSearchForm
        * ``mongodb_data_set`` - CDR_MONGO_CDR_COMMON
        * ``map_reduce`` - mapreduce_cdr_view()

    **Logic Description**:

        get the call records as well as daily call analytics
        from mongodb collection according to search parameters
    """

    if not check_cdr_data_exists(request):
        return render_to_response('cdr/error_import.html', context_instance=RequestContext(request))
    template_name = 'cdr/cdr_view.html'
    logging.debug('CDR View Start')
    query_var = {}
    result = 1 # default min
    switch_id = 0 # default all
    hangup_cause_id = 0 #default all
    destination = ''
    destination_type = ''
    dst = ''
    accountcode = ''
    accountcode_type = ''
    acc = ''
    direction = ''
    duration = ''
    duration_type = ''
    due = ''
    caller = ''
    caller_type = ''
    cli = ''
    search_tag = 0
    action = 'tabs-1'
    menu = 'on'
    if request.method == 'POST':
        logging.debug('CDR Search View')
        search_tag = 1
        request.session['session_search_tag'] = search_tag
        form = CdrSearchForm(request.POST)
        if form.is_valid():
            if "from_date" in request.POST:
                # From
                from_date = request.POST['from_date']
                start_date = datetime(int(from_date[0:4]),
                                      int(from_date[5:7]),
                                      int(from_date[8:10]), 0, 0, 0, 0)
                request.session['session_from_date'] = from_date

            if "to_date" in request.POST:
                # To
                to_date = request.POST['to_date']
                end_date = datetime(int(to_date[0:4]),
                                    int(to_date[5:7]),
                                    int(to_date[8:10]), 23, 59, 59, 999999)
                request.session['session_to_date'] = to_date

            result = int(variable_value(request, 'result'))
            if result:
                request.session['session_result'] = result
            #print form.cleaned_data.get('destination')
            destination = variable_value(request, 'destination')
            destination_type = variable_value(request, 'destination_type')
            if destination:
                request.session['session_destination'] = destination
                request.session['session_destination_type'] = destination_type

            accountcode = variable_value(request, 'accountcode')
            accountcode_type = variable_value(request, 'accountcode_type')
            if accountcode:
                request.session['session_accountcode'] = accountcode
                request.session['session_accountcode_type'] = accountcode_type

            caller = variable_value(request, 'caller')
            caller_type = variable_value(request, 'caller_type')
            if caller:
                request.session['session_caller'] = caller
                request.session['session_accountcode_type'] = caller_type

            duration = variable_value(request, 'duration')
            duration_type = variable_value(request, 'duration_type')
            if duration:
                request.session['session_duration'] = duration
                request.session['session_duration_type'] = duration_type

            direction = variable_value(request, 'direction')
            if direction:
                request.session['session_direction'] = str(direction)

            switch_id = variable_value(request, 'switch')
            if switch_id:
                request.session['session_switch_id'] = switch_id

            hangup_cause_id = variable_value(request, 'hangup_cause')
            if hangup_cause_id:
                request.session['session_hangup_cause_id'] = hangup_cause_id

            records_per_page = variable_value(request, 'records_per_page')
            if records_per_page:
                request.session['session_records_per_page'] = records_per_page

            country_id = variable_value(request, 'country_id')
            # convert list value in int
            country_id = [int(row) for row in country_id]
            if len(country_id) >= 1:
                request.session['session_country_id'] = country_id
        else:
            # form is not valid
            logging.debug('Error : CDR search form')
            docs = []
            docs_pages = 0
            PAGE_SIZE = settings.PAGE_SIZE
            total_data = []
            total_duration = 0
            total_calls = 0
            total_avg_duration = 0
            max_duration = 0
            col_name_with_order = []
            detail_data = []
            tday = datetime.today()
            start_date = tday.strftime('%Y-%m-01')
            last_day = ((datetime(tday.year, tday.month, 1, 23, 59, 59, 999999) + relativedelta(months=1)) - relativedelta(days=1)).strftime('%d')
            end_date = tday.strftime('%Y-%m-'+last_day)
            template_data = {'module': current_view(request),
                             'rows': docs,
                             'form': form,
                             'pages': docs_pages,
                             'PAGE_SIZE': PAGE_SIZE,
                             'total_data': detail_data,
                             'total_duration': total_duration,
                             'total_calls': total_calls,
                             'total_avg_duration': total_avg_duration,
                             'max_duration': max_duration,
                             'user': request.user,
                             'search_tag': search_tag,
                             'col_name_with_order': col_name_with_order,
                             'menu': menu,
                             'start_date': start_date,
                             'end_date': end_date,
                             'action': action,
                             }
            logging.debug('CDR View End')
            return render_to_response(template_name, template_data,
                context_instance=RequestContext(request))

    try:
        menu = request.GET.get('menu')
    except:
        menu = 'on'

    try:
        if request.GET.get('page') or request.GET.get('sort_by'):
            from_date = request.session.get('session_from_date')
            to_date = request.session.get('session_to_date')
            destination = request.session.get('session_destination')
            destination_type = request.session.get('session_destination_type')
            accountcode = request.session.get('session_accountcode')
            accountcode_type = request.session.get('session_accountcode_type')
            caller = request.session.get('session_caller')
            caller_type = request.session.get('session_caller_type')
            duration = request.session.get('session_duration')
            duration_type = request.session.get('session_duration_type')
            direction = request.session.get('session_direction')
            switch_id = request.session.get('session_switch_id')
            hangup_cause_id = request.session.get('session_hangup_cause_id')
            result = request.session.get('session_result')
            search_tag = request.session.get('session_search_tag')
            records_per_page = request.session.get('session_records_per_page')
            country_id = request.session['session_country_id']
        else:
            from_date
    except NameError:
        tday = datetime.today()
        from_date = tday.strftime('%Y-%m-01')
        last_day = ((datetime(tday.year, tday.month, 1, 23, 59, 59, 999999) + relativedelta(months=1)) - relativedelta(days=1)).strftime('%d')
        to_date = tday.strftime('%Y-%m-'+last_day)
        search_tag = 0
        country_id = ''
        records_per_page = settings.PAGE_SIZE
        # unset session var value
        request.session['session_result'] = ''
        request.session['session_from_date'] = from_date
        request.session['session_to_date'] = to_date
        request.session['session_destination'] = ''
        request.session['session_destination_type'] = ''
        request.session['session_accountcode'] = ''
        request.session['session_accountcode_type'] = ''
        request.session['session_caller'] = ''
        request.session['session_caller_type'] = ''
        request.session['session_duration'] = ''
        request.session['session_duration_type'] = ''
        request.session['session_hangup_cause_id'] = ''
        request.session['session_switch_id'] = ''
        request.session['session_direction'] = ''
        request.session['session_search_tag'] = search_tag
        request.session['session_records_per_page'] = records_per_page
        request.session['session_country_id'] = ''

    start_date = datetime(int(from_date[0:4]), int(from_date[5:7]), int(from_date[8:10]), 0, 0, 0, 0)
    end_date = datetime(int(to_date[0:4]), int(to_date[5:7]), int(to_date[8:10]), 23, 59, 59, 999999)
    query_var['start_uepoch'] = {'$gte': start_date, '$lt': end_date}

    dst = source_desti_field_chk_mongodb(destination, destination_type)
    if dst:
        query_var['destination_number'] = dst

    if request.user.is_superuser: # superuser
        acc = source_desti_field_chk_mongodb(accountcode, accountcode_type)
        if acc:
            query_var['accountcode'] = acc

    if not request.user.is_superuser: # not superuser
        if not chk_account_code(request):
            return HttpResponseRedirect('/?acc_code_error=true')
        else:
            query_var['accountcode'] = chk_account_code(request)


    cli = source_desti_field_chk_mongodb(caller, caller_type)
    if cli:
        query_var['caller_id_number'] = cli

    due = duration_field_chk_mongodb(duration, duration_type)
    if due:
        query_var['duration'] = due

    if switch_id and int(switch_id) != 0:
        query_var['switch_id'] = int(switch_id)

    if hangup_cause_id and int(hangup_cause_id) != 0:
        query_var['hangup_cause_id'] = int(hangup_cause_id)

    if direction:
        query_var['direction'] = str(direction)

    if len(country_id) >= 1 and country_id[0] != 0:
        query_var['country_id'] = {'$in': country_id}

    final_result = cdr_data.find(query_var)
    total_result_count = cdr_data.find(query_var).count()

    # Define no of records per page
    PAGE_SIZE = int(records_per_page)
    try:
        PAGE_NUMBER = int(request.GET['page'])
    except:
        PAGE_NUMBER = 1
        #PAGE_SIZE = settings.PAGE_SIZE

    docs = []
    docs_pages = []

    docs_pages = [[] for x in range(1, int(final_result.count()))]

    form = CdrSearchForm(initial={'from_date': from_date, 'to_date': to_date,
                                  'destination': destination, 'destination_type': destination_type,
                                  'accountcode': accountcode, 'accountcode_type': accountcode_type,
                                  'caller': caller, 'caller_type': caller_type,
                                  'duration': duration, 'duration_type': duration_type,
                                  'result': result, 'direction': direction,
                                  'hangup_cause': hangup_cause_id,
                                  'switch': switch_id, 'country_id': country_id,
                                  'records_per_page': records_per_page})

    request.session['query_var'] = query_var

    col_name_with_order = {}

    #TODO: Clean and optimize the col_name_with_order
    # default
    col_name_start_uepoch = '-start_uepoch'
    col_name_with_order['start_uepoch_up'] = col_name_start_uepoch[1:]
    col_name_with_order['start_uepoch_down'] = col_name_start_uepoch
    col_name_with_order['start_uepoch'] = col_name_start_uepoch

    col_name_caller_id_number = '-caller_id_number'
    col_name_with_order['caller_id_number_up'] = col_name_caller_id_number[1:]
    col_name_with_order['caller_id_number_down'] = col_name_caller_id_number
    col_name_with_order['caller_id_number'] = col_name_caller_id_number

    col_name_destination_number = '-destination_number'
    col_name_with_order['destination_number_up'] = col_name_destination_number[1:]
    col_name_with_order['destination_number_down'] = col_name_destination_number
    col_name_with_order['destination_number'] = col_name_destination_number

    col_name_duration = '-duration'
    col_name_with_order['duration_up'] = col_name_duration[1:]
    col_name_with_order['duration_down'] = col_name_duration
    col_name_with_order['duration'] = col_name_duration

    col_name_billsec = '-billsec'
    col_name_with_order['billsec_up'] = col_name_billsec[1:]
    col_name_with_order['billsec_down'] = col_name_billsec
    col_name_with_order['billsec'] = col_name_billsec

    col_name_hangup_cause = '-hangup_cause_id'
    col_name_with_order['hangup_cause_id_up'] = col_name_hangup_cause[1:]
    col_name_with_order['hangup_cause_id_down'] = col_name_hangup_cause
    col_name_with_order['hangup_cause_id'] = col_name_hangup_cause

    col_name_accountcode = '-accountcode'
    col_name_with_order['accountcode_up'] = col_name_accountcode[1:]
    col_name_with_order['accountcode_down'] = col_name_accountcode
    col_name_with_order['accountcode'] = col_name_accountcode

    sort_field = variable_value(request, 'sort_by')
    if not sort_field:
        sort_field = 'start_uepoch' # default sort field
        default_order = -1 # desc
    else:
        if "-" in sort_field:
            default_order = -1
            sort_field = sort_field[1:]
            col_name_with_order[sort_field] = sort_field
        else:
            default_order = 1
            col_name_with_order[sort_field] = '-' + sort_field

    col_name_with_order['sort_field'] = sort_field

    final_result = \
    final_result.skip(PAGE_SIZE * (PAGE_NUMBER - 1)).limit(PAGE_SIZE).sort([(sort_field, default_order)]).clone()
    logging.debug('Create cdr result')
    for i in final_result:
        # duration convert into min
        if result == 1 or result == '':
            duration = int_convert_to_minute(int(i['duration']))
            billsec = int_convert_to_minute(int(i['billsec']))
        else:
            duration = i['duration']
            billsec = i['duration']

        docs.append({
                     'id': i['cdr_object_id'],
                     'start_uepoch': i['start_uepoch'],
                     'caller_id_number': i['caller_id_number'],
                     'caller_id_name': i['caller_id_name'],
                     'destination_number': i['destination_number'],
                     'duration': duration,
                     'billsec': billsec,
                     'country': i['country_id'],
                     'hangup_cause': get_hangupcause_name(i['hangup_cause_id']),
                     'accountcode': i['accountcode'],
                     'direction': i['direction'],
                     'authorized': i['authorized'],
                     'switch_id': i['switch_id'],
                   })

    logging.debug('Map-reduce cdr analytic')
    #Retrieve Map Reduce
    (map, reduce, finalize_fun, out) = mapreduce_cdr_view()

    total_data = cdr_data.map_reduce(map, reduce, out, query=query_var, finalize=finalize_fun,)
    total_data = total_data.find().sort([('_id.a_Year', -1), ('_id.b_Month', -1), ('_id.c_Day', -1)])

    detail_data = []
    for doc in total_data:
        detail_data.append({'calldate': datetime(int(doc['_id']['a_Year']),
                                                 int(doc['_id']['b_Month']),
                                                 int(doc['_id']['c_Day'])),
                            'duration__sum': int(doc['value']['duration__sum']),
                            'calldate__count': int(doc['value']['calldate__count']),
                            'duration__avg': doc['value']['duration__avg'],
                            })

    if total_data.count() != 0:
        max_duration = max([int(x['value']['duration__sum']) for x in total_data.clone()])
        total_duration = sum([int(x['value']['duration__sum']) for x in total_data.clone()])
        total_calls = sum([int(x['value']['calldate__count']) for x in total_data.clone()])
        total_avg_duration = (sum([float(x['value']['duration__avg']) for x in total_data.clone()]))/total_data.count()
    else:
        max_duration = 0
        total_duration = 0
        total_calls = 0
        total_avg_duration = 0

    template_data = {'module': current_view(request),
                     'rows': docs,
                     'form': form,
                     'pages': docs_pages,
                     'PAGE_SIZE': PAGE_SIZE,
                     'total_data': detail_data,
                     'total_duration': total_duration,
                     'total_calls': total_calls,
                     'total_avg_duration': total_avg_duration,
                     'max_duration': max_duration,
                     'user': request.user,
                     'search_tag': search_tag,
                     'col_name_with_order': col_name_with_order,
                     'menu': menu,
                     'start_date': start_date,
                     'end_date': end_date,
                     'action': action,
                     }
    logging.debug('CDR View End')
    return render_to_response(template_name, template_data,
                              context_instance=RequestContext(request))


@login_required
def cdr_export_to_csv(request):
    """
    **Logic Description**:

        get the call records  from mongodb collection
        according to search parameters & store into csv file
    """
    # get the response object, this can be used as a stream
    response = HttpResponse(mimetype='text/csv')
    # force download
    response['Content-Disposition'] = 'attachment;filename=export.csv'
    # the csv writer
    writer = csv.writer(response)
    query_var = request.session['query_var']
    final_result = cdr_data.find(query_var).clone()

    writer.writerow(['Answer stamp', 'Clid', 'Destination',
                     'Duration', 'Bill sec', 'Hangup cause', 'AccountCode', 'Direction'])
    for cdr in final_result:
        writer.writerow([
                         cdr['start_uepoch'],
                         cdr['caller_id_number'].encode("utf-8") + '-' + cdr['caller_id_name'].encode("utf-8"),
                         cdr['destination_number'],
                         cdr['duration'],
                         cdr['billsec'],
                         get_hangupcause_name(cdr['hangup_cause_id']),
                         cdr['accountcode'].encode("utf-8"),
                         cdr['direction'].encode("utf-8")
                       ])
    return response


@login_required
def cdr_detail(request, id, switch_id):
    """Detail of Call

    **Attributes**:

        * ``template`` - cdr/cdr_detail.html

    **Logic Description**:

        get the single call record in detail from mongodb collection
    """
    c_switch = Switch.objects.get(id=switch_id)
    ipaddress = c_switch.ipaddress

    #Connect on MongoDB Database
    host = settings.CDR_MONGO_IMPORT[ipaddress]['host']
    port = settings.CDR_MONGO_IMPORT[ipaddress]['port']
    db_name = settings.CDR_MONGO_IMPORT[ipaddress]['db_name']
    try:
        connection = Connection(host, port)
        DB_CONNECTION = connection[db_name]
    except ConnectionFailure, e:
        raise Http404

    try:
        menu = request.GET.get('menu')
    except:
        menu = 'on'
    doc = DB_CONNECTION[settings.CDR_MONGO_IMPORT[ipaddress]['collection']].find({'_id': ObjectId(id)})
    return render_to_response('cdr/cdr_detail.html', {'row': list(doc), 'menu': menu,},
                              context_instance=RequestContext(request))


@login_required
def cdr_global_report(request):
    """CDR global report

    **Attributes**:

        * ``template`` - cdr/cdr_global_report.html
        * ``form`` - SwitchForm
        * ``mongodb_data_set`` - CDR_MONGO_CDR_COMMON
        * ``map_reduce`` - mapreduce_cdr_view()

    **Logic Description**:

        get all call records from mongodb collection to create
        global call report
    """

    if not check_cdr_data_exists(request):
        return render_to_response('cdr/error_import.html', context_instance=RequestContext(request))

    logging.debug('CDR global report view start')
    query_var = {}
    total_data = []
    form = SwitchForm()
    switch_id = 0
    if request.method == 'POST':
        logging.debug('CDR global report with search options')
        form = SwitchForm(request.POST)
        if form.is_valid():
            switch_id = form.cleaned_data.get('switch')
            if switch_id and int(switch_id) != 0:
                query_var['switch_id'] = int(switch_id)

    if not request.user.is_superuser: # not superuser
        acc_code_error = ''
        if chk_account_code(request):
            query_var['accountcode'] = chk_account_code(request)
        else:
            return HttpResponseRedirect('/?acc_code_error=true')

    logging.debug('Map-reduce cdr global report analytic')
    #Retrieve Map Reduce
    (map, reduce, finalize_fun, out) = mapreduce_cdr_view()

    #Run Map Reduce
    calls = cdr_data.map_reduce(map, reduce, out, query=query_var, finalize=finalize_fun,)
    calls = calls.find().sort([('_id.a_Year', -1), ('_id.b_Month', -1), ('_id.c_Day', -1)])
    
    if calls.count() != 0:
        maxtime = datetime(int(calls[0]['_id']['a_Year']),
                           int(calls[0]['_id']['b_Month']),
                           int(calls[0]['_id']['c_Day']), 0, 0, 0, 0)
        mintime = datetime(int(calls[0]['_id']['a_Year']),
                           int(calls[0]['_id']['b_Month']),
                           int(calls[0]['_id']['c_Day']), 0, 0, 0, 0)
        calls_dict = {}

        for d in calls:
            dtime = datetime(int(d['_id']['a_Year']),
                            int(d['_id']['b_Month']),
                            int(d['_id']['c_Day']), 0, 0, 0, 0)
            if dtime > maxtime:
                maxtime = dtime
            elif dtime < mintime:
                mintime = dtime
            calls_dict[int(dtime.strftime("%Y%m%d"))] = {'calldate__count': d['value']['calldate__count'],
                                                        'duration__sum': d['value']['duration__sum'],
                                                        'duration__avg': d['value']['duration__avg']}
        dateList = date_range(mintime, maxtime)

        i = 0
        for date in dateList:
            inttime = int(date.strftime("%Y%m%d"))
            name_date = _(date.strftime("%B")) + " " + str(date.day) + ", " + str(date.year)

            if inttime in calls_dict.keys():
                total_data.append({'count': i, 'day': date.day, 'month': date.month,
                                   'year': date.year, 'date': name_date ,
                                   'calldate__count': calls_dict[inttime]['calldate__count'],
                                   'duration__sum': calls_dict[inttime]['duration__sum'],
                                   'duration__avg': calls_dict[inttime]['duration__avg']})
            else:
                total_data.append({'count': i, 'day': date.day, 'month': date.month,
                                   'year': date.year, 'date': name_date ,
                                   'calldate__count': 0, 'duration__sum': 0, 'duration__avg': 0})
            i += 1

    # remove mapreduce output from database (no longer required)
    settings.DB_CONNECTION[out].drop()

    logging.debug('CDR global report view end')
    template_data = {'module': current_view(request),
                     'total_data': total_data,
                     'form': form,
                    }
    return render_to_response('cdr/cdr_global_report.html', template_data,
                              context_instance=RequestContext(request))


@login_required
def cdr_dashboard(request):
    """CDR dashboard for a current day

    **Attributes**:

        * ``template`` - cdr/cdr_dashboard.html
        * ``form`` - SwitchForm
        * ``mongodb_data_set`` - CDR_MONGO_CDR_COMMON
        * ``map_reduce`` - mapreduce_cdr_minute_report()

    **Logic Description**:

        get all call records from mongodb collection for current day
        to create hourly report as well as to hungupcause/country analytic
    """

    if not check_cdr_data_exists(request):
        return render_to_response('cdr/error_import.html', context_instance=RequestContext(request))

    logging.debug('CDR dashboard view start')
    now = datetime.now()
    form = SwitchForm()
    switch_id = 0
    query_var = {}
    search_tag = 0
    if request.method == 'POST':
        logging.debug('CDR dashboard view with search option')
        search_tag = 1
        form = SwitchForm(request.POST)
        if form.is_valid():
            switch_id = form.cleaned_data.get('switch')
            if switch_id and int(switch_id) != 0:
                query_var['switch_id'] = int(switch_id)

    #start_date = datetime(now.year, now.month, now.day, 0, 0, 0, 0)
    #end_date = datetime(now.year, now.month, now.day, 23, 59, 59, 999999)
    end_date = datetime(now.year, now.month, now.day,
                        now.hour, now.minute, now.second, now.microsecond)
    start_date = end_date+relativedelta(days=-int(1))

    query_var['start_uepoch'] = {'$gte': start_date, '$lt': end_date}

    if not request.user.is_superuser: # not superuser
        acc_code_error = ''
        if chk_account_code(request):
            query_var['accountcode'] = chk_account_code(request)
        else:
            return HttpResponseRedirect('/?acc_code_error=true')

    logging.debug('Map-reduce cdr dashboard analytic')
    #Retrieve Map Reduce
    (map, reduce, finalize_fun, out) = mapreduce_cdr_minute_report()

    #Run Map Reduce
    calls = cdr_data.map_reduce(map, reduce, out, query=query_var)
    calls = calls.find().sort([('_id.a_Year', 1),
                               ('_id.b_Month', 1),
                               ('_id.c_Day', 1),
                               ('_id.d_Hour', 1),
                               ('_id.e_Min', 1)])

    total_calls = 0
    total_duration = 0
    total_record_final = []

    for d in calls:
        graph_day = str(int(d['_id']['a_Year'])) + "-" + str(int(d['_id']['b_Month'])) + "-" + str(int(d['_id']['c_Day'])) + " "
        day = graph_day + str(int(d['_id']['d_Hour'])) + ":" + str(int(d['_id']['e_Min']))
        day = datetime.strptime(str(day), "%Y-%m-%d %H:%M")
        dt = (1000*time.mktime(day.timetuple())) #  - time.timezone

        total_record_final.append([dt, #str(dtime),
                                   d['value']['calldate__count'],
                                   d['value']['duration__sum']])
        total_calls += int(d['value']['calldate__count'])
        total_duration += int(d['value']['duration__sum'])
        
        # created cdr_hangup_analytic
        settings.DB_CONNECTION[settings.CDR_MONGO_CDR_HANGUP].update({'hangup_cause_id': int(d['value']['hangup_cause_id'])},
                                                                     {'$inc': {'count': 1}}, upsert=True)

    hangup_analytic_array = []
    hangup_analytic = settings.DB_CONNECTION[settings.CDR_MONGO_CDR_HANGUP].find({})
    for i in hangup_analytic:
        hangup_analytic_array.append((get_hangupcause_name(int(i['hangup_cause_id'])), i['count']))

    # remove mapreduce output & hangup analytic from database (no longer required)
    settings.DB_CONNECTION[settings.CDR_MONGO_CDR_HANGUP].drop()
    settings.DB_CONNECTION[out].drop()

    # Country call analytic start
    (map, reduce, finalize_fun, out) = mapreduce_cdr_country_report()
    country_calls = cdr_data.map_reduce(map, reduce, out, query=query_var)

    country_calls = country_calls.find().sort([('_id.d_Hour', 1),
                                               ('_id.e_Min', 1), ('_id.f_Con', 1)])

    for d in country_calls:
        # created cdr_country_analytic
        settings.DB_CONNECTION[settings.CDR_MONGO_CDR_COUNTRY].update({
                                                                      'country_id': int(d['_id']['f_Con']),
                                                                      },
                                                                      {
                                                                        '$inc': {'count': int(d['value']['calldate__count']),
                                                                                 'duration': int(d['value']['duration__sum'])}
                                                                      }, upsert=True)

    country_calls_final = settings.DB_CONNECTION[settings.CDR_MONGO_CDR_COUNTRY].find()
    country_analytic_array = []
    country_analytic_array_final = []
    for i in country_calls_final:
        # All countries list
        country_analytic_array.append((get_country_name(int(i['country_id'])),
                                       int(i['count']),
                                       int(i['duration']),
                                       int(i['country_id'])))

    country_analytic_array = sorted(country_analytic_array, key=lambda record: record[1], reverse=True)

    # remove mapreduce output & country analytic from database (no longer required)
    settings.DB_CONNECTION[settings.CDR_MONGO_CDR_COUNTRY].drop()
    settings.DB_CONNECTION[out].drop()
    # Country call analytic end

    #Calculate the Average Time of Call
    ACT = math.floor(total_calls / 24)
    if total_calls==0:
        ACD = 0
    else:
        ACD = int_convert_to_minute(math.floor(total_duration / total_calls))

    logging.debug('CDR dashboard view end')
    variables = {'module': current_view(request),
                 'total_calls': total_calls,
                 'total_duration': int_convert_to_minute(total_duration),
                 'ACT': ACT,
                 'ACD': ACD,
                 'total_record': sorted(total_record_final, key=lambda record: record[0]),
                 'hangup_analytic': hangup_analytic_array,
                 'country_analytic_array_final': country_analytic_array[0:5],# Top 5 countries list
                 'form': form,
                 'search_tag': search_tag,
                }

    return render_to_response('cdr/cdr_dashboard.html', variables,
           context_instance=RequestContext(request))


@login_required
def cdr_country_report(request):
    """CDR country report

    **Attributes**:

        * ``template`` - cdr/cdr_country_report.html
        * ``form`` - CountryReportForm
        * ``mongodb_data_set`` - CDR_MONGO_CDR_COUNTRY_REPORT / CDR_MONGO_CDR_COUNTRY
        * ``map_reduce`` - mapreduce_cdr_country_report()

    **Logic Description**:

        get all call records from mongodb collection for all countries
        to create country call
    """
    if not check_cdr_data_exists(request):
        return render_to_response('cdr/error_import.html', context_instance=RequestContext(request))

    logging.debug('CDR country report view start')
    template_name = 'cdr/cdr_country_report.html'
    form = CountryReportForm()

    switch_id = 0
    query_var = {}
    search_tag = 0
    now = datetime.now()
    start_date = datetime(now.year, now.month, now.day, 0, 0, 0, 0)
    end_date = datetime(now.year, now.month, now.day, 23, 59, 59, 999999)
    from_date = start_date.strftime("%Y-%m-%d")
    to_date = end_date.strftime("%Y-%m-%d")
    form = CountryReportForm(initial={'from_date': from_date, 'to_date': to_date})

    total_calls = 0
    total_duration = 0
    total_record_final = []

    if request.method == 'POST':
        logging.debug('CDR country report view with search option')
        search_tag = 1
        form = CountryReportForm(request.POST)
        if form.is_valid():
            if "from_date" in request.POST:
                # From
                from_date = form.cleaned_data.get('from_date')
                start_date = datetime(int(from_date[0:4]),
                                      int(from_date[5:7]),
                                      int(from_date[8:10]), 0, 0, 0, 0)

            if "to_date" in request.POST:
                # To
                to_date = form.cleaned_data.get('to_date')
                end_date = datetime(int(to_date[0:4]),
                                    int(to_date[5:7]),
                                    int(to_date[8:10]), 23, 59, 59, 999999)

            country_id = form.cleaned_data.get('country_id')
            # convert list value in int
            country_id = [int(row) for row in country_id]
            if len(country_id) >= 1 and country_id[0] != 0:
                query_var['country_id'] = {'$in': country_id}

            switch_id = form.cleaned_data.get('switch')
            if switch_id and int(switch_id) != 0:
                query_var['switch_id'] = int(switch_id)

            duration = form.cleaned_data.get('duration')
            duration_type = form.cleaned_data.get('duration_type')
            if duration:
                due = duration_field_chk_mongodb(duration, duration_type)
                if due:
                    query_var['duration'] = due
        else:
            country_analytic_array_final = country_analytic_array = []
            logging.debug('Error : CDR country report form')
            variables = {'module': current_view(request),
                         'total_calls': total_calls,
                         'total_duration': total_duration,
                         'total_record': total_record_final,
                         'country_analytic_array_final': country_analytic_array_final,
                         'top_ten_country_analytic' : country_analytic_array[0:11],
                         'form': form,
                         'search_tag': search_tag,
                         'DISPLAY_NO_OF_COUNTRY': DISPLAY_NO_OF_COUNTRY,
                         }

            return render_to_response(template_name, variables,
                   context_instance=RequestContext(request))

    query_var['start_uepoch'] = {'$gte': start_date, '$lt': end_date}

    if not request.user.is_superuser: # not superuser
        acc_code_error = ''
        if chk_account_code(request):
            query_var['accountcode'] = chk_account_code(request)
        else:
            return HttpResponseRedirect('/?acc_code_error=true')

    logging.debug('Map-reduce cdr dashboard analytic')
    #Retrieve Map Reduce
    (map, reduce, finalize_fun, out) = mapreduce_cdr_country_report()

    #Run Map Reduce
    country_data = settings.DB_CONNECTION[settings.CDR_MONGO_CDR_COUNTRY_REPORT]

    calls = country_data.map_reduce(map, reduce, out, query=query_var)
    calls = calls.find().sort([('_id.a_Year', 1),
                               ('_id.b_Month', 1),
                               ('_id.c_Day', 1),
                               ('_id.d_Hour', 1),
                               ('_id.e_Min', 1)])

    for d in calls:
        graph_day = str(int(d['_id']['a_Year'])) + "-" + str(int(d['_id']['b_Month'])) + "-" + str(int(d['_id']['c_Day'])) + " "
        day = graph_day + str(int(d['_id']['d_Hour'])) + ":" + str(int(d['_id']['e_Min']))

        day = datetime.strptime(str(day), "%Y-%m-%d %H:%M")
        dt = int(1000*time.mktime(day.timetuple())) #- time.timezone
        total_record_final.append({'dt': dt,
                                   'calldate__count': int(d['value']['calldate__count']),
                                   'duration__sum': int(d['value']['duration__sum']),
                                   'country_id': int(d['_id']['f_Con'])})

        total_calls += int(d['value']['calldate__count'])
        total_duration += int(d['value']['duration__sum'])

        # created cdr_country_analytic
        settings.DB_CONNECTION[settings.CDR_MONGO_CDR_COUNTRY].update({
                                                                        'country_id': int(d['_id']['f_Con']),
                                                                      },
                                                                      {
                                                                        '$inc': {'count': int(d['value']['calldate__count']),
                                                                                 'duration': int(d['value']['duration__sum'])}
                                                                      }, upsert=True)

    country_calls_final = settings.DB_CONNECTION[settings.CDR_MONGO_CDR_COUNTRY].find()
    country_analytic_array = []
    country_analytic_array_final = []
    for i in country_calls_final:
        # All countries list
        country_analytic_array.append((get_country_name(int(i['country_id'])),
                                       int(i['count']),
                                       int(i['duration']),
                                       int(i['country_id'])))

    # sort array based on call count in desc order
    country_analytic_array = sorted(country_analytic_array, key=lambda record: record[1], reverse=True)

    # Top countries list
    for i in country_analytic_array[0: DISPLAY_NO_OF_COUNTRY ]:
        #i[0] - country name, i[1] - call count, i[2] - call duration, i[3] - country id,
        country_analytic_array_final.append((i[0], int(i[1]), int(i[2]), int(i[3])))

    # Other countries analytic
    other_country_call_count = 0
    other_country_call_duration = 0
    for i in country_analytic_array[DISPLAY_NO_OF_COUNTRY:]:
        #i[0] - country name, i[1] - call count, i[2] - call duration
        other_country_call_count += int(i[1])
        other_country_call_duration += int(i[2])

    country_analytic_array_final.append((_('Other'),
                                         other_country_call_count,
                                         other_country_call_duration))

    # remove mapreduce output & country analytic from database (no longer required)
    settings.DB_CONNECTION[out].drop()
    settings.DB_CONNECTION[settings.CDR_MONGO_CDR_COUNTRY].drop()

    logging.debug('CDR country report view end')
    variables = {'module': current_view(request),
                 'total_calls': total_calls,
                 'total_duration': total_duration,
                 'total_record': total_record_final,
                 'country_analytic_array_final': country_analytic_array_final,
                 'top_ten_country_analytic' : country_analytic_array[0:DISPLAY_NO_OF_COUNTRY],
                 'form': form,
                 'search_tag': search_tag,
                 'DISPLAY_NO_OF_COUNTRY': DISPLAY_NO_OF_COUNTRY,
                }

    return render_to_response(template_name, variables,
           context_instance=RequestContext(request))


@login_required
def cdr_overview(request):
    """CDR graph by hourly/daily/monthly basis

    **Attributes**:

        * ``template`` - cdr/cdr_overview.html.html
        * ``form`` - CdrOverviewForm
        * ``mongodb_data_set`` - CDR_MONGO_CDR_DAILY, CDR_MONGO_CDR_HOURLY
        * ``map_reduce`` - mapreduce_cdr_hourly_overview() | mapreduce_cdr_monthly_overview()
                           mapreduce_cdr_daily_overview

    **Logic Description**:

        get all call records from mongodb collection for
        all monthly, daily, hourly analytics
    """

    if not check_cdr_data_exists(request):
        return render_to_response('cdr/error_import.html', context_instance=RequestContext(request))
    template_name = 'cdr/cdr_overview.html'
    logging.debug('CDR overview start')
    query_var = {}
    tday = datetime.today()
    search_tag = 0
    if request.method == 'POST':
        logging.debug('CDR overview with search option')
        search_tag = 1
        form = CdrOverviewForm(request.POST)
        if form.is_valid():
            if "from_date" in request.POST:
                from_date = datetime(int(request.POST['from_date'][0:4]),
                    int(request.POST['from_date'][5:7]),
                    int(request.POST['from_date'][8:10]), 0, 0, 0, 0)
            else:
                from_date = tday

            if "to_date" in request.POST:
                to_date = datetime(int(request.POST['to_date'][0:4]),
                    int(request.POST['to_date'][5:7]),
                    int(request.POST['to_date'][8:10]), 23, 59, 59, 999999)
            else:
                to_date = tday

            destination = form.cleaned_data.get('destination')
            destination_type = form.cleaned_data.get('destination_type')
            dst = source_desti_field_chk_mongodb(destination, destination_type)
            if dst:
                query_var['destination_number'] = dst

            switch_id = form.cleaned_data.get('switch')
            if switch_id and int(switch_id) != 0:
                query_var['switch_id'] = int(switch_id)

            if from_date != '' and to_date != '':
                start_date = datetime(from_date.year, from_date.month, from_date.day, 0, 0, 0, 0)
                end_date = datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59, 999999)
                query_var['start_uepoch'] = {'$gte': start_date, '$lt': end_date}

                month_start_date = datetime(start_date.year, start_date.month, 1, 0, 0, 0, 0)
                month_end_date = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, 999999)

        else:
            # form is not valid
            logging.debug('Error : CDR overview search form')
            total_hour_record = []
            total_hour_call_count = []
            total_hour_call_duration = []
            total_day_record = []
            total_day_call_duration = []
            total_day_call_count = []
            total_month_record = []
            total_month_call_duration = []
            total_month_call_count = []

            tday = datetime.today()
            start_date = datetime(tday.year, tday.month, tday.day, 0, 0, 0, 0)
            end_date = datetime(tday.year, tday.month, tday.day, 23, 59, 59, 999999)

            variables = {'module': current_view(request),
                         'form': form,
                         'search_tag': search_tag,
                         'total_hour_record': total_hour_record,
                         'total_hour_call_count': total_hour_call_count,
                         'total_hour_call_duration': total_hour_call_duration,
                         'total_day_record': total_day_record,
                         'total_day_call_count': total_day_call_count,
                         'total_day_call_duration': total_day_call_duration,
                         'total_month_record': total_month_record,
                         'total_month_call_duration': total_month_call_duration,
                         'total_month_call_count': total_month_call_count,
                         'start_date': start_date,
                         'end_date': end_date,
                         'TOTAL_GRAPH_COLOR': TOTAL_GRAPH_COLOR,
                         }

            return render_to_response(template_name, variables,
                                      context_instance = RequestContext(request))

    if len(query_var) == 0:
        tday = datetime.today()
        switch_id = 0
        form = CdrOverviewForm(initial={'from_date': tday.strftime('%Y-%m-%d'),
                                        'to_date': tday.strftime('%Y-%m-%d'),
                                        'destination_type': 1,
                                        'switch': switch_id,})

        start_date = datetime(tday.year, tday.month, tday.day, 0, 0, 0, 0)
        end_date = datetime(tday.year, tday.month, tday.day, 23, 59, 59, 999999)
        month_start_date = datetime(start_date.year, start_date.month, 1, 0, 0, 0, 0)
        month_end_date = datetime(end_date.year, end_date.month, end_date.day,  23, 59, 59, 999999)

        query_var['start_uepoch'] = {'$gte': start_date, '$lt': end_date}

    if not request.user.is_superuser: # not superuser
        acc_code_error = ''
        if chk_account_code(request):
            query_var['accountcode'] = chk_account_code(request)
        else:
            return HttpResponseRedirect('/?acc_code_error=true')

    if query_var:
        logging.debug('Map-reduce cdr overview analytic')
        # Collect Hourly data
        hourly_data = settings.DB_CONNECTION[settings.CDR_MONGO_CDR_HOURLY]

        (map, reduce, finalize_fun, out) = mapreduce_cdr_hourly_overview()
        calls_in_day = hourly_data.map_reduce(map, reduce, out, query=query_var)
        calls_in_day = calls_in_day.find().sort([('_id.a_Year', -1), ('_id.b_Month', -1), ('_id.c_Day', -1),
                                                 ('_id.d_Hour', -1), ('_id.f_Switch', 1)])

        total_hour_record = []
        total_hour_call_count = []
        total_hour_call_duration = []
        if calls_in_day.count()!=0:
            hour_data_call_count = dict()
            hour_data_call_duration = dict()
            for i in calls_in_day.clone():
                graph_day = str(int(i['_id']['a_Year'])) + "-" + str(int(i['_id']['b_Month'])) + "-" + str(int(i['_id']['c_Day'])) + " "
                day = graph_day + str(int(i['_id']['d_Hour']))
                day = datetime.strptime(str(day), "%Y-%m-%d %H")
                dt = int(1000*time.mktime(day.timetuple())) #- time.timezone
                total_hour_record.append({'dt': dt,
                                          'calldate__count': int(i['value']['calldate__count']),
                                          'duration__sum': int(i['value']['duration__sum']),
                                          'switch_id': int(i['_id']['f_Switch'])})

                if dt in hour_data_call_count:
                    hour_data_call_count[dt] += int(i['value']['calldate__count'])
                else:
                    hour_data_call_count[dt] = int(i['value']['calldate__count'])

                if dt in hour_data_call_duration:
                    hour_data_call_duration[dt] += int(i['value']['duration__sum'])
                else:
                    hour_data_call_duration[dt] = int(i['value']['duration__sum'])

            total_hour_call_count = hour_data_call_count.items()
            total_hour_call_count = sorted(total_hour_call_count, key=lambda k: k[0])

            total_hour_call_duration = hour_data_call_duration.items()
            total_hour_call_duration = sorted(total_hour_call_duration, key=lambda k: k[0])

        # remove mapreduce output from database (no longer required)
        settings.DB_CONNECTION[out].drop()

        # Collect daily data
        daily_data = settings.DB_CONNECTION[settings.CDR_MONGO_CDR_DAILY]

        (map, reduce, finalize_fun, out) = mapreduce_cdr_daily_overview()
        calls_in_day = daily_data.map_reduce(map, reduce, out, query=query_var)
        calls_in_day = calls_in_day.find().sort([('_id.a_Year', -1), ('_id.b_Month', -1),
                                                 ('_id.c_Day', -1), ('_id.f_Switch', 1)])
        total_day_record = []
        total_day_call_duration = []
        total_day_call_count = []
        if calls_in_day.count()!=0:
            day_call_duration = dict()
            day_call_count = dict()
            for i in calls_in_day.clone():
                day = str(int(i['_id']['a_Year'])) + "-" + str(int(i['_id']['b_Month'])) + "-" + str(int(i['_id']['c_Day']))
                day = datetime.strptime(str(day), "%Y-%m-%d")
                dt = int(1000*time.mktime(day.timetuple()))
                total_day_record.append({'dt': dt,
                                         'calldate__count': int(i['value']['calldate__count']),
                                         'duration__sum': int(i['value']['duration__sum']),
                                         'switch_id': int(i['_id']['f_Switch'])})

                if dt in day_call_duration:
                    day_call_duration[dt] += int(i['value']['duration__sum'])
                else:
                    day_call_duration[dt] = int(i['value']['duration__sum'])

                if dt in day_call_count:
                    day_call_count[dt] += int(i['value']['calldate__count'])
                else:
                    day_call_count[dt] = int(i['value']['calldate__count'])

            total_day_call_duration = day_call_duration.items()
            total_day_call_duration = sorted(total_day_call_duration, key=lambda k: k[0])
            total_day_call_count = day_call_count.items()
            total_day_call_count = sorted(total_day_call_count, key=lambda k: k[0])

        # remove mapreduce output from database (no longer required)
        settings.DB_CONNECTION[out].drop()

        # Collect monthly data
        monthly_data = settings.DB_CONNECTION[settings.CDR_MONGO_CDR_MONTHLY]

        (map, reduce, finalize_fun, out) = mapreduce_cdr_monthly_overview()
        query_var['start_uepoch'] = {'$gte': month_start_date, '$lt': month_end_date}

        #Run Map Reduce
        calls_in_month = monthly_data.map_reduce(map, reduce, out, query=query_var)
        calls_in_month = calls_in_month.find().sort([('_id.a_Year', -1),
                                                     ('_id.b_Month', -1),
                                                     ('_id.f_Switch', 1)])

        total_month_record = []
        total_month_call_duration = []
        total_month_call_count = []
        if calls_in_month.count()!=0:
            month_call_duration = dict()
            month_call_count = dict()
            for i in calls_in_month.clone():
                graph_day = str(int(i['_id']['a_Year'])) + "-" + str(int(i['_id']['b_Month']))
                day = datetime.strptime(str(graph_day), "%Y-%m")
                dt = int(1000*time.mktime(day.timetuple()))
                total_month_record.append({'dt': dt,
                                           'calldate__count': int(i['value']['calldate__count']),
                                           'duration__sum': int(i['value']['duration__sum']),
                                           'switch_id': int(i['_id']['f_Switch'])})

                if dt in month_call_duration:
                    month_call_duration[dt] += int(i['value']['duration__sum'])
                else:
                    month_call_duration[dt] = int(i['value']['duration__sum'])

                if dt in month_call_count:
                    month_call_count[dt] += int(i['value']['calldate__count'])
                else:
                    month_call_count[dt] = int(i['value']['calldate__count'])

            total_month_call_duration = month_call_duration.items()
            total_month_call_duration = sorted(total_month_call_duration, key=lambda k: k[0])
            total_month_call_count = month_call_count.items()
            total_month_call_count = sorted(total_month_call_count, key=lambda k: k[0])

        # remove mapreduce output from database (no longer required)
        settings.DB_CONNECTION[out].drop()

        logging.debug('CDR daily view end')
        variables = {'module': current_view(request),
                     'form': form,
                     'search_tag': search_tag,
                     'total_hour_record': total_hour_record,
                     'total_hour_call_count': total_hour_call_count,
                     'total_hour_call_duration': total_hour_call_duration,
                     'total_day_record': total_day_record,
                     'total_day_call_count': total_day_call_count,
                     'total_day_call_duration': total_day_call_duration,
                     'total_month_record': total_month_record,
                     'total_month_call_duration': total_month_call_duration,
                     'total_month_call_count': total_month_call_count,
                     'start_date': start_date,
                     'end_date': end_date,
                     'TOTAL_GRAPH_COLOR': TOTAL_GRAPH_COLOR,
                     }

        return render_to_response(template_name, variables,
                                  context_instance = RequestContext(request))


def get_hourly_data_for_date(start_date, end_date, query_var, graph_view):
    hourly_data = settings.DB_CONNECTION[settings.CDR_MONGO_CDR_HOURLY]
    logging.debug('Map-reduce cdr hourly analytic')
    #Retrieve Map Reduce
    (map, reduce, finalize_fun, out) = mapreduce_cdr_hour_report()

    #Run Map Reduce
    calls_in_day = hourly_data.map_reduce(map, reduce, out, query=query_var)
    calls_in_day = calls_in_day.find().sort([('_id.a_Year', -1), ('_id.b_Month', -1), ('_id.c_Day', -1),
        ('_id.d_Hour', -1), ('_id.e_Min', -1)])

    record_dates = []
    total_record = []
    total_call_count = []

    #get the dates of the period
    #return [datetime.datetime(2012, 3, 20, 0, 0), datetime.datetime(2012, 3, 21, 0, 0)]
    dateList = date_range(datetime(start_date.year, start_date.month,start_date.day),
        datetime(end_date.year, end_date.month, end_date.day))

    for i in calls_in_day:
        date_in_list = datetime(int(i['_id']['a_Year']), int(i['_id']['b_Month']), int(i['_id']['c_Day']))
        if date_in_list in dateList:
            called_time = datetime.strptime(str(i['value']['calldate']), "%Y-%m-%d %H:%M:%S")
            record_dates.append(( str(date_in_list)[0:10] ))
            if graph_view == '1':
                total_record.append(( called_time, i['value']['calldate__count']))
                total_call_count.append((int(i['value']['calldate__count'])))
            else:
                total_record.append(( called_time, i['value']['duration__sum']))
                total_call_count.append((int(i['value']['duration__sum'])))

    record_dates = list(set(record_dates))

    if calls_in_day.count() != 0:
        total_record_final = []

        for rd in record_dates:
            list_of_hour = []
            list_of_count= []
            l_o_c = {}
            for i in calls_in_day.clone():
                string_date = datetime(int(i['_id']['a_Year']), int(i['_id']['b_Month']), int(i['_id']['c_Day']))
                string_date = str(string_date)[0:10]
                if string_date == rd:
                    list_of_hour.append(int((i['_id']['d_Hour'])))
                    if graph_view == '1':
                        list_of_count.append((int(i['_id']['d_Hour']), i['value']['calldate__count']))
                        l_o_c[int(i['_id']['d_Hour'])] = i['value']['calldate__count']
                    else:
                        list_of_count.append((int(i['_id']['d_Hour']), i['value']['duration__sum']))
                        l_o_c[int(i['_id']['d_Hour'])] = i['value']['duration__sum']

            x = 0
            for j in range(0, 24):
                if j not in list_of_hour:
                    total_record_final.append((rd, j, 0))
                else:
                    total_record_final.append((rd, j, l_o_c[j]))
                    x = x + 1

        for d in dateList:
            sd = d.strftime('%Y-%m-%d')
            if sd not in record_dates:
                for j in range(0, 24):
                    total_record_final.append((sd, j, 0))
    else:
        total_record_final=[]

    total_record = {}
    for i in total_record_final:
        if (i[0] in total_record.keys()) and (i[1] not in total_record[i[0]].keys()):
            total_record[i[0]][i[1]] = i[2]
        elif i[0] not in total_record.keys():
            total_record[i[0]] = {}
            total_record[i[0]][i[1]] = i[2]

    # remove mapreduce output from database (no longer required)
    settings.DB_CONNECTION[out].drop()
    variables = {
        'total_record': total_record,
        }
    return variables


@login_required
def cdr_graph_by_hour(request):
    """CDR graph by hourly basis

    **Attributes**:

        * ``template`` - cdr/cdr_graph_by_hour.html
        * ``form`` - CompareCallSearchForm
        * ``mongodb_data_set`` - CDR_MONGO_CDR_HOURLY
        * ``map_reduce`` - mapreduce_cdr_hour_report()

    **Logic Description**:

        get all call records from mongodb collection for
        hourly analytics for given date
    """

    if not check_cdr_data_exists(request):
        return render_to_response('cdr/error_import.html', context_instance=RequestContext(request))

    logging.debug('CDR hourly view start')
    template_name = 'cdr/cdr_graph_by_hour.html'
    query_var = {}
    total_record = []
    #default
    comp_days = 2
    graph_view = '1'
    check_days = 1
    search_tag = 0
    tday = datetime.today()
    from_date = tday.strftime('%Y-%m-%d')
    form = CompareCallSearchForm(initial={'from_date': from_date,
                                          'comp_days': comp_days,
                                          'check_days': check_days,
                                          'destination_type': 1,
                                          'switch': 0,
                                          'graph_view': graph_view})
    if request.method == 'POST':
        logging.debug('CDR hourly view with search option')
        search_tag = 1
        form = CompareCallSearchForm(request.POST)
        if form.is_valid():
            if "from_date" in request.POST:
                from_date = request.POST['from_date']
                select_date = datetime(int(from_date[0:4]),
                    int(from_date[5:7]),
                    int(from_date[8:10]), 0, 0, 0, 0)
            else:
                from_date = tday.strftime('%Y-%m-%d')
                select_date = tday

            comp_days = int(variable_value(request, 'comp_days'))
            destination = variable_value(request, 'destination')
            destination_type = variable_value(request, 'destination_type')
            graph_view = int(variable_value(request, 'graph_view'))
            check_days = int(variable_value(request, 'check_days'))
            # check previous days
            if check_days == 2:
                compare_date_list = []
                compare_date_list.append(select_date)

                for i in range(1, int(comp_days)+1):
                    #select_date+relativedelta(weeks=-i)
                    interval_date = select_date+relativedelta(weeks=-i)
                    compare_date_list.append(interval_date)

            dst = source_desti_field_chk_mongodb(destination, destination_type)
            if dst:
                query_var['destination_number'] = dst

            switch_id = form.cleaned_data.get('switch')
            if switch_id and int(switch_id) != 0:
                query_var['switch_id'] = int(switch_id)

            if from_date != '':
                end_date = from_date = select_date
                start_date= end_date+relativedelta(days=-int(comp_days))
                start_date = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0, 0)
                end_date = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, 999999)
                if check_days==1:
                    query_var['start_uepoch'] = {'$gte': start_date, '$lt': end_date}
        else:
            # form is not valid
            logging.debug('Error : CDR hourly search form')
            total_record = []
            variables = {'module': current_view(request),
                         'form': form,
                         'result': 'min',
                         'graph_view': graph_view,
                         'search_tag': search_tag,
                         'from_date': from_date,
                         'comp_days': comp_days,
                         'total_record': total_record,
                         }

            return render_to_response(template_name, variables,
                   context_instance = RequestContext(request))

    if len(query_var) == 0:
        from_date = datetime.today()
        from_day = validate_days(from_date.year, from_date.month, from_date.day)
        from_year=from_date.year
        from_month= from_date.month
        end_date = datetime(from_year, from_month, from_day)
        start_date= end_date+relativedelta(days=-comp_days)
        start_date = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0, 0)
        end_date = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, 999999)
        query_var['start_uepoch'] = {'$gte': start_date, '$lt': end_date}

    if not request.user.is_superuser: # not superuser
        acc_code_error = ''
        if chk_account_code(request):
            query_var['accountcode'] = chk_account_code(request)
        else:
            return HttpResponseRedirect('/?acc_code_error=true')

    if query_var:
        if check_days == 2:
            for i in compare_date_list:
                s_date = datetime(i.year, i.month, i.day, 0, 0, 0, 0)
                e_date = datetime(i.year, i.month, i.day, 23, 59, 59, 999999)
                query_var['start_uepoch'] = {'$gte': s_date, '$lt': e_date}
                result_data = get_hourly_data_for_date(s_date, e_date, query_var, graph_view)
                total_record.append((result_data['total_record']))

        if check_days == 1:
            result_data = get_hourly_data_for_date(start_date, end_date, query_var, graph_view)
            total_record.append((result_data['total_record']))

        logging.debug('CDR hourly view end')
        variables = {'module': current_view(request),
                     'form': form,
                     'result': 'min',
                     'graph_view': graph_view,
                     'search_tag': search_tag,
                     'from_date': from_date,
                     'comp_days': comp_days,
                     'total_record': total_record,
                     }

        return render_to_response(template_name, variables,
               context_instance = RequestContext(request))


@login_required
def cdr_concurrent_calls(request):
    """CDR view of concurrent calls

    **Attributes**:

        * ``template`` - cdr/cdr_graph_concurrent_calls.html
        * ``form`` - ConcurrentCallForm
        * ``mongodb_data_set`` - CDR_MONGO_CONC_CALL_AGG (map-reduce collection)

    **Logic Description**:

        get all concurrent call records from mongodb map-reduce collection for
        current date
    """

    if not check_cdr_data_exists(request):
        return render_to_response('cdr/error_import.html', context_instance=RequestContext(request))

    logging.debug('CDR concurrent view start')
    query_var = {}
    switch_id = 0
    if request.method == 'POST':
        logging.debug('CDR concurrent view with search option')
        form = ConcurrentCallForm(request.POST)
        if form.is_valid():
            if "from_date" in request.POST and request.POST['from_date'] != '':
                from_date = request.POST['from_date']
                start_date = datetime(int(from_date[0:4]),
                                      int(from_date[5:7]),
                                      int(from_date[8:10]), 0, 0, 0, 0)
                end_date = datetime(int(from_date[0:4]),
                                    int(from_date[5:7]),
                                    int(from_date[8:10]), 23, 59, 59, 0)

            switch_id = form.cleaned_data.get('switch')
            if switch_id and int(switch_id) != 0:
                query_var['value.switch_id'] = int(switch_id)
    else:
        now = datetime.today()
        from_date = to_date = now.strftime('%Y-%m-%d')
        start_date = datetime(now.year, now.month, now.day, 0, 0, 0, 0)
        end_date = datetime(now.year, now.month, now.day, 23, 59, 59, 0)
        form = ConcurrentCallForm(initial={'from_date': from_date})

    query_var['value.call_date'] = {'$gte': start_date, '$lt': end_date}

    if not request.user.is_superuser: # not superuser
        acc_code_error = ''
        if chk_account_code(request):
            query_var['value.accountcode'] = chk_account_code(request)
        else:
            return HttpResponseRedirect('/?acc_code_error=true')

    if query_var:
        calls_in_day = settings.DB_CONNECTION[settings.CDR_MONGO_CONC_CALL_AGG]
        final_data = []

        calls_in_day = calls_in_day.find(query_var).sort([('_id.a_Year', -1), ('_id.b_Month', -1),
                                                          ('_id.c_Day', -1), ('_id.d_Hour', -1),
                                                          ('_id.e_Min', -1)])
        #new total data
        for d in calls_in_day.clone():
            c_date = datetime(int(d['_id']['a_Year']), int(d['_id']['b_Month']),
                              int(d['_id']['c_Day']), int(d['_id']['d_Hour']), int(d['_id']['e_Min']), 0, 0)

            dt = int(1000*time.mktime(c_date.timetuple())- time.timezone)
            final_data.append((dt, int(d['value']['numbercall__max'])))
            ms = time.mktime(c_date.timetuple())
            
        logging.debug('CDR concurrent view end')
        variables = {'module': current_view(request),
                     'form': form,
                     'final_data': final_data,
                     'start_date': start_date
                    }

    return render_to_response('cdr/cdr_graph_concurrent_calls.html', variables,
           context_instance = RequestContext(request))



@login_required
def cdr_realtime(request):
    """Call realtime view

    **Attributes**:

        * ``template`` - cdr/cdr_realtime.html
        * ``form`` - SwitchForm
        * ``mongodb_collection`` - CDR_MONGO_CONC_CALL_AGG (map-reduce collection)

    **Logic Description**:

        get all call records from mongodb collection for
        concurrent analytics
    """
    logging.debug('CDR realtime view start')
    query_var = {}
    switch_id = 0
    search_tag = 0
    if request.method == 'POST':
        logging.debug('CDR realtime view with search option')
        search_tag = 1
        form = SwitchForm(request.POST)
        if form.is_valid():
            switch_id = form.cleaned_data.get('switch')
            if switch_id and int(switch_id) != 0:
                query_var['value.switch_id'] = int(switch_id)
    else:
        form = SwitchForm()
    now = datetime.now()
    start_date = datetime(now.year, now.month, now.day, 0, 0, 0, 0)
    end_date = datetime(now.year, now.month, now.day, 23, 59, 59, 999999)

    query_var['value.call_date'] = {'$gte': start_date, '$lt': end_date}

    if not request.user.is_superuser: # not superuser
        acc_code_error = ''
        if chk_account_code(request):
            query_var['value.accountcode'] = chk_account_code(request)
        else:
            return HttpResponseRedirect('/?acc_code_error=true')

    if query_var:
        calls_in_day = settings.DB_CONNECTION[settings.CDR_MONGO_CONC_CALL_AGG]
        final_data = []

        calls_in_day = calls_in_day.find(query_var).sort([('_id.a_Year', -1), ('_id.b_Month', -1),
                                                          ('_id.c_Day', -1), ('_id.d_Hour', -1),
                                                          ('_id.e_Min', -1)])
        #new total data
        for d in calls_in_day.clone():
            c_date = datetime(int(d['_id']['a_Year']), int(d['_id']['b_Month']),
                              int(d['_id']['c_Day']), int(d['_id']['d_Hour']), int(d['_id']['e_Min']), 0, 0)

            dt = int(1000*time.mktime(c_date.timetuple())- time.timezone)
            final_data.append((dt, int(d['value']['numbercall__max'])))
            ms = time.mktime(c_date.timetuple())
            
        logging.debug('Realtime view end')
        list_switch = Switch.objects.all()
        user_obj = User.objects.get(username=request.user)
        variables = {'module': current_view(request),
                     'form': form,
                     'final_data': final_data,
                     'list_switch': list_switch,
                     'user_id': request.user.id,
                     'colorgraph1': '180, 0, 0',
                     'colorgraph2': '0, 180, 0',
                     'colorgraph3': '0, 0, 180',
                     'realtime_graph_maxcall': 300,
                     'socketio_host': settings.SOCKETIO_HOST,
                     'socketio_port': settings.SOCKETIO_PORT,
                    }

    return render_to_response('cdr/cdr_graph_realtime.html', variables,
           context_instance = RequestContext(request))


def get_cdr_mail_report():
    """General function to get previous day CDR report"""
    # Get yesterday's CDR-Stats Mail Report
    switch_id = 0

    query_var = {}
    yesterday = date.today() - timedelta(1)
    start_date = datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0, 0)
    end_date = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59, 999999)

    query_var['start_uepoch'] = {'$gte': start_date, '$lt': end_date}
    # result set
    final_result = cdr_data.find(query_var)

    total_records = [[] for x in range(1, int(final_result.count()))]

    last_ten_calls = final_result.limit(10).sort([('start_uepoch', -1)]).clone()
    final_last_ten_calls = []
    for i in last_ten_calls:
        # duration convert into min
        duration = int_convert_to_minute(int(i['duration']))
        billsec = int_convert_to_minute(int(i['billsec']))
        
        final_last_ten_calls.append({
                             'id': i['cdr_object_id'],
                             'start_uepoch': i['start_uepoch'],
                             'caller_id_number': i['caller_id_number'],
                             'caller_id_name': i['caller_id_name'],
                             'destination_number': i['destination_number'],
                             'duration': duration,
                             'billsec': billsec,
                             'hangup_cause': get_hangupcause_name(i['hangup_cause_id']),
                             'accountcode': i['accountcode'],
                             'country': i['country_id'],
                             'direction': i['direction'],
                            })

    #Retrieve Map Reduce
    (map, reduce, finalize_fun, out) = mapreduce_cdr_mail_report()

    total_data = cdr_data.map_reduce(map, reduce, out, query=query_var, finalize=finalize_fun,)

    total_data = total_data.find().sort([('_id.c_Day', -1), ('_id.d_Hour', -1)])
    total_hour_count = total_data.count()
    detail_data = []
    for doc in total_data:
        detail_data.append({
                            'duration__sum': int(doc['value']['duration__sum']),
                            'calldate__count': int(doc['value']['calldate__count']),
                            'duration__avg': doc['value']['duration__avg'],
                            })
        # created cdr_hangup_analytic
        settings.DB_CONNECTION[settings.CDR_MONGO_CDR_HANGUP].update({'hangup_cause_id': int(doc['value']['hangup_cause_id'])},
                                                                     {'$inc': {'count': 1}}, upsert=True)

        # created cdr_country_analytic
        settings.DB_CONNECTION[settings.CDR_MONGO_CDR_COUNTRY].update({
                                                                      'country_id': int(doc['_id']['f_Con']),
                                                                      },
                                                                      {
                                                                        '$inc': {'count': int(doc['value']['calldate__count']),
                                                                                 'duration': int(doc['value']['duration__sum'])}
                                                                      }, upsert=True)

    if total_data.count() != 0:
        total_duration = sum([int(x['value']['duration__sum']) for x in total_data.clone()])
        total_calls = sum([int(x['value']['calldate__count']) for x in total_data.clone()])
    else:
        total_duration = 0
        total_calls = 0

    #Calculate the Average Time of Call
    ACT = math.floor(total_calls / 24)
    if total_calls == 0:
        ACD = 0
    else:
        ACD = int_convert_to_minute(math.floor(total_duration / total_calls))

    # Top 5 called countries
    country_calls_final = settings.DB_CONNECTION[settings.CDR_MONGO_CDR_COUNTRY].find().sort([('count', -1)]).limit(5)
    country_analytic_array = []
    country_analytic_array_final = []
    for i in country_calls_final:
        # All countries list
        country_analytic_array.append((get_country_name(int(i['country_id'])),
                                       int(i['count']),
                                       int(i['duration']),
                                       int(i['country_id'])))

    settings.DB_CONNECTION[settings.CDR_MONGO_CDR_COUNTRY].drop()
    # Country call analytic end

    hangup_analytic_array = []
    hangup_analytic = settings.DB_CONNECTION[settings.CDR_MONGO_CDR_HANGUP].find({})
    if hangup_analytic.count() != 0:
        total_hangup = sum([int(x['count']) for x in hangup_analytic.clone()])
        for i in hangup_analytic.clone():
            hangup_analytic_array.append((get_hangupcause_name(int(i['hangup_cause_id'])),
                                          "{0:.0f}%".format((float(i['count']) / float(total_hangup)) * 100) ))

    settings.DB_CONNECTION[settings.CDR_MONGO_CDR_HANGUP].drop()
    # remove mapreduce output from database (no longer required)
    settings.DB_CONNECTION[out].drop()

    mail_data = {
                'yesterday_date': start_date,
                'rows': final_last_ten_calls,
                'total_duration': total_duration,
                'total_calls': total_calls,
                'ACT': ACT,
                'ACD': ACD,
                'country_analytic_array': country_analytic_array,
                'hangup_analytic_array': hangup_analytic_array,
                }
    return mail_data


@login_required
def mail_report(request):
    """Mail Report Template

    **Attributes**:

        * ``template`` - cdr/cdr_mail_report.html
        * ``form`` - MailreportForm
        * ``mongodb_data_set`` - CDR_MONGO_CDR_COMMON

    **Logic Description**:

        get top 10 calls from mongodb collection & hnagupcause/country analytic
        to generate mail report
    """

    if not check_cdr_data_exists(request):
        return render_to_response('cdr/error_import.html', context_instance=RequestContext(request))
    
    logging.debug('CDR mail report view start')
    template = 'cdr/cdr_mail_report.html'
    user_obj = User.objects.get(username=request.user)
    msg = ''
    try:
        user_profile_obj = UserProfile.objects.get(user=user_obj)
    except UserProfile.DoesNotExist:
        #create UserProfile
        user_profile_obj = UserProfile(user=user_obj)
        user_profile_obj.save()
        
    form = EmailReportForm(request.user, instance=user_profile_obj)
    if request.method == 'POST' :
        form = EmailReportForm(request.user, request.POST, instance=user_profile_obj)
        if form.is_valid():
            form.save()
            msg = _('Email ids are saved successfully.')

    mail_data = get_cdr_mail_report()
    logging.debug('CDR mail report view end')
    data = {'module': current_view(request),
            'yesterday_date': mail_data['yesterday_date'],
            'rows': mail_data['rows'],
            'form' : form,
            'total_duration': mail_data['total_duration'],
            'total_calls': mail_data['total_calls'],
            'ACT': mail_data['ACT'],
            'ACD': mail_data['ACD'],
            'country_analytic_array': mail_data['country_analytic_array'],
            'hangup_analytic_array': mail_data['hangup_analytic_array'],
            'msg': msg,
    }
    return render_to_response(template, data,
           context_instance = RequestContext(request))


def index(request):
    """Index Page of CDR-Stats

    **Attributes**:

        * ``template`` - cdr/index.html
        * ``form`` - loginForm
    """
    template = 'cdr/index.html'
    errorlogin = ''
    loginform = loginForm()
    db_error = ''

    if request.GET.get('db_error'):
        if request.GET['db_error'] == 'closed':
            errorlogin = _('Mongodb Database connection is closed!')
        if request.GET['db_error'] == 'locked':
            errorlogin = _('Mongodb Database is locked!')

    code_error = _('Account code is not assigned!')
    if request.GET.get('acc_code_error'):
        if request.GET['acc_code_error'] == 'true':
            errorlogin = code_error

    data = {'module': current_view(request),
            'loginform' : loginform,
            'errorlogin' : errorlogin,
            'news' : get_news(news_url),
    }
    return render_to_response(template, data,
           context_instance = RequestContext(request))


def pleaselog(request):
    template = 'cdr/index.html'
    loginform = loginForm()
    
    data = {
        'loginform' : loginform,
        'notlogged' : True,
        'news' : get_news(news_url),
    }
    return render_to_response(template, data,
           context_instance = RequestContext(request))


def cust_password_reset(request):
    """Use ``django.contrib.auth.views.password_reset`` view method for
    forgotten password on the Customer UI

    This method sends an e-mail to the user's email-id which is entered in
    ``password_reset_form``
    """
    if not request.user.is_authenticated():
        data = {'loginform': loginForm()}
        return password_reset(request,
        template_name='cdr/registration/password_reset_form.html',
        email_template_name='cdr/registration/password_reset_email.html',
        post_reset_redirect='/password_reset/done/',
        from_email='cdr_admin@localhost.com',
        extra_context=data)
    else:
        return HttpResponseRedirect("/")


def cust_password_reset_done(request):
    """Use ``django.contrib.auth.views.password_reset_done`` view method for
    forgotten password on the Customer UI

    This will show a message to the user who is seeking to reset their
    password.
    """
    if not request.user.is_authenticated():
        data = {'loginform': loginForm()}
        return password_reset_done(request,
        template_name='cdr/registration/password_reset_done.html',
        extra_context=data)
    else:
        return HttpResponseRedirect("/")


def cust_password_reset_confirm(request, uidb36=None, token=None):
    """Use ``django.contrib.auth.views.password_reset_confirm`` view method for
    forgotten password on the Customer UI

    This will allow a user to reset their password.
    """
    if not request.user.is_authenticated():
        data = {'loginform': loginForm()}
        return password_reset_confirm(request, uidb36=uidb36, token=token,
        template_name='cdr/registration/password_reset_confirm.html',
        post_reset_redirect='/reset/done/',
        extra_context=data)
    else:
        return HttpResponseRedirect("/")


def cust_password_reset_complete(request):
    """Use ``django.contrib.auth.views.password_reset_complete`` view method
    for forgotten password on theCustomer UI

    This shows an acknowledgement to the user after successfully resetting
    their password for the system.
    """
    if not request.user.is_authenticated():
        data = {'loginform': loginForm()}
        return password_reset_complete(request,
        template_name='cdr/registration/password_reset_complete.html',
        extra_context=data)
    else:
        return HttpResponseRedirect("/")
