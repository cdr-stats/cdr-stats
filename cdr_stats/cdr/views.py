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
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.utils.translation import gettext as _
from django.conf import settings
from pymongo.connection import Connection
from pymongo.errors import ConnectionFailure
from notification import models as notification
from common.common_functions import current_view, get_news, \
                                    variable_value,\
                                    mongodb_str_filter,\
                                    mongodb_int_filter, \
                                    int_convert_to_minute, \
                                    validate_days,\
                                    ceil_strdate
from cdr.models import Switch
from cdr.functions_def import get_country_name, \
                                chk_account_code, \
                                get_hangupcause_name
from cdr.forms import CdrSearchForm, \
                        CountryReportForm, \
                        CdrOverviewForm, \
                        CompareCallSearchForm, \
                        ConcurrentCallForm, \
                        SwitchForm, \
                        WorldForm, \
                        EmailReportForm
from frontend.forms import LoginForm
from user_profile.models import UserProfile
from cdr.aggregate import pipeline_cdr_view_daily_report,\
                          pipeline_monthly_overview,\
                          pipeline_daily_overview,\
                          pipeline_hourly_overview,\
                          pipeline_country_report,\
                          pipeline_hourly_report,\
                          pipeline_country_hourly_report,\
                          pipeline_mail_report

from bson.objectid import ObjectId
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import math
import csv
import time
import logging


cdr_data = settings.DBCON[settings.MG_CDR_COMMON]
#db.cdr.ensureIndex({"variables.answer_stamp":1}, {background:true});


def index(request):
    """Index Page of CDR-Stats

    **Attributes**:

        * ``template`` - frontend/index.html
        * ``form`` - loginForm
    """
    template = 'frontend/index.html'
    errorlogin = ''
    loginform = LoginForm()

    if request.GET.get('db_error'):
        if request.GET['db_error'] == 'closed':
            errorlogin = _('Mongodb Database connection is closed!')
        if request.GET['db_error'] == 'locked':
            errorlogin = _('Mongodb Database is locked!')

    code_error = _('Account code is not assigned!')
    if request.GET.get('acc_code_error'):
        if request.GET['acc_code_error'] == 'true':
            errorlogin = code_error

    data = {
        'module': current_view(request),
        'loginform': loginform,
        'errorlogin': errorlogin,
        'news': get_news(settings.NEWS_URL),
    }
    return render_to_response(template, data,
        context_instance=RequestContext(request))

@login_required
def notice_count(request):
    """Get count of logged in user's notifications"""
    notice_count = notification.Notice.objects\
        .filter(recipient=request.user,
                unseen=1)\
        .count()
    return notice_count


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
        sender = User.objects.get(username=recipient)
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


def check_cdr_exists(function=None):
    """
    decorator check if cdr exists if not go to error page
    """
    def _dec(run_func):
        """Decorator"""
        def _caller(request, *args, **kwargs):
            """Caller."""
            doc = cdr_data.find_one()
            if not doc:
                return render_to_response(
                    'frontend/error_import.html',
                    context_instance=RequestContext(request))
            else:
                return run_func(request, *args, **kwargs)
        return _caller
    return _dec(function) if function is not None else _dec


def show_menu(request):
    """Check if we suppose to show menu"""
    try:
        return request.GET.get('menu')
    except:
        return 'on'


def cdr_view_daily_report(query_var):
    logging.debug('Aggregate cdr analytic')
    pipeline = pipeline_cdr_view_daily_report(query_var)

    logging.debug('Before Aggregate')
    list_data = settings.DBCON.command('aggregate',
                                       settings.MG_DAILY_ANALYTIC,
                                       pipeline=pipeline)
    logging.debug('After Aggregate')

    total_data = []
    total_duration = 0
    total_calls = 0
    duration__avg = 0.0
    count_days = 0
    for doc in list_data['result']:
        count_days = count_days + 1

        total_data.append(
            {
                'calldate': datetime(int(doc['_id'][0:4]),
                                     int(doc['_id'][4:6]),
                                     int(doc['_id'][6:8])),
                'duration__sum': int(doc['duration_per_day']),
                'calldate__count': int(doc['call_per_day']),
                'duration__avg': doc['avg_duration_per_day'],
            })

        total_duration += int(doc['duration_per_day'])
        total_calls += int(doc['call_per_day'])
        duration__avg += float(doc['avg_duration_per_day'])

    if count_days != 0:
        max_duration = max([int(x['duration__sum']) for x in total_data])
        total_avg_duration = (float(duration__avg)) / count_days
    else:
        max_duration = 0
        total_avg_duration = 0

    cdr_view_daily_data = {
        'total_data': total_data,
        'total_duration': total_duration,
        'total_calls': total_calls,
        'total_avg_duration': total_avg_duration,
        'max_duration': max_duration,
    }
    return cdr_view_daily_data


@check_cdr_exists
@login_required
def cdr_view(request):
    """List of CDRs

    **Attributes**:

        * ``template`` - frontend/cdr_view.html
        * ``form`` - CdrSearchForm
        * ``mongodb_data_set`` - MG_CDR_COMMON

    **Logic Description**:

        get the call records as well as daily call analytics
        from mongodb collection according to search parameters
    """
    template_name = 'frontend/cdr_view.html'
    logging.debug('CDR View Start')
    query_var = {}
    result = 1  # default min
    switch_id = 0  # default all
    hangup_cause_id = 0  # default all
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
    cdr_view_daily_data = {}
    if request.method == 'POST':
        logging.debug('CDR Search View')
        search_tag = 1
        request.session['session_search_tag'] = search_tag
        form = CdrSearchForm(request.POST)
        if form.is_valid():
            # set session var value
            request.session['session_destination'] = ''
            request.session['session_result'] = ''
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
            request.session['session_country_id'] = ''
            request.session['session_cdr_view_daily_data'] = {}

            if "from_date" in request.POST:
                # From
                from_date = request.POST['from_date']
                start_date = ceil_strdate(from_date, 'start')
                request.session['session_from_date'] = from_date

            if "to_date" in request.POST:
                # To
                to_date = request.POST['to_date']
                end_date = ceil_strdate(to_date, 'end')
                request.session['session_to_date'] = to_date

            result = request.POST['result']
            if result:
                request.session['session_result'] = int(result)

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
            if direction and direction != 'all':
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

            country_id = form.cleaned_data.get('country_id')
            # convert list value in int
            country_id = [int(row) for row in country_id]
            if len(country_id) >= 1:
                request.session['session_country_id'] = country_id
        else:
            # form is not valid
            logging.debug('Error : CDR search form')
            rows = []
            PAGE_SIZE = settings.PAGE_SIZE
            total_duration = 0
            total_calls = 0
            total_avg_duration = 0
            max_duration = 0
            col_name_with_order = []
            detail_data = []
            tday = datetime.today()
            start_date = tday.strftime('%Y-%m-01')
            last_day = ((datetime(tday.year, tday.month, 1, 23, 59, 59, 999999) \
                        + relativedelta(months=1)) \
                        - relativedelta(days=1)).strftime('%d')
            end_date = tday.strftime('%Y-%m-' + last_day)
            template_data = {
                'module': current_view(request),
                'rows': rows,
                'form': form,
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
                'result': result,
                'notice_count': notice_count(request),
            }
            logging.debug('CDR View End')
            return render_to_response(template_name, template_data,
                context_instance=RequestContext(request))

    menu = show_menu(request)

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
            result = int(request.session.get('session_result'))
            search_tag = request.session.get('session_search_tag')
            records_per_page = request.session.get('session_records_per_page')
            country_id = request.session['session_country_id']
            cdr_view_daily_data = request.session.get(
                                            'session_cdr_view_daily_data')
        else:
            from_date
    except NameError:
        tday = datetime.today()
        from_date = tday.strftime('%Y-%m-01')
        last_day = ((datetime(tday.year, tday.month, 1, 23, 59, 59, 999999) + \
                    relativedelta(months=1)) - \
                    relativedelta(days=1)).strftime('%d')
        to_date = tday.strftime('%Y-%m-' + last_day)
        search_tag = 0
        country_id = ''
        records_per_page = settings.PAGE_SIZE
        # unset session var value
        request.session['session_result'] = 1
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
        request.session['session_cdr_view_daily_data'] = {}

    start_date = datetime(int(from_date[0:4]), int(from_date[5:7]), \
                          int(from_date[8:10]), 0, 0, 0, 0)
    end_date = datetime(int(to_date[0:4]), int(to_date[5:7]), \
                        int(to_date[8:10]), 23, 59, 59, 999999)
    query_var['start_uepoch'] = {'$gte': start_date, '$lt': end_date}

    # Mapreduce query variable
    mr_query_var = {}
    mr_query_var['metadata.date'] = {'$gte': start_date, '$lt': end_date}

    dst = mongodb_str_filter(destination, destination_type)
    if dst:
        query_var['destination_number'] = dst

    if request.user.is_superuser:
        # superuser can see everything
        acc = mongodb_str_filter(accountcode, accountcode_type)
        if acc:
            mr_query_var['metadata.accountcode'] = acc
            query_var['accountcode'] = acc

    if not request.user.is_superuser:
        # not superuser can only see his own data
        if not chk_account_code(request):
            return HttpResponseRedirect('/?acc_code_error=true')
        else:
            mr_query_var['metadata.accountcode'] = chk_account_code(request)
            query_var['accountcode'] = mr_query_var['metadata.accountcode']

    cli = mongodb_str_filter(caller, caller_type)
    if cli:
        query_var['caller_id_number'] = cli

    due = mongodb_int_filter(duration, duration_type)
    if due:
        query_var['duration'] = mr_query_var['duration_daily'] = due

    if switch_id and int(switch_id) != 0:
        mr_query_var['metadata.switch_id'] = int(switch_id)
        query_var['switch_id'] = int(switch_id)

    if hangup_cause_id and int(hangup_cause_id) != 0:
        query_var['hangup_cause_id'] = int(hangup_cause_id)

    if direction and direction != 'all':
        query_var['direction'] = str(direction)

    if len(country_id) >= 1 and country_id[0] != 0:
        mr_query_var['metadata.country_id'] = {'$in': country_id}
        query_var['country_id'] = {'$in': country_id}

    # Define no of records per page
    PAGE_SIZE = int(records_per_page)
    try:
        PAGE_NUMBER = int(request.GET['page'])
    except:
        PAGE_NUMBER = 1

    final_result = cdr_data.find(query_var,
                        {
                            "uuid": 0,
                            "answer_uepoch": 0,
                            "end_uepoch": 0,
                            "mduration": 0,
                            "billmsec": 0,
                            "read_codec": 0,
                            "write_codec": 0,
                            "remote_media_ip": 0,
                        })

    form = CdrSearchForm(initial={
                            'from_date': from_date,
                            'to_date': to_date,
                            'destination': destination,
                            'destination_type': destination_type,
                            'accountcode': accountcode,
                            'accountcode_type': accountcode_type,
                            'caller': caller,
                            'caller_type': caller_type,
                            'duration': duration,
                            'duration_type': duration_type,
                            'result': result,
                            'direction': direction,
                            'hangup_cause': hangup_cause_id,
                            'switch': switch_id,
                            'country_id': country_id,
                            'records_per_page': records_per_page
                            })

    request.session['query_var'] = query_var

    col_name_with_order = {}
    sort_field = variable_value(request, 'sort_by')
    if not sort_field:
        sort_field = 'start_uepoch'  # default sort field
        default_order = -1  # desc
    else:
        if '-' in sort_field:
            default_order = -1
            sort_field = sort_field[1:]
            col_name_with_order[sort_field] = sort_field
        else:
            default_order = 1
            col_name_with_order[sort_field] = '-' + sort_field

    col_name_with_order['sort_field'] = sort_field

    logging.debug('Create cdr result')

    rows = final_result.skip(PAGE_SIZE * (PAGE_NUMBER - 1))\
                .limit(PAGE_SIZE)\
                .sort([(sort_field, default_order)])

    # Get daily report from session while using pagination & sorting
    if request.GET.get('page') or request.GET.get('sort_by'):
        cdr_view_daily_data = request.session['session_cdr_view_daily_data']
    else:
        # pass mapreduce query to cdr_view_daily_report
        cdr_view_daily_data = cdr_view_daily_report(mr_query_var)
        request.session['session_cdr_view_daily_data'] = cdr_view_daily_data

    template_data = {
        'module': current_view(request),
        'rows': rows,
        'form': form,
        'PAGE_SIZE': PAGE_SIZE,
        'total_data': cdr_view_daily_data['total_data'],
        'total_duration': cdr_view_daily_data['total_duration'],
        'total_calls': cdr_view_daily_data['total_calls'],
        'total_avg_duration': cdr_view_daily_data['total_avg_duration'],
        'max_duration': cdr_view_daily_data['max_duration'],
        'user': request.user,
        'search_tag': search_tag,
        'col_name_with_order': col_name_with_order,
        'menu': menu,
        'start_date': start_date,
        'end_date': end_date,
        'action': action,
        'result': int(result),
        'notice_count': notice_count(request),
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

    query_var = request.session['query_var']
    final_result = cdr_data.find(query_var, {"uuid": 0,
                                             "answer_uepoch": 0,
                                             "end_uepoch": 0,
                                             "mduration": 0,
                                             "billmsec": 0,
                                             "read_codec": 0,
                                             "write_codec": 0,
                                             "remote_media_ip": 0
                                            })

    writer = csv.writer(response, dialect=csv.excel_tab)
    writer.writerow(['Call-date', 'CLID', 'Destination', 'Duration', \
                     'Bill sec', 'Hangup cause', 'AccountCode', 'Direction'])

    for cdr in final_result:
        writer.writerow([
                         cdr['start_uepoch'],
                         cdr['caller_id_number'] + '-' + cdr['caller_id_name'],
                         cdr['destination_number'],
                         cdr['duration'],
                         cdr['billsec'],
                         get_hangupcause_name(cdr['hangup_cause_id']),
                         cdr['accountcode'],
                         cdr['direction']
                       ])
    return response


@login_required
def cdr_detail(request, id, switch_id):
    """Detail of Call

    **Attributes**:

        * ``template`` - frontend/cdr_detail.html

    **Logic Description**:

        get the single call record in detail from mongodb collection
    """
    c_switch = get_object_or_404(Switch, id=switch_id)
    ipaddress = c_switch.ipaddress
    menu = show_menu(request)

    if settings.LOCAL_SWITCH_TYPE == 'freeswitch':
        #Connect on MongoDB Database
        host = settings.CDR_BACKEND[ipaddress]['host']
        port = settings.CDR_BACKEND[ipaddress]['port']
        db_name = settings.CDR_BACKEND[ipaddress]['db_name']
        table_name = settings.CDR_BACKEND[ipaddress]['table_name']
        try:
            connection = Connection(host, port)
            DBCON = connection[db_name]
        except ConnectionFailure:
            raise Http404

        doc = DBCON[table_name].find({'_id': ObjectId(id)})
        return render_to_response(
                        'frontend/cdr_detail_freeswitch.html',
                        {'row': list(doc), 'menu': menu},
                        context_instance=RequestContext(request))

    elif settings.LOCAL_SWITCH_TYPE == 'asterisk':
        #Connect on Mysql Database
        #TODO: support other DBMS
        #TODO: Support postgresql
        import MySQLdb as Database
        db_name = settings.CDR_BACKEND[ipaddress]['db_name']
        table_name = settings.CDR_BACKEND[ipaddress]['table_name']
        user = settings.CDR_BACKEND[ipaddress]['user']
        password = settings.CDR_BACKEND[ipaddress]['password']
        host = settings.CDR_BACKEND[ipaddress]['host']
        try:
            connection = Database.connect(user=user, passwd=password,
                                          db=db_name, host=host)
            cursor = connection.cursor()
        except:
            raise Http404

        #TODO: SQL for different DBMS
        cursor.execute("SELECT dst, UNIX_TIMESTAMP(calldate), clid, channel, "\
                        "duration, billsec, disposition, accountcode, " \
                        "uniqueid, %s FROM %s WHERE %s=%s" % \
                        (settings.ASTERISK_PRIMARY_KEY, table_name,
                        settings.ASTERISK_PRIMARY_KEY, id))
        row = cursor.fetchone()
        if not row:
            raise Http404

        return render_to_response(
                            'frontend/cdr_detail_asterisk.html',
                            {'row': list(row), 'menu': menu},
                            context_instance=RequestContext(request))


def chk_date_for_hrs(graph_date):
    """Check given graph_date is in last 24 hours range

    >>> graph_date = datetime(2012, 8, 20)

    >>> chk_date_for_hrs(graph_date)
    False
    """
    previous_date = datetime.now() - relativedelta(days=1)
    if graph_date > previous_date:
        return True
    return False


def calculate_act_and_acd(total_calls, total_duration):
    """Calculate the Average Time of Call

    >>> calculate_act_and_acd(5, 100)
    {'ACD': '00:20', 'ACT': 0.0}
    """
    ACT = math.floor(total_calls / 24)
    if total_calls == 0:
        ACD = 0
    else:
        ACD = int_convert_to_minute(math.floor(total_duration / total_calls))

    return {'ACT': ACT, 'ACD': ACD}


@check_cdr_exists
@login_required
def cdr_dashboard(request):
    """CDR dashboard for a current day

    **Attributes**:

        * ``template`` - frontend/cdr_dashboard.html
        * ``form`` - SwitchForm
        * ``mongodb_data_set`` - MG_DAILY_ANALYTIC

    **Logic Description**:

        get all call records from mongodb collection for current day
        to create hourly report as well as hangup cause/country analytics
    """
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
                query_var['metadata.switch_id'] = int(switch_id)

    end_date = datetime(now.year, now.month, now.day,
                        now.hour, now.minute, now.second, now.microsecond)
    # -2 cause the collection metadata.date only contains year-month-day
    start_date = end_date + relativedelta(days=-2)

    query_var['metadata.date'] = {'$gte': start_date, '$lt': end_date}

    if not request.user.is_superuser:  # not superuser
        if chk_account_code(request):
            query_var['metadata.accountcode'] = chk_account_code(request)
        else:
            return HttpResponseRedirect('/?acc_code_error=true')

    logging.debug('cdr dashboard analytic')

    daily_data = settings.DBCON[settings.MG_DAILY_ANALYTIC]
    not_require_field = {'call_daily': 0,
                         'call_hourly': 0,
                         'duration_daily': 0,
                         'duration_hourly': 0}
    logging.debug('Before daily_data.find')
    daily_data = daily_data.find(query_var, not_require_field)\
                        .sort([('metadata.date', 1),
                               ('metadata.country_id', 1),
                               ('metadata.hangup_cause_id', 1)])
    logging.debug('After daily_data.find')
    total_calls = 0
    total_duration = 0

    hangup_analytic = dict()
    country_all_data = dict()
    final_record = dict()

    for i in daily_data:
        calldate_dict = i['call_minute']
        duration_dict = i['duration_minute']
        if len(calldate_dict) > 0:
            for call_hour, min_dict in calldate_dict.iteritems():
                for min, count_val in min_dict.iteritems():
                    calldate__count = int(calldate_dict[call_hour][min])
                    if calldate__count > 0:
                        a_Year = int(i['metadata']['date'].strftime('%Y'))
                        b_Month = int(i['metadata']['date'].strftime('%m'))
                        c_Day = int(i['metadata']['date'].strftime('%d'))
                        graph_day = datetime(int(a_Year), int(b_Month),
                                             int(c_Day), int(call_hour),
                                             int(min))
                        dt = int(1000 * time.mktime(graph_day.timetuple()))
                        # check graph date
                        if chk_date_for_hrs(graph_day):
                            duration__sum = int(duration_dict[call_hour][min])

                            if int(dt) in final_record:
                                final_record[dt]['duration_sum'] += duration__sum
                                final_record[dt]['count_call'] += calldate__count
                            else:
                                final_record[dt] = {
                                    'duration_sum': duration__sum,
                                    'count_call': calldate__count
                                }

                            total_calls += calldate__count
                            total_duration += duration__sum

                            # created hangup_analytic
                            hc = int(i['metadata']['hangup_cause_id'])
                            if hc in hangup_analytic:
                                hangup_analytic[hc] += calldate__count
                            else:
                                hangup_analytic[hc] = calldate__count

                            country_id = int(i['metadata']['country_id'])
                            if country_id in country_all_data:
                                country_all_data[country_id]['call_count'] += calldate__count
                                country_all_data[country_id]['duration_sum'] += duration__sum
                            else:
                                country_all_data[country_id] = {
                                    'call_count': calldate__count,
                                    'duration_sum': duration__sum
                                }

    logging.debug('After loop to handle data')

    # sorting on date col
    final_record = final_record.items()
    final_record = sorted(final_record, key=lambda k: k[0])

    hangup_analytic = hangup_analytic.items()

    total_country_data = country_all_data.items()
    total_country_data = sorted(total_country_data,
                                key=lambda k: (k[1]['call_count'],
                                               k[1]['duration_sum']),
                                reverse=True)

    logging.debug("Result total_record_final %d" % len(final_record))
    logging.debug("Result hangup_analytic %d" % len(hangup_analytic))
    logging.debug("Result country_call_count %d" % len(total_country_data))

    #Calculate the Average Time of Call
    act_acd_array = calculate_act_and_acd(total_calls, total_duration)
    ACT = act_acd_array['ACT']
    ACD = act_acd_array['ACD']

    logging.debug('CDR dashboard view end')
    variables = {
        'module': current_view(request),
        'total_calls': total_calls,
        'total_duration': int_convert_to_minute(total_duration),
        'ACT': ACT,
        'ACD': ACD,
        'total_record': final_record,
        'hangup_analytic': hangup_analytic,
        'form': form,
        'search_tag': search_tag,
        'notice_count': notice_count(request),
        'total_country_data': total_country_data[0:5],
    }

    return render_to_response('frontend/cdr_dashboard.html', variables,
           context_instance=RequestContext(request))


@check_cdr_exists
@login_required
def cdr_concurrent_calls(request):
    """CDR view of concurrent calls

    **Attributes**:

        * ``template`` - frontend/cdr_graph_concurrent_calls.html
        * ``form`` - ConcurrentCallForm
        * ``mongodb_data_set`` - MG_CONC_CALL_AGG (map-reduce collection)

    **Logic Description**:

        get all concurrent call records from mongodb map-reduce collection for
        current date
    """
    logging.debug('CDR concurrent view start')
    query_var = {}
    switch_id = 0
    if request.method == 'POST':
        logging.debug('CDR concurrent view with search option')
        form = ConcurrentCallForm(request.POST)
        if form.is_valid():
            if "from_date" in request.POST and request.POST['from_date'] != '':
                from_date = request.POST['from_date']
                start_date = ceil_strdate(from_date, 'start')
                end_date = ceil_strdate(from_date, 'end')

            switch_id = form.cleaned_data.get('switch')
            if switch_id and int(switch_id) != 0:
                query_var['_id.f_Switch'] = int(switch_id)
    else:
        now = datetime.today()
        from_date = now.strftime('%Y-%m-%d')
        start_date = datetime(now.year, now.month, now.day, 0, 0, 0, 0)
        end_date = datetime(now.year, now.month, now.day, 23, 59, 59, 0)
        form = ConcurrentCallForm(initial={'from_date': from_date})

    query_var['value.call_date'] = {'$gte': start_date, '$lt': end_date}

    if not request.user.is_superuser:  # not superuser
        if chk_account_code(request):
            query_var['value.accountcode'] = chk_account_code(request)
        else:
            return HttpResponseRedirect('/?acc_code_error=true')

    final_data = []
    if query_var:
        calls_in_day = settings.DBCON[settings.MG_CONC_CALL_AGG]
        calls_in_day = calls_in_day.find(query_var).\
                                sort([('_id.g_Millisec', 1)])

        for d in calls_in_day.clone():
            final_data.append({'millisec': int(d['_id']['g_Millisec']),
                               'call__count': int(d['value']['numbercall__max']),
                               'switch_id': int(d['_id']['f_Switch'])})

        logging.debug('CDR concurrent view end')
        variables = {
            'module': current_view(request),
            'form': form,
            'final_data': final_data,
            'start_date': start_date,
            'notice_count': notice_count(request),
        }

    return render_to_response('frontend/cdr_graph_concurrent_calls.html', variables,
           context_instance=RequestContext(request))


@login_required
def cdr_realtime(request):
    """Call realtime view

    **Attributes**:

        * ``template`` - frontend/cdr_realtime.html
        * ``form`` - SwitchForm
        * ``mongodb_collection`` - MG_CONC_CALL_AGG (map-reduce collection)

    **Logic Description**:

        get all call records from mongodb collection for
        concurrent analytics
    """
    logging.debug('CDR realtime view start')
    query_var = {}
    switch_id = 0
    if request.method == 'POST':
        logging.debug('CDR realtime view with search option')
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

    if not request.user.is_superuser:  # not superuser
        if chk_account_code(request):
            query_var['value.accountcode'] = chk_account_code(request)
        else:
            return HttpResponseRedirect('/?acc_code_error=true')

    if query_var:
        calls_in_day = settings.DBCON[settings.MG_CONC_CALL_AGG]
        calls_in_day = calls_in_day.find(query_var).\
                                sort([('_id.g_Millisec', -1)])

        final_data = []
        for d in calls_in_day:
            dt = int(d['_id']['g_Millisec'])
            final_data.append((dt, int(d['value']['numbercall__max'])))

        logging.debug('Realtime view end')
        list_switch = Switch.objects.all()
        variables = {
            'module': current_view(request),
            'form': form,
            'final_data': final_data,
            'list_switch': list_switch,
            'user_id': request.user.id,
            'colorgraph1': '180, 0, 0',
            'colorgraph2': '0, 180, 0',
            'colorgraph3': '0, 0, 180',
            'realtime_graph_maxcall': settings.REALTIME_Y_AXIS_LIMIT,
            'socketio_host': settings.SOCKETIO_HOST,
            'socketio_port': settings.SOCKETIO_PORT,
            'notice_count': notice_count(request),
        }

    return render_to_response('frontend/cdr_graph_realtime.html', variables,
           context_instance=RequestContext(request))


def get_cdr_mail_report():
    """General function to get previous day CDR report"""
    # Get yesterday's CDR-Stats Mail Report
    query_var = {}
    yesterday = date.today() - timedelta(1)
    start_date = datetime(yesterday.year, yesterday.month,
                          yesterday.day, 0, 0, 0, 0)
    end_date = datetime(yesterday.year, yesterday.month,
                        yesterday.day, 23, 59, 59, 999999)

    query_var['start_uepoch'] = {'$gte': start_date, '$lt': end_date}

    # result set
    final_result =\
        cdr_data.find(query_var).sort([('start_uepoch', -1)]).limit(10)

    # Collect analytics
    logging.debug('Aggregate cdr mail report')
    pipeline = pipeline_mail_report(query_var)

    logging.debug('Before Aggregate')
    list_data = settings.DBCON.command('aggregate',
                                       settings.MG_CDR_COMMON,
                                       pipeline=pipeline)
    logging.debug('After Aggregate')

    total_duration = 0
    total_calls = 0
    country_analytic = dict()
    hangup_analytic = dict()
    if list_data:
        for doc in list_data['result']:
            total_duration += doc['duration_sum']
            total_calls += int(doc['call_count'])

            # created cdr_hangup_analytic
            hangup_cause_id = int(doc['_id']['hangup_cause_id'])
            if hangup_cause_id in hangup_analytic:
                hangup_analytic[hangup_cause_id] += 1
            else:
                hangup_analytic[hangup_cause_id] = 1

            country_id = int(doc['_id']['country_id'])
            if country_id in country_analytic:
                country_analytic[country_id]['call_count'] +=\
                    int(doc['call_count'])
                country_analytic[country_id]['duration_sum'] +=\
                    doc['duration_sum']
            else:
                country_analytic[country_id] = {
                    'call_count': int(doc['call_count']),
                    'duration_sum': doc['duration_sum']
                }

    #Calculate the Average Time of Call
    act_acd_array = calculate_act_and_acd(total_calls, total_duration)
    ACT = act_acd_array['ACT']
    ACD = act_acd_array['ACD']

    country_analytic = country_analytic.items()
    country_analytic = sorted(country_analytic,
                              key=lambda k: (k[1]['call_count'],
                                             k[1]['duration_sum']),
                              reverse=True)

    # Hangup Cause analytic end
    hangup_analytic_array = []
    hangup_analytic = hangup_analytic.items()
    hangup_analytic = sorted(hangup_analytic, key=lambda k: k[0])
    if len(hangup_analytic) != 0:
        total_hangup = sum([int(x[1]) for x in hangup_analytic])
        for i in hangup_analytic:
            hangup_analytic_array.append(
                (get_hangupcause_name(int(i[0])),
                "{0:.0f}%".format((float(i[1]) / float(total_hangup)) * 100)))

    mail_data = {
        'yesterday_date': start_date,
        'rows': final_result,
        'total_duration': total_duration,
        'total_calls': total_calls,
        'ACT': ACT,
        'ACD': ACD,
        'country_analytic_array': country_analytic[0:5],
        'hangup_analytic_array': hangup_analytic_array,
    }
    return mail_data


@check_cdr_exists
@login_required
def mail_report(request):
    """Mail Report Template

    **Attributes**:

        * ``template`` - frontend/cdr_mail_report.html
        * ``form`` - MailreportForm
        * ``mongodb_data_set`` - MG_CDR_COMMON

    **Logic Description**:

        get top 10 calls from mongodb collection & hnagupcause/country analytic
        to generate mail report
    """
    logging.debug('CDR mail report view start')
    template = 'frontend/cdr_mail_report.html'
    user_obj = User.objects.get(username=request.user)
    msg = ''
    try:
        user_profile_obj = UserProfile.objects.get(user=user_obj)
    except UserProfile.DoesNotExist:
        #create UserProfile
        user_profile_obj = UserProfile(user=user_obj)
        user_profile_obj.save()

    form = EmailReportForm(request.user, instance=user_profile_obj)
    if request.method == 'POST':
        form = EmailReportForm(request.user, request.POST,
                               instance=user_profile_obj)
        if form.is_valid():
            form.save()
            msg = _('Email ids are saved successfully.')

    mail_data = get_cdr_mail_report()
    logging.debug('CDR mail report view end')
    data = {
        'module': current_view(request),
        'yesterday_date': mail_data['yesterday_date'],
        'rows': mail_data['rows'],
        'form': form,
        'total_duration': mail_data['total_duration'],
        'total_calls': mail_data['total_calls'],
        'ACT': mail_data['ACT'],
        'ACD': mail_data['ACD'],
        'country_analytic_array': mail_data['country_analytic_array'],
        'hangup_analytic_array': mail_data['hangup_analytic_array'],
        'msg': msg,
        'notice_count': notice_count(request),
    }
    return render_to_response(template, data,
           context_instance=RequestContext(request))


def get_hourly_report_for_date(start_date, end_date, query_var, graph_view):
    """Get Hourly report for date"""
    logging.debug('Aggregate cdr hourly report')
    pipeline = pipeline_hourly_report(query_var)
    logging.debug('Before Aggregate')
    list_data = settings.DBCON.command('aggregate',
                                       settings.MG_DAILY_ANALYTIC,
                                       pipeline=pipeline)

    total_record = {}
    if list_data:
        for doc in list_data['result']:
            called_time = datetime(int(doc['_id'][0:4]),
                                   int(doc['_id'][4:6]),
                                   int(doc['_id'][6:8]))
            day_hours = {}
            for hr in range(0, 24):
                day_hours[hr] = 0

            if graph_view == 1:  # Calls per hour
                for dict_in_list in doc['call_per_hour']:
                    for key, value in dict_in_list.iteritems():
                        day_hours[int(key)] += int(value)

                total_record[str(called_time)[:10]] = day_hours

            if graph_view == 2:  # Min per hour
                for dict_in_list in doc['duration_per_hour']:
                    for key, value in dict_in_list.iteritems():
                        day_hours[int(key)] += float(value)/60

                total_record[str(called_time)[:10]] = day_hours

    logging.debug('After Aggregate')

    variables = {
        'total_record': total_record,
    }
    return variables


@check_cdr_exists
@login_required
def cdr_report_by_hour(request):
    """CDR graph by hourly basis

    **Attributes**:

        * ``template`` - frontend/cdr_report_by_hour.html
        * ``form`` - CompareCallSearchForm
        * ``mongodb_data_set`` - MG_DAILY_ANALYTIC
        * ``map_reduce`` - mapreduce_cdr_hourly_analytic()

    **Logic Description**:

        get all call records from mongodb collection for
        hourly analytics for given date
    """
    logging.debug('CDR hourly view start')
    template_name = 'frontend/cdr_report_by_hour.html'
    query_var = {}
    total_record = []
    #default
    comp_days = 2
    graph_view = 1
    check_days = 1
    search_tag = 0
    tday = datetime.today()
    from_date = tday.strftime('%Y-%m-%d')
    form = CompareCallSearchForm(initial={'from_date': from_date,
                                          'comp_days': comp_days,
                                          'check_days': check_days,
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
            graph_view = int(variable_value(request, 'graph_view'))
            check_days = int(variable_value(request, 'check_days'))
            # check previous days
            if check_days == 2:
                compare_date_list = []
                compare_date_list.append(select_date)

                for i in range(1, int(comp_days) + 1):
                    #select_date+relativedelta(weeks=-i)
                    interval_date = select_date + relativedelta(weeks=-i)
                    compare_date_list.append(interval_date)

            switch_id = form.cleaned_data.get('switch')
            if switch_id and int(switch_id) != 0:
                query_var['metadata.switch_id'] = int(switch_id)

            if from_date != '':
                end_date = from_date = select_date
                start_date = end_date + \
                                relativedelta(days=-int(comp_days))
                start_date = datetime(start_date.year, start_date.month,
                                      start_date.day, 0, 0, 0, 0)
                end_date = datetime(end_date.year, end_date.month,
                                    end_date.day, 23, 59, 59, 999999)
                if check_days == 1:
                    query_var['metadata.date'] = {
                                                    '$gte': start_date,
                                                    '$lt': end_date
                                                 }
        else:
            # form is not valid
            logging.debug('Error : CDR hourly search form')
            total_record = []
            variables = {
                'module': current_view(request),
                'form': form,
                'result': 'min',
                'graph_view': graph_view,
                'search_tag': search_tag,
                'from_date': from_date,
                'comp_days': comp_days,
                'total_record': total_record,
                'notice_count': notice_count(request),
            }

            return render_to_response(template_name, variables,
                            context_instance=RequestContext(request))

    if len(query_var) == 0:
        from_date = datetime.today()
        from_day = validate_days(from_date.year,
                                 from_date.month,
                                 from_date.day)
        from_year = from_date.year
        from_month = from_date.month
        end_date = datetime(from_year, from_month, from_day)
        start_date = end_date + relativedelta(days=-comp_days)
        start_date = datetime(start_date.year, start_date.month,
                              start_date.day, 0, 0, 0, 0)
        end_date = datetime(end_date.year, end_date.month,
                            end_date.day, 23, 59, 59, 999999)
        query_var['metadata.date'] = {'$gte': start_date, '$lt': end_date}

    if not request.user.is_superuser:  # not superuser
        if chk_account_code(request):
            query_var['metadata.accountcode'] = chk_account_code(request)
        else:
            return HttpResponseRedirect('/?acc_code_error=true')

    if query_var:
        if check_days == 2:
            for i in compare_date_list:
                s_date = datetime(i.year, i.month, i.day, 0, 0, 0, 0)
                e_date = datetime(i.year, i.month, i.day, 23, 59, 59, 999999)
                query_var['metadata.date'] = {'$gte': s_date, '$lt': e_date}
                result_data = \
                    get_hourly_report_for_date(s_date, e_date,
                                               query_var, graph_view)
                total_record.append((result_data['total_record']))

        if check_days == 1:
            result_data = \
                get_hourly_report_for_date(start_date, end_date,
                                           query_var, graph_view)
            total_record.append((result_data['total_record']))

        logging.debug('CDR hourly view end')
        variables = {
            'module': current_view(request),
            'form': form,
            'result': 'min',
            'graph_view': graph_view,
            'search_tag': search_tag,
            'from_date': from_date,
            'comp_days': comp_days,
            'total_record': total_record,
            'notice_count': notice_count(request),
        }

        return render_to_response(template_name, variables,
                                context_instance=RequestContext(request))


@check_cdr_exists
@login_required
def cdr_overview(request):
    """CDR graph by hourly/daily/monthly basis

    **Attributes**:

        * ``template`` - frontend/cdr_overview.html.html
        * ``form`` - CdrOverviewForm
        * ``mongodb_data_set`` - MG_DAILY_ANALYTIC

    **Logic Description**:

        get all call records from mongodb collection for
        all monthly, daily, hourly analytics
    """
    template_name = 'frontend/cdr_overview.html'
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
                from_date = request.POST['from_date']
                start_date = ceil_strdate(from_date, 'start')
            else:
                from_date = tday.strftime('%Y-%m-%d')

            if "to_date" in request.POST:
                to_date = request.POST['to_date']
                end_date = ceil_strdate(to_date, 'end')
            else:
                to_date = tday.strftime('%Y-%m-%d')

            switch_id = form.cleaned_data.get('switch')
            if switch_id and int(switch_id) != 0:
                query_var['metadata.switch_id'] = int(switch_id)

            if from_date != '' and to_date != '':
                start_date = ceil_strdate(from_date, 'start')
                end_date = ceil_strdate(to_date, 'end')
                query_var['metadata.date'] = {
                    '$gte': start_date,
                    '$lt': end_date
                }

                month_start_date = datetime(start_date.year, start_date.month,
                    1, 0, 0, 0, 0)
                month_end_date = datetime(end_date.year, end_date.month,
                    end_date.day, 23, 59, 59, 999999)
        else:
            # form is not valid
            logging.debug('Error : CDR overview search form')
            total_hour_record = []
            total_hour_data = []
            total_day_record = []
            total_day_data = []
            total_month_record = []
            total_month_data = []

            tday = datetime.today()
            start_date = datetime(tday.year, tday.month,
                tday.day, 0, 0, 0, 0)
            end_date = datetime(tday.year, tday.month,
                tday.day, 23, 59, 59, 999999)

            variables = {
                'module': current_view(request),
                'form': form,
                'search_tag': search_tag,
                'total_hour_record': total_hour_record,
                'total_hour_data': total_hour_data,
                'total_day_record': total_day_record,
                'total_day_data': total_day_data,
                'total_month_record': total_month_record,
                'total_month_data': total_month_data,
                'start_date': start_date,
                'end_date': end_date,
                'TOTAL_GRAPH_COLOR': settings.TOTAL_GRAPH_COLOR,
                'notice_count': notice_count(request),
            }

            return render_to_response(
                template_name, variables,
                context_instance=RequestContext(request)
            )

    if len(query_var) == 0:
        tday = datetime.today()
        switch_id = 0
        form = CdrOverviewForm(initial={'from_date': tday.strftime('%Y-%m-%d'),
                                        'to_date': tday.strftime('%Y-%m-%d'),
                                        'switch': switch_id})

        start_date = datetime(tday.year, tday.month, tday.day, 0, 0, 0, 0)
        end_date = datetime(tday.year, tday.month,
                            tday.day, 23, 59, 59, 999999)
        month_start_date = datetime(start_date.year,
                                    start_date.month, 1, 0, 0, 0, 0)
        month_end_date = datetime(end_date.year, end_date.month,
                                  end_date.day, 23, 59, 59, 999999)

        query_var['metadata.date'] = {'$gte': start_date, '$lt': end_date}

    if not request.user.is_superuser:  # not superuser
        if chk_account_code(request):
            query_var['metadata.accountcode'] = chk_account_code(request)
        else:
            return HttpResponseRedirect('/?acc_code_error=true')

    if query_var:
        logging.debug('Map-reduce cdr overview analytic')
        # Collect Hourly data
        logging.debug('Aggregate cdr hourly overview')
        pipeline = pipeline_hourly_overview(query_var)

        logging.debug('Before Aggregate')
        list_data = settings.DBCON.command('aggregate',
                                           settings.MG_DAILY_ANALYTIC,
                                           pipeline=pipeline)
        logging.debug('After Aggregate')

        total_hour_record = []
        total_hour_data = []
        hour_data = dict()
        if list_data:
            for doc in list_data['result']:
                a_Year = int(doc['_id'][0:4])
                b_Month = int(doc['_id'][4:6])
                c_Day = int(doc['_id'][6:8])
                day_hours = dict()

                for dict_in_list in doc['call_per_hour']:
                    for key, value in dict_in_list.iteritems():
                        key = int(key)
                        graph_day = datetime(a_Year, b_Month, c_Day, key)
                        dt = int(1000 * time.mktime(graph_day.timetuple()))

                        if key in day_hours:
                            day_hours[key]['calldate__count'] += int(value)
                        else:
                            day_hours[key] = {
                                'dt': dt,
                                'calldate__count': int(value),
                                'duration__sum': 0,
                                'switch_id': int(doc['switch_id'])
                            }

                for dict_in_list in doc['duration_per_hour']:
                    for key, value in dict_in_list.iteritems():
                        day_hours[int(key)]['duration__sum'] += int(value)

                        # To avoid duplicate entry in total_hour_record
                        if not day_hours[int(key)] in total_hour_record:
                            total_hour_record.append(day_hours[int(key)])

                            # All switches hourly data
                            temp_dt = day_hours[int(key)]['dt']
                            temp_call_count = int(day_hours[int(key)]['calldate__count'])
                            temp_duration_sum = day_hours[int(key)]['duration__sum']
                            if temp_dt in hour_data:
                                hour_data[temp_dt]['call_count'] += temp_call_count
                                hour_data[temp_dt]['duration_sum'] += temp_duration_sum
                            else:
                                hour_data[temp_dt] = {
                                    'call_count': temp_call_count,
                                    'duration_sum': temp_duration_sum
                                }

        total_hour_record = sorted(total_hour_record, key=lambda k: k['dt'])

        total_hour_data = hour_data.items()
        total_hour_data = sorted(total_hour_data, key=lambda k: k[0])

        # Collect daily data
        ####################
        logging.debug('Aggregate cdr daily analytic')
        pipeline = pipeline_daily_overview(query_var)

        logging.debug('Before Aggregate')
        list_data = settings.DBCON.command('aggregate',
                                           settings.MG_DAILY_ANALYTIC,
                                           pipeline=pipeline)
        logging.debug('After Aggregate')

        total_day_record = []
        total_day_data = []
        if list_data:
            day_data = dict()
            for doc in list_data['result']:
                graph_day = datetime(int(doc['_id'][0:4]),
                                     int(doc['_id'][4:6]),
                                     int(doc['_id'][6:8]),
                                     0, 0, 0, 0)
                dt = int(1000 * time.mktime(graph_day.timetuple()))

                total_day_record.append({
                    'dt': dt,
                    'calldate__count': int(doc['call_per_day']),
                    'duration__sum': int(doc['duration_per_day']),
                    'switch_id': int(doc['switch_id'])
                })

                if dt in day_data:
                    day_data[dt]['call_count'] += int(doc['call_per_day'])
                    day_data[dt]['duration_sum'] += int(doc['duration_per_day'])
                else:
                    day_data[dt] = {
                        'call_count': int(doc['call_per_day']),
                        'duration_sum': int(doc['duration_per_day']),
                    }

            total_day_data = day_data.items()
            total_day_data = sorted(total_day_data, key=lambda k: k[0])

        # Collect monthly data
        ######################
        logging.debug('Aggregate cdr monthly analytic')
        query_var['metadata.date'] = {
            '$gte': month_start_date,
            '$lt': month_end_date
        }
        pipeline = pipeline_monthly_overview(query_var)

        logging.debug('Before Aggregate')
        list_data = settings.DBCON.command('aggregate',
                                           settings.MG_MONTHLY_ANALYTIC,
                                           pipeline=pipeline)
        logging.debug('After Aggregate')

        total_month_record = []
        total_month_data = []
        if list_data:
            month_data = dict()
            for doc in list_data['result']:
                graph_month = datetime(int(doc['_id'][0:4]),
                                       int(doc['_id'][4:6]),
                                       1, 0, 0, 0, 0)
                dt = int(1000 * time.mktime(graph_month.timetuple()))

                total_month_record.append({
                    'dt': dt,
                    'calldate__count': int(doc['call_per_month']),
                    'duration__sum': int(doc['duration_per_month']),
                    'switch_id': int(doc['switch_id'])
                })

                if dt in month_data:
                    month_data[dt]['call_count'] +=\
                        int(doc['call_per_month'])
                    month_data[dt]['duration_sum'] +=\
                        int(doc['duration_per_month'])
                else:
                    month_data[dt] = {
                        'call_count': int(doc['call_per_month']),
                        'duration_sum': int(doc['duration_per_month'])
                    }

            total_month_data = month_data.items()
            total_month_data = sorted(total_month_data, key=lambda k: k[0])

        logging.debug('CDR daily view end')
        variables = {
            'module': current_view(request),
            'form': form,
            'search_tag': search_tag,
            'total_hour_record': total_hour_record,
            'total_hour_data': total_hour_data,
            'total_day_record': total_day_record,
            'total_day_data': total_day_data,
            'total_month_record': total_month_record,
            'total_month_data': total_month_data,
            'start_date': start_date,
            'end_date': end_date,
            'TOTAL_GRAPH_COLOR': settings.TOTAL_GRAPH_COLOR,
            'notice_count': notice_count(request),
        }

        return render_to_response(template_name, variables,
            context_instance=RequestContext(request))


@check_cdr_exists
@login_required
def cdr_country_report(request):
    """CDR country report

    **Attributes**:

        * ``template`` - frontend/cdr_country_report.html
        * ``form`` - CountryReportForm
        * ``mongodb_data_set`` - MG_DAILY_ANALYTIC

    **Logic Description**:

        get all call records from mongodb collection for all countries
        to create country call
    """
    logging.debug('CDR country report view start')
    template_name = 'frontend/cdr_country_report.html'
    form = CountryReportForm()

    switch_id = 0
    query_var = {}
    search_tag = 0
    now = datetime.now()
    start_date = datetime(now.year, now.month, now.day, 0, 0, 0, 0)
    end_date = datetime(now.year, now.month, now.day, 23, 59, 59, 999999)
    from_date = start_date.strftime("%Y-%m-%d")
    to_date = end_date.strftime("%Y-%m-%d")
    form = CountryReportForm(initial={'from_date': from_date,
                                      'to_date': to_date})

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
                start_date = ceil_strdate(from_date, 'start')

            if "to_date" in request.POST:
                # To
                to_date = form.cleaned_data.get('to_date')
                end_date = ceil_strdate(to_date, 'end')

            country_id = form.cleaned_data.get('country_id')
            # convert list value in int
            country_id = [int(row) for row in country_id]
            if len(country_id) >= 1 and country_id[0] != 0:
                query_var['metadata.country_id'] = {'$in': country_id}

            switch_id = form.cleaned_data.get('switch')
            if switch_id and int(switch_id) != 0:
                query_var['metadata.switch_id'] = int(switch_id)

            duration = form.cleaned_data.get('duration')
            duration_type = form.cleaned_data.get('duration_type')
            if duration:
                due = mongodb_int_filter(duration, duration_type)
                temp = []
                if due:
                    for i in range(0, 24):
                        temp.append({'duration_hourly.%d' % (i) : due})
                    query_var['$or'] = temp
        else:
            country_analytic_array = []
            logging.debug('Error : CDR country report form')
            variables = {
                'module': current_view(request),
                'total_calls': total_calls,
                'total_duration': total_duration,
                'total_record': total_record_final,
                'country_final': country_analytic_array,
                'form': form,
                'search_tag': search_tag,
                'NUM_COUNTRY': settings.NUM_COUNTRY,
            }

            return render_to_response(template_name, variables,
                context_instance=RequestContext(request))

    query_var['metadata.date'] = {'$gte': start_date, '$lt': end_date}

    if not request.user.is_superuser:  # not superuser
        if chk_account_code(request):
            query_var['metadata.accountcode'] = chk_account_code(request)
        else:
            return HttpResponseRedirect('/?acc_code_error=true')

    # Country daily data
    pipeline = pipeline_country_hourly_report(query_var)

    logging.debug('Before Aggregate')
    list_data = settings.DBCON.command('aggregate',
                                       settings.MG_DAILY_ANALYTIC,
                                       pipeline=pipeline)
    total_record_final = []
    if list_data:
        for doc in list_data['result']:
            a_Year = int(doc['_id']['date'][0:4])
            b_Month = int(doc['_id']['date'][5:7])
            c_Day = int(doc['_id']['date'][8:10])

            day_hours = dict()
            for hr in range(0, 24):
                graph_day = datetime(a_Year, b_Month, c_Day, int(hr))
                dt = int(1000 * time.mktime(graph_day.timetuple()))
                day_hours[hr] = {
                    'dt': dt,
                    'calldate__count': 0,
                    'duration__sum': 0,
                    'country_id': doc['_id']['country_id']
                }

            for dict_in_list in doc['call_per_hour']:
                for key, value in dict_in_list.iteritems():
                    day_hours[int(key)]['calldate__count'] += int(value)

            for dict_in_list in doc['duration_per_hour']:
                for key, value in dict_in_list.iteritems():
                    day_hours[int(key)]['duration__sum'] += int(value)

                    total_record_final.append(day_hours[int(key)])

        total_record_final = sorted(total_record_final, key=lambda k: k['dt'])

    # World report
    logging.debug('Aggregate world report')
    pipeline = pipeline_country_report(query_var)

    logging.debug('Before Aggregate')
    list_data = settings.DBCON.command('aggregate',
                                       settings.MG_DAILY_ANALYTIC,
                                       pipeline=pipeline)
    logging.debug('After Aggregate')
    country_analytic_array = []
    country_final = []
    if list_data:
        for doc in list_data['result']:
            #country id - country name - call count - call duration - country_id
            # _id = country id
            country_analytic_array.append(
                (get_country_name(int(doc['_id'])),
                 int(doc['call_per_day']),
                 int(doc['duration_per_day']),
                 int(doc['_id'])))

            total_calls += int(doc['call_per_day'])
            total_duration += int(doc['duration_per_day'])

    logging.debug('CDR country report view end')
    variables = {
        'module': current_view(request),
        'total_calls': total_calls,
        'total_duration': total_duration,
        'total_record': total_record_final,
        'country_analytic': country_analytic_array,
        'form': form,
        'search_tag': search_tag,
        'NUM_COUNTRY': settings.NUM_COUNTRY,
        'notice_count': notice_count(request),
    }
    return render_to_response(template_name, variables,
        context_instance=RequestContext(request))


@check_cdr_exists
def world_map_view(request):
    """CDR world report

    **Attributes**:

        * ``template`` - frontend/world_map.html
        * ``form`` - WorldForm
        * ``mongodb_data_set`` - MG_DAILY_ANALYTIC

    **Logic Description**:

        get all call records from mongodb collection for all countries
        to create country call
    """
    logging.debug('CDR world report view start')
    template_name = 'frontend/world_map.html'

    switch_id = 0
    query_var = {}
    search_tag = 0
    now = datetime.now()
    start_date = datetime(now.year, now.month, now.day, 0, 0, 0, 0)
    end_date = datetime(now.year, now.month, now.day, 23, 59, 59, 999999)
    from_date = start_date.strftime("%Y-%m-%d")
    to_date = end_date.strftime("%Y-%m-%d")
    form = WorldForm(initial={'from_date': from_date, 'to_date': to_date})
    action = 'tabs-1'

    if request.method == 'POST':
        logging.debug('CDR world report view with search option')
        search_tag = 1
        form = WorldForm(request.POST)
        if form.is_valid():
            if "from_date" in request.POST:
                # From
                from_date = form.cleaned_data.get('from_date')
                start_date = ceil_strdate(from_date, 'start')

            if "to_date" in request.POST:
                # To
                to_date = form.cleaned_data.get('to_date')
                end_date = ceil_strdate(to_date, 'end')

            switch_id = form.cleaned_data.get('switch')
            if switch_id and int(switch_id) != 0:
                query_var['metadata.switch_id'] = int(switch_id)

        else:
            world_analytic_array = []
            logging.debug('Error : CDR world report form')
            variables = {
                'module': current_view(request),
                'form': form,
                'search_tag': search_tag,
                'start_date': start_date,
                'end_date': end_date,
                'world_analytic_array': world_analytic_array,
                'action': action,
                'notice_count': notice_count(request),
            }

            return render_to_response(template_name, variables,
                context_instance=RequestContext(request))

    query_var['metadata.date'] = {'$gte': start_date, '$lt': end_date}

    if not request.user.is_superuser:  # not superuser
        if chk_account_code(request):
            query_var['metadata.accountcode'] = chk_account_code(request)
        else:
            return HttpResponseRedirect('/?acc_code_error=true')

    logging.debug('Aggregate world report')
    pipeline = pipeline_country_report(query_var)

    logging.debug('Before Aggregate')
    list_data = settings.DBCON.command('aggregate',
                                       settings.MG_DAILY_ANALYTIC,
                                       pipeline=pipeline)
    logging.debug('After Aggregate')
    world_analytic_array = []
    if list_data:
        for doc in list_data['result']:
            #country id - country name - call count - call duration - country_id
            # _id = country id
            world_analytic_array.append((int(doc['_id']),
                                         get_country_name(int(doc['_id']), type='iso2'),
                                         int(doc['call_per_day']),
                                         doc['duration_per_day'],
                                         get_country_name(int(doc['_id']))))

    logging.debug('CDR world report view end')

    variables = {
        'module': current_view(request),
        'form': form,
        'search_tag': search_tag,
        'start_date': start_date,
        'end_date': end_date,
        'world_analytic_array': world_analytic_array,
        'action': action,
        'notice_count': notice_count(request),
    }
    return render_to_response(template_name, variables,
        context_instance=RequestContext(request))
