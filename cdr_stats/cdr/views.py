#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2013 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#
from django.contrib.auth.decorators import login_required,\
    permission_required
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.utils.translation import gettext as _
from django.conf import settings
from mongodb_connection import mongodb
from pymongo.connection import Connection
from pymongo.errors import ConnectionFailure
from django_lets_go.common_functions import current_view, get_news, \
    variable_value, mongodb_str_filter, mongodb_int_filter, \
    int_convert_to_minute, validate_days, percentage, \
    getvar, unset_session_var
from cdr.models import Switch
from cdr.functions_def import get_country_name, get_hangupcause_name,\
    get_switch_ip_addr, convert_to_minute
from cdr.forms import CdrSearchForm, \
    CountryReportForm, CdrOverviewForm, CompareCallSearchForm, \
    ConcurrentCallForm, SwitchForm, WorldForm, EmailReportForm
from cdr.aggregate import pipeline_cdr_view_daily_report,\
    pipeline_monthly_overview, pipeline_daily_overview,\
    pipeline_hourly_overview, pipeline_country_report,\
    pipeline_hourly_report, pipeline_country_hourly_report,\
    pipeline_mail_report
from cdr.decorators import check_cdr_exists, check_user_accountcode, \
    check_user_voipplan
from cdr.constants import CDR_COLUMN_NAME, Export_choice
from voip_billing.function_def import get_rounded_value
from bson.objectid import ObjectId
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import math
import tablib
import time
import logging
import itertools


def ceil_strdate(str_date, start, hour_min=False):
    """convert a string date to either a start or end day date"""
    str_date = str_date.strftime('%Y-%m-%d %H:%M')
    if start == 'start':
        if hour_min:
            return datetime(int(str_date[0:4]), int(str_date[5:7]),
                int(str_date[8:10]), int(str_date[11:13]), int(str_date[14:16]), 0, 0)
        else:
            return datetime(int(str_date[0:4]), int(str_date[5:7]), int(str_date[8:10]), 0, 0, 0, 0)
    else:
        if hour_min:
            return datetime(int(str_date[0:4]), int(str_date[5:7]), int(str_date[8:10]), int(str_date[11:13]), int(str_date[14:16]), 0, 0)
        else:
            return datetime(int(str_date[0:4]), int(str_date[5:7]), int(str_date[8:10]), 23, 59, 59, 999999)


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
    list_data = mongodb.DBCON.command('aggregate',
                                      settings.MONGO_CDRSTATS['DAILY_ANALYTIC'],
                                      pipeline=pipeline)
    logging.debug('After Aggregate')

    total_data = []
    total_duration = 0
    total_calls = 0
    duration__avg = 0.0
    count_days = 0
    total_buy_cost = 0.0
    total_sell_cost = 0.0
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
                'buy_cost': float(doc['buy_cost_per_day']),
                'sell_cost': float(doc['sell_cost_per_day']),
            })

        total_duration += int(doc['duration_per_day'])
        total_calls += int(doc['call_per_day'])
        duration__avg += float(doc['avg_duration_per_day'])
        total_buy_cost += float(doc['buy_cost_per_day'])
        total_sell_cost += float(doc['sell_cost_per_day'])

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
        'total_buy_cost': total_buy_cost,
        'total_sell_cost': total_sell_cost,
    }
    return cdr_view_daily_data


def get_pagination_vars(request, default_sort_field='start_uepoch'):
    """Pagination data for mongodb cdr_common collection"""
    PAGE_NUMBER = int(request.GET.get('page', 1))

    # get sorting field and sorting order
    col_name_with_order = {}
    sort_field = variable_value(request, 'sort_by')
    if not sort_field:
        sort_field = default_sort_field  # default sort field
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

    data = {
        'PAGE_NUMBER': PAGE_NUMBER,
        'col_name_with_order': col_name_with_order,
        'sort_field': sort_field,
        'default_order': default_order,
    }
    return data


@permission_required('user_profile.search', login_url='/')
@check_cdr_exists
@check_user_accountcode
@check_user_voipplan
@login_required
def cdr_view(request):
    """List of CDRs

    **Attributes**:

        * ``template`` - frontend/cdr_view.html
        * ``form`` - CdrSearchForm
        * ``mongodb_data_set`` - mongodb.cdr_common

    **Logic Description**:

        get the call records as well as daily call analytics
        from mongodb collection according to search parameters
    """
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
    form = CdrSearchForm(request.POST or None)
    if form.is_valid():
        logging.debug('CDR Search View')
        search_tag = 1
        request.session['session_search_tag'] = search_tag
        # set session var value
        field_list = ['destination', 'result', 'destination_type', 'accountcode',
                      'accountcode_type', 'caller', 'caller_type', 'duration',
                      'duration_type', 'hangup_cause_id', 'switch_id', 'direction',
                      'country_id']
        unset_session_var(request, field_list)

        request.session['session_cdr_view_daily_data'] = {}

        from_date = str(getvar(request, 'from_date', setsession=True))
        to_date = str(getvar(request, 'to_date', setsession=True))
        result = getvar(request, 'result', setsession=True)
        destination = getvar(request, 'destination', setsession=True)
        destination_type = getvar(request, 'destination_type', setsession=True)
        accountcode = getvar(request, 'accountcode', setsession=True)
        accountcode_type = getvar(request, 'accountcode_type', setsession=True)
        caller = getvar(request, 'caller', setsession=True)
        caller_type = getvar(request, 'caller_type', setsession=True)
        duration = getvar(request, 'duration', setsession=True)
        duration_type = getvar(request, 'duration_type', setsession=True)
        direction = getvar(request, 'direction', setsession=True)
        if direction and direction != 'all':
            request.session['session_direction'] = str(direction)

        switch_id = getvar(request, 'switch_id', setsession=True)
        hangup_cause_id = getvar(request, 'hangup_cause_id', setsession=True)
        records_per_page = getvar(request, 'records_per_page', setsession=True)

        country_id = form.cleaned_data.get('country_id')
        # convert list value in int
        country_id = [int(row) for row in country_id]
        if len(country_id) >= 1:
            request.session['session_country_id'] = country_id

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
            cdr_view_daily_data = request.session.get('session_cdr_view_daily_data')
        else:
            from_date
    except NameError:
        tday = datetime.today()
        from_date = tday.strftime('%Y-%m-01 00:00')
        last_day = ((datetime(tday.year, tday.month, 1, 23, 59, 59, 999999) +
                    relativedelta(months=1)) -
                    relativedelta(days=1)).strftime('%d')
        to_date = tday.strftime('%Y-%m-' + last_day + ' 23:59')
        search_tag = 0
        country_id = ''
        records_per_page = settings.PAGE_SIZE
        # unset session var value
        request.session['session_result'] = 1
        request.session['session_from_date'] = from_date
        request.session['session_to_date'] = to_date

        field_list = ['destination', 'destination_type', 'accountcode',
                      'accountcode_type', 'caller', 'caller_type', 'duration',
                      'duration_type', 'hangup_cause_id', 'switch_id', 'direction',
                      'country_id']
        unset_session_var(request, field_list)

        request.session['session_search_tag'] = search_tag
        request.session['session_records_per_page'] = records_per_page
        request.session['session_country_id'] = ''
        request.session['session_cdr_view_daily_data'] = {}

    start_date = ceil_strdate(from_date, 'start', True)  # .strftime('%Y-%m-%d %H:%M')
    end_date = ceil_strdate(to_date, 'end', True)

    query_var['start_uepoch'] = {'$gte': start_date, '$lt': end_date}

    # aggregate query variable
    daily_report_query_var = {}
    daily_report_query_var['metadata.date'] = {'$gte': start_date, '$lt': end_date}

    dst = mongodb_str_filter(destination, destination_type)
    if dst:
        query_var['destination_number'] = dst

    if request.user.is_superuser:
        # superuser can see everything
        acc = mongodb_str_filter(accountcode, accountcode_type)
        if acc:
            daily_report_query_var['metadata.accountcode'] = acc
            query_var['accountcode'] = acc

    if not request.user.is_superuser:
        daily_report_query_var['metadata.accountcode'] = request.user.get_profile().accountcode
        query_var['accountcode'] = daily_report_query_var['metadata.accountcode']

    cli = mongodb_str_filter(caller, caller_type)
    if cli:
        query_var['caller_id_number'] = cli

    due = mongodb_int_filter(duration, duration_type)
    if due:
        query_var['duration'] = daily_report_query_var['duration_daily'] = due

    if switch_id and int(switch_id) != 0:
        daily_report_query_var['metadata.switch_id'] = int(switch_id)
        query_var['switch_id'] = int(switch_id)

    if hangup_cause_id and int(hangup_cause_id) != 0:
        daily_report_query_var['metadata.hangup_cause_id'] = int(hangup_cause_id)
        query_var['hangup_cause_id'] = int(hangup_cause_id)

    if direction and direction != 'all':
        query_var['direction'] = str(direction)

    if len(country_id) >= 1 and country_id[0] != 0:
        daily_report_query_var['metadata.country_id'] = {'$in': country_id}
        query_var['country_id'] = {'$in': country_id}

    final_result = mongodb.cdr_common.find(query_var,
        {
            "uuid": 0,
            "answer_uepoch": 0,
            "end_uepoch": 0,
            "mduration": 0,
            "billmsec": 0,
            "read_codec": 0,
            "write_codec": 0,
            "remote_media_ip": 0,
        }
    )

    form = CdrSearchForm(
        initial={
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
            'hangup_cause_id': hangup_cause_id,
            'switch_id': switch_id,
            'country_id': country_id,
            'records_per_page': records_per_page
        }
    )

    request.session['query_var'] = query_var

    # Define no of records per page
    PAGE_SIZE = int(records_per_page)
    pagination_data = get_pagination_vars(request)

    PAGE_NUMBER = pagination_data['PAGE_NUMBER']
    col_name_with_order = pagination_data['col_name_with_order']
    sort_field = pagination_data['sort_field']
    default_order = pagination_data['default_order']

    logging.debug('Create cdr result')
    SKIP_NO = PAGE_SIZE * (PAGE_NUMBER - 1)
    record_count = final_result.count()
    # perform pagination on cdr_common collection via skip() and limit()
    rows = final_result.skip(SKIP_NO).limit(PAGE_SIZE).sort([(sort_field, default_order)])

    # Get daily report from session while using pagination & sorting
    if request.GET.get('page') or request.GET.get('sort_by'):
        cdr_view_daily_data = request.session['session_cdr_view_daily_data']
    else:
        # pass aggregate query to cdr_view_daily_report
        cdr_view_daily_data = cdr_view_daily_report(daily_report_query_var)
        request.session['session_cdr_view_daily_data'] = cdr_view_daily_data

    template_data = {
        'module': current_view(request),
        'rows': rows,
        'form': form,
        'record_count': record_count,
        'PAGE_SIZE': PAGE_SIZE,
        'cdr_daily_data': cdr_view_daily_data,
        'search_tag': search_tag,
        'col_name_with_order': col_name_with_order,
        'menu': menu,
        'start_date': start_date,
        'end_date': end_date,
        'action': action,
        'result': result,
        'CDR_COLUMN_NAME': CDR_COLUMN_NAME,
    }

    logging.debug('CDR View End')
    return render_to_response('cdr/list.html', template_data, context_instance=RequestContext(request))


@login_required
def cdr_export_to_csv(request):
    """
    **Logic Description**:

        get the call records  from mongodb collection
        according to search parameters & store into csv file
    """
    format = request.GET['format']
    # get the response object, this can be used as a stream
    response = HttpResponse(mimetype='text/' + format)
    # force download
    response['Content-Disposition'] = 'attachment;filename=export.' + format

    # get query_var from request.session
    query_var = request.session.get('query_var')

    final_result = mongodb.cdr_common.find(query_var,
        {
            "uuid": 0,
            "answer_uepoch": 0,
            "end_uepoch": 0,
            "mduration": 0,
            "billmsec": 0,
            "read_codec": 0,
            "write_codec": 0,
            "remote_media_ip": 0,
        }
    )

    headers = ('Call-date', 'CLID', 'Destination', 'Duration',
               'Bill sec', 'Hangup cause', 'AccountCode', 'Direction')

    list_val = []
    for cdr in final_result:
        starting_date = cdr['start_uepoch']
        if format == Export_choice.JSON:
            starting_date = str(cdr['start_uepoch'])

        list_val.append((
            starting_date,
            cdr['caller_id_number'] + '-' + cdr['caller_id_name'],
            cdr['destination_number'],
            cdr['duration'],
            cdr['billsec'],
            get_hangupcause_name(cdr['hangup_cause_id']),
            cdr['accountcode'],
            cdr['direction'],
        ))
    data = tablib.Dataset(*list_val, headers=headers)

    if format == Export_choice.XLS:
        response.write(data.xls)

    if format == Export_choice.CSV:
        response.write(data.csv)

    if format == Export_choice.JSON:
        response.write(data.json)

    return response


@permission_required('user_profile.cdr_detail', login_url='/')
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

    db_engine = settings.CDR_BACKEND[ipaddress]['db_engine']
    cdr_type = settings.CDR_BACKEND[ipaddress]['cdr_type']

    if cdr_type == 'freeswitch':
        #Connect on MongoDB Database
        host = settings.CDR_BACKEND[ipaddress]['host']
        port = settings.CDR_BACKEND[ipaddress]['port']
        db_name = settings.CDR_BACKEND[ipaddress]['db_name']
        table_name = settings.CDR_BACKEND[ipaddress]['table_name']
        user = settings.CDR_BACKEND[ipaddress]['user']
        password = settings.CDR_BACKEND[ipaddress]['password']
        try:
            connection = Connection(host, port)
            DBCON = connection[db_name]
            DBCON.autentificate(user, password)
        except ConnectionFailure:
            raise Http404

        doc = DBCON[table_name].find({'_id': ObjectId(id)})
        data = {'row': list(doc), 'menu': menu}
        return render_to_response('cdr/detail_freeswitch.html', data, context_instance=RequestContext(request))

    elif cdr_type == 'asterisk':
        #Connect on Database
        db_name = settings.CDR_BACKEND[ipaddress]['db_name']
        table_name = settings.CDR_BACKEND[ipaddress]['table_name']
        user = settings.CDR_BACKEND[ipaddress]['user']
        password = settings.CDR_BACKEND[ipaddress]['password']
        host = settings.CDR_BACKEND[ipaddress]['host']
        try:
            if db_engine == 'mysql':
                import MySQLdb as Database
                connection = Database.connect(user=user, passwd=password,
                    db=db_name, host=host, port=port, connect_timeout=4)
                connection.autocommit(True)
                cursor = connection.cursor()
            elif db_engine == 'pgsql':
                import psycopg2 as Database
                connection = Database.connect(user=user, password=password,
                    database=db_name, host=host, port=port)
                connection.autocommit(True)
                cursor = connection.cursor()
        except:
            raise Http404

        cursor.execute(
            "SELECT dst, calldate, clid, src, dst, dcontext, channel, dstchannel "
            "lastapp, duration, billsec, disposition, amaflags, accountcode, "
            "uniqueid, userfield, %s FROM %s WHERE %s=%s" %
            (settings.ASTERISK_PRIMARY_KEY, table_name,
            settings.ASTERISK_PRIMARY_KEY, id))
        row = cursor.fetchone()
        if not row:
            raise Http404
        data = {'row': list(row), 'menu': menu}
        return render_to_response('cdr/detail_asterisk.html', data, context_instance=RequestContext(request))


def chk_date_for_hrs(previous_date, graph_date):
    """Check given graph_date is in last 24 hours range

    >>> graph_date = datetime(2012, 8, 20)

    >>> chk_date_for_hrs(graph_date)
    False
    """
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


@permission_required('user_profile.dashboard', login_url='/')
@check_cdr_exists
@check_user_accountcode
@check_user_voipplan
@login_required
def cdr_dashboard(request):
    """CDR dashboard for a current day

    **Attributes**:

        * ``template`` - frontend/cdr_dashboard.html
        * ``form`` - SwitchForm
        * ``mongodb_data_set`` - MONGO_CDRSTATS['DAILY_ANALYTIC']

    **Logic Description**:

        get all call records from mongodb collection for current day
        to create hourly report as well as hangup cause/country analytics
    """
    logging.debug('CDR dashboard view start')
    now = datetime.now()
    form = SwitchForm(request.POST or None)
    switch_id = 0
    query_var = {}

    if form.is_valid():
        logging.debug('CDR dashboard view with search option')
        switch_id = form.cleaned_data.get('switch_id')
        if switch_id and int(switch_id) != 0:
            query_var['metadata.switch_id'] = int(switch_id)

    end_date = datetime(now.year, now.month, now.day,
                        now.hour, now.minute, now.second, now.microsecond)
    # -2 cause the collection metadata.date only contains year-month-day
    start_date = end_date + relativedelta(days=-2)

    query_var['metadata.date'] = {'$gte': start_date, '$lt': end_date}

    if not request.user.is_superuser:  # not superuser
        query_var['metadata.accountcode'] = request.user.get_profile().accountcode

    logging.debug('cdr dashboard analytic')

    not_require_field = {'call_daily': 0,
                         'call_hourly': 0,
                         'duration_daily': 0,
                         'duration_hourly': 0}
    logging.debug('Before daily_data.find')
    if not mongodb.daily_analytic:
        raise Http404
    daily_data = mongodb.daily_analytic.find(query_var, not_require_field)\
        .sort([('metadata.date', 1),
               ('metadata.country_id', 1),
               ('metadata.hangup_cause_id', 1)])
    logging.debug('After daily_data.find')
    # initialize variables
    total_calls = 0
    total_duration = 0
    total_buy_cost = 0.0
    total_sell_cost = 0.0
    previous_date = datetime.now() - relativedelta(days=1)

    hangup_analytic = dict()
    country_all_data = dict()
    final_record = dict()

    for i in daily_data:
        # get individual dict variable from daily_data
        calldate_dict = i['call_minute']
        duration_dict = i['duration_minute']
        buy_cost_dict = i['buy_cost_minute']
        sell_cost_dict = i['sell_cost_minute']

        # get date info from daily_data
        a_Year = int(i['metadata']['date'].strftime('%Y'))
        b_Month = int(i['metadata']['date'].strftime('%m'))
        c_Day = int(i['metadata']['date'].strftime('%d'))
        country_id = int(i['metadata']['country_id'])
        hc = int(i['metadata']['hangup_cause_id'])

        if len(calldate_dict) > 0:
            # get key(call_hour) - value(min_dict) from calldate_dict
            for call_hour, min_dict in calldate_dict.iteritems():
                # get key(min) - value(count_val) from min_dict
                for min, count_val in min_dict.iteritems():
                    calldate__count = int(calldate_dict[call_hour][min])

                    if calldate__count > 0:
                        # Get graph_day from aggregate result array
                        graph_day = datetime(a_Year, b_Month, c_Day,
                                             int(call_hour), int(min))
                        # convert date into timestamp value
                        dt = int(1000 * time.mktime(graph_day.timetuple()))

                        # check graph date
                        if chk_date_for_hrs(previous_date, graph_day):
                            duration__sum = int(duration_dict[call_hour][min])
                            buy_cost__sum = float(buy_cost_dict[call_hour][min])
                            sell_cost__sum = float(sell_cost_dict[call_hour][min])

                            # if timestamp value in final_record, then update dict value
                            if dt in final_record:
                                final_record[dt]['duration_sum'] += duration__sum
                                final_record[dt]['count_call'] += calldate__count
                                final_record[dt]['buy_cost_sum'] += buy_cost__sum
                                final_record[dt]['sell_cost_sum'] += sell_cost__sum
                            else:
                                # assign new timestamp value in final_record with dict value
                                final_record[dt] = {
                                    'duration_sum': duration__sum,
                                    'count_call': calldate__count,
                                    'buy_cost_sum': buy_cost__sum,
                                    'sell_cost_sum': sell_cost__sum,
                                }

                            # make total values of calls, duration, buy_cost, sell_cost
                            total_calls += calldate__count
                            total_duration += duration__sum
                            total_buy_cost += buy_cost__sum
                            total_sell_cost += sell_cost__sum

                            # created hangup_analytic
                            if hc in hangup_analytic:
                                hangup_analytic[hc] += calldate__count
                            else:
                                hangup_analytic[hc] = calldate__count

                            # created country_analytic
                            if country_id in country_all_data:
                                country_all_data[country_id]['call_count'] += calldate__count
                                country_all_data[country_id]['duration_sum'] += duration__sum
                                country_all_data[country_id]['buy_cost_sum'] += buy_cost__sum
                                country_all_data[country_id]['sell_cost_sum'] += sell_cost__sum
                            else:
                                country_all_data[country_id] = {
                                    'call_count': calldate__count,
                                    'duration_sum': duration__sum,
                                    'buy_cost_sum': buy_cost__sum,
                                    'sell_cost_sum': sell_cost__sum
                                }
    logging.debug('*** After loop to handle data ***')

    # sorting on timestamp col
    final_record = final_record.items()
    final_record = sorted(final_record, key=lambda k: k[0])

    xdata = []
    ydata = []
    ydata2 = []
    ydata3 = []
    ydata4 = []
    for i in final_record:
        xdata.append(i[0])
        ydata.append(i[1]['count_call'])
        ydata2.append(i[1]['duration_sum'])
        ydata3.append(i[1]['buy_cost_sum'])
        ydata4.append(i[1]['sell_cost_sum'])

    tooltip_date = "%d %b %y %H:%M %p"
    extra_serie1 = {"tooltip": {"y_start": "", "y_end": " calls"}, "date_format": tooltip_date}
    extra_serie2 = {"tooltip": {"y_start": "", "y_end": " sec"}, "date_format": tooltip_date}
    extra_serie3 = {"tooltip": {"y_start": "", "y_end": ""}, "date_format": tooltip_date}
    extra_serie4 = {"tooltip": {"y_start": "", "y_end": ""}, "date_format": tooltip_date}

    final_chartdata = {
        'x': xdata,
        'name1': 'Calls', 'y1': ydata, 'extra1': extra_serie1,
        'name2': 'Duration', 'y2': ydata2, 'extra2': extra_serie2,
        'name3': 'Buy cost', 'y3': ydata3, 'extra3': extra_serie3,
        'name4': 'Sell cost', 'y4': ydata4, 'extra4': extra_serie4,
    }
    final_charttype = "lineWithFocusChart"

    # hangup analytic pie chart data
    hangup_analytic = hangup_analytic.items()
    xdata = []
    ydata = []
    for i in hangup_analytic:
        xdata.append(str(get_hangupcause_name(i[0])))
        ydata.append(percentage(i[1], total_calls))

    extra_serie = {"tooltip": {"y_start": "", "y_end": " %"}}
    hangup_analytic_chartdata = {'x': xdata, 'y1': ydata, 'extra1': extra_serie}
    hangup_analytic_charttype = "pieChart"

    # sorting on call_count, duration_sum col
    total_country_data = country_all_data.items()
    total_country_data = sorted(total_country_data,
                                key=lambda k: (k[1]['call_count'],
                                               k[1]['duration_sum']),
                                reverse=True)
    # country analytic pie chart data
    xdata = []
    ydata = []
    for i in total_country_data:
        xdata.append(str(get_country_name(i[0])))
        ydata.append(percentage(i[1]['call_count'], total_calls))

    extra_serie = {"tooltip": {"y_start": "", "y_end": " %"}}
    country_analytic_chartdata = {'x': xdata, 'y1': ydata, 'extra1': extra_serie}
    country_analytic_charttype = "pieChart"

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
        'total_buy_cost': total_buy_cost,
        'total_sell_cost': total_sell_cost,
        'ACT': ACT,
        'ACD': ACD,
        'total_record': final_record,
        'hangup_analytic': hangup_analytic,
        'form': form,
        'total_country_data': total_country_data[0:5],

        'final_chartdata': final_chartdata,
        'final_charttype': final_charttype,
        'final_chartcontainer': 'final_container',
        'final_extra': {
            'x_is_date': True,
            'x_axis_format': '%H:%M',
            'tag_script_js': True,
            'jquery_on_ready': True,
        },
        'hangup_analytic_charttype': hangup_analytic_charttype,
        'hangup_analytic_chartdata': hangup_analytic_chartdata,
        'hangup_chartcontainer': 'hangup_piechart_container',
        'hangup_extra': {
            'x_is_date': False,
            'x_axis_format': '',
            'tag_script_js': True,
            'jquery_on_ready': True,
        },
        'country_analytic_charttype': country_analytic_charttype,
        'country_analytic_chartdata': country_analytic_chartdata,
        'country_chartcontainer': 'country_piechart_container',
        'country_extra': {
            'x_is_date': False,
            'x_axis_format': '',
            'tag_script_js': True,
            'jquery_on_ready': True,
        },
    }

    return render_to_response('cdr/dashboard.html', variables, context_instance=RequestContext(request))


@permission_required('user_profile.concurrent_calls', login_url='/')
@check_cdr_exists
@check_user_accountcode
@login_required
def cdr_concurrent_calls(request):
    """CDR view of concurrent calls

    **Attributes**:

        * ``template`` - frontend/cdr_graph_concurrent_calls.html
        * ``form`` - ConcurrentCallForm
        * ``mongodb_data_set`` - MONGO_CDRSTATS['CONC_CALL_AGG'] (map-reduce collection)

    **Logic Description**:

        get all concurrent call records from mongodb map-reduce collection for
        current date
    """
    logging.debug('CDR concurrent view start')
    query_var = {}
    switch_id = 0
    form = ConcurrentCallForm(request.POST or None)
    logging.debug('CDR concurrent view with search option')

    if form.is_valid():
        if "from_date" in request.POST and request.POST['from_date'] != '':
            from_date = request.POST['from_date']
            start_date = ceil_strdate(from_date, 'start')
            end_date = ceil_strdate(from_date, 'end')

        switch_id = form.cleaned_data.get('switch_id')
        if switch_id and int(switch_id) != 0:
            query_var['switch_id'] = int(switch_id)
    else:
        now = datetime.today()
        from_date = now.strftime('%Y-%m-%d')
        start_date = datetime(now.year, now.month, now.day, 0, 0, 0, 0)
        end_date = datetime(now.year, now.month, now.day, 23, 59, 59, 0)
        form = ConcurrentCallForm(initial={'from_date': from_date})

    query_var['date'] = {'$gte': start_date, '$lt': end_date}

    if not request.user.is_superuser:  # not superuser
        query_var['accountcode'] = request.user.get_profile().accountcode

    xdata = []
    charttype = "stackedAreaChart"
    call_count_res = defaultdict(list)

    if query_var:
        if not mongodb.conc_call_agg:
            raise Http404
        calls_in_day = mongodb.conc_call_agg.find(query_var).sort([('date', 1)])

        for d in calls_in_day:
            # convert date into timestamp value
            ts = time.mktime(d['date'].timetuple())
            tsint = int(ts * 1000)
            xdata.append(str(tsint))
            call_count_res[d['switch_id']].append(d['numbercall'])

        chartdata = {
            'x': xdata,
        }

        int_count = 1
        extra_serie = {"tooltip": {"y_start": "", "y_end": " concurrent calls"},
                       "date_format": "%d %b %Y %I:%M:%S %p"}
        for i in call_count_res:
            chartdata['name' + str(int_count)] = str(get_switch_ip_addr(i))
            chartdata['y' + str(int_count)] = call_count_res[i]
            chartdata['extra' + str(int_count)] = extra_serie
            int_count += 1

        logging.debug('CDR concurrent view end')
        data = {
            'module': current_view(request),
            'form': form,
            'start_date': start_date,
            'chartdata': chartdata,
            'charttype': charttype,
            'chartcontainer': 'stacked_area_container',
            'chart_extra': {
                'x_is_date': True,
                'x_axis_format': '%d %b %Y %H:%S',
                'tag_script_js': True,
                'jquery_on_ready': True,
            },
        }
    return render_to_response('cdr/graph_concurrent_calls.html', data, context_instance=RequestContext(request))


@permission_required('user_profile.real_time_calls', login_url='/')
@check_user_accountcode
@login_required
def cdr_realtime(request):
    """Call realtime view

    **Attributes**:

        * ``template`` - frontend/cdr_realtime.html
        * ``form`` - SwitchForm
        * ``mongodb_collection`` - MONGO_CDRSTATS['CONC_CALL_AGG'] (map-reduce collection)

    **Logic Description**:

        get all call records from mongodb collection for
        concurrent analytics
    """
    logging.debug('CDR realtime view start')
    query_var = {}
    switch_id = 0
    form = SwitchForm(request.POST or None)
    if form.is_valid():
        switch_id = form.cleaned_data.get('switch_id')
        if switch_id and int(switch_id) != 0:
            query_var['value.switch_id'] = int(switch_id)

    now = datetime.now()
    start_date = datetime(now.year, now.month, now.day, 0, 0, 0, 0)
    end_date = datetime(now.year, now.month, now.day, 23, 59, 59, 999999)

    query_var['value.call_date'] = {'$gte': start_date, '$lt': end_date}

    if not request.user.is_superuser:  # not superuser
        query_var['value.accountcode'] = request.user.get_profile().accountcode

    if query_var:
        if not mongodb.conc_call_agg:
            raise mongodb.conc_call_agg
        calls_in_day = mongodb.conc_call_agg.find(query_var).sort([('_id.g_Millisec', -1)])

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
        }

    return render_to_response('cdr/graph_realtime.html', variables, context_instance=RequestContext(request))


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

    # find result from cdr_common collection
    final_result = mongodb.cdr_common.find(query_var).sort([('start_uepoch', -1)]).limit(10)

    # Collect analytics
    logging.debug('Aggregate cdr mail report')
    pipeline = pipeline_mail_report(query_var)

    logging.debug('Before Aggregate')
    list_data = mongodb.DBCON.command('aggregate',
                                      settings.MONGO_CDRSTATS['CDR_COMMON'],
                                      pipeline=pipeline)
    logging.debug('After Aggregate')

    # inintalize variables
    total_duration = 0
    total_calls = 0
    total_buy_cost = 0.0
    total_sell_cost = 0.0
    country_analytic = dict()
    hangup_analytic = dict()
    if list_data:
        for doc in list_data['result']:
            # make total of duration, call count, buy/sell cost
            total_duration += doc['duration_sum']
            total_calls += int(doc['call_count'])
            total_buy_cost += float(doc['buy_cost'])
            total_sell_cost += float(doc['sell_cost'])

            # created hangup_analytic
            hangup_cause_id = int(doc['_id']['hangup_cause_id'])
            if hangup_cause_id in hangup_analytic:
                hangup_analytic[hangup_cause_id] += 1
            else:
                hangup_analytic[hangup_cause_id] = 1

            # created country_analytic
            country_id = int(doc['_id']['country_id'])
            if country_id in country_analytic:
                country_analytic[country_id]['call_count'] +=\
                    int(doc['call_count'])
                country_analytic[country_id]['duration_sum'] +=\
                    doc['duration_sum']
                country_analytic[country_id]['buy_cost'] +=\
                    float(doc['buy_cost'])
                country_analytic[country_id]['sell_cost'] +=\
                    float(doc['sell_cost'])
            else:
                country_analytic[country_id] = {
                    'call_count': int(doc['call_count']),
                    'duration_sum': doc['duration_sum'],
                    'buy_cost': float(doc['buy_cost']),
                    'sell_cost': float(doc['sell_cost'])
                }
    #Calculate the Average Time of Call
    act_acd_array = calculate_act_and_acd(total_calls, total_duration)
    ACT = act_acd_array['ACT']
    ACD = act_acd_array['ACD']

    # sorting on country_analytic
    country_analytic = country_analytic.items()
    country_analytic = sorted(country_analytic,
                              key=lambda k: (k[1]['call_count'],
                                             k[1]['duration_sum']),
                              reverse=True)

    # Create Hangup Cause analytic in percentage format
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
        'total_buy_cost': total_buy_cost,
        'total_sell_cost': total_sell_cost,
        'ACT': ACT,
        'ACD': ACD,
        'country_analytic_array': country_analytic[0:5],
        'hangup_analytic_array': hangup_analytic_array,
    }
    return mail_data


@permission_required('user_profile.mail_report', login_url='/')
@check_cdr_exists
@check_user_accountcode
@check_user_voipplan
@login_required
def mail_report(request):
    """Mail Report Template

    **Attributes**:

        * ``template`` - frontend/cdr_mail_report.html
        * ``form`` - MailreportForm
        * ``mongodb_data_set`` - mongodb.cdr_common

    **Logic Description**:

        get top 10 calls from mongodb collection & hnagupcause/country analytic
        to generate mail report
    """
    logging.debug('CDR mail report view start')
    msg = ''
    user_profile = request.user.get_profile()

    form = EmailReportForm(request.user, request.POST or None, instance=user_profile)
    if form.is_valid():
        form.save()
        msg = _('email ids are saved successfully.')

    mail_data = get_cdr_mail_report()
    logging.debug('CDR mail report view end')
    data = {
        'module': current_view(request),
        'yesterday_date': mail_data['yesterday_date'],
        'rows': mail_data['rows'],
        'form': form,
        'total_duration': mail_data['total_duration'],
        'total_calls': mail_data['total_calls'],
        'total_buy_cost': mail_data['total_buy_cost'],
        'total_sell_cost': mail_data['total_sell_cost'],
        'ACT': mail_data['ACT'],
        'ACD': mail_data['ACD'],
        'country_analytic_array': mail_data['country_analytic_array'],
        'hangup_analytic_array': mail_data['hangup_analytic_array'],
        'msg': msg,
    }
    return render_to_response('cdr/mail_report.html', data, context_instance=RequestContext(request))


def get_hourly_report_for_date(start_date, end_date, query_var):
    """Get Hourly report for date"""
    logging.debug('Aggregate cdr hourly report')
    pipeline = pipeline_hourly_report(query_var)
    logging.debug('Before Aggregate')
    list_data = mongodb.DBCON.command('aggregate',
                                      settings.MONGO_CDRSTATS['DAILY_ANALYTIC'],
                                      pipeline=pipeline)

    call_total_record = {}
    min_total_record = {}
    if list_data:
        for doc in list_data['result']:
            called_time = datetime(int(doc['_id'][0:4]),
                                   int(doc['_id'][4:6]),
                                   int(doc['_id'][6:8]))
            # assign 0 to 23 as key hours to day_hours with initial value 0
            call_day_hours = {}
            min_day_hours = {}
            for hr in range(0, 24):
                call_day_hours[hr] = 0
                min_day_hours[hr] = 0

            # Calls per hour
            for dict_in_list in doc['call_per_hour']:
                # update day_hours via key
                for key, value in dict_in_list.iteritems():
                    call_day_hours[int(key)] += int(value)

            call_total_record[str(called_time)[:10]] = \
                [value for key, value in call_day_hours.iteritems()]

            # Min per hour
            for dict_in_list in doc['duration_per_hour']:
                # update day_hours via key
                for key, value in dict_in_list.iteritems():
                    min_day_hours[int(key)] += float(value) / 60

            min_total_record[str(called_time)[:10]] = \
                [get_rounded_value(value) for key, value in min_day_hours.iteritems()]

    logging.debug('After Aggregate')

    variables = {
        'call_total_record': call_total_record,
        'min_total_record': min_total_record,
    }
    return variables


@permission_required('user_profile.daily_comparison', login_url='/')
@check_cdr_exists
@check_user_accountcode
@login_required
def cdr_daily_comparison(request):
    """CDR graph by hourly basis

    **Attributes**:

        * ``template`` - frontend/cdr_report_by_hour.html
        * ``form`` - CompareCallSearchForm
        * ``mongodb_data_set`` - MONGO_CDRSTATS['DAILY_ANALYTIC']
        * ``map_reduce`` - mapreduce_cdr_hourly_analytic()

    **Logic Description**:

        get all call records from mongodb collection for
        hourly analytics for given date
    """
    logging.debug('CDR hourly view start')
    query_var = {}
    #default
    min_charttype = call_charttype = "lineChart"
    min_chartdata = call_chartdata = {'x': []}
    comp_days = 2
    check_days = 1
    search_tag = 0
    action = 'tabs-1'
    tday = datetime.today()
    from_date = tday.strftime('%Y-%m-%d')
    form = CompareCallSearchForm(request.POST or None,
                                 initial={'from_date': from_date,
                                          'comp_days': comp_days,
                                          'check_days': check_days,
                                          'switch_id': 0})

    logging.debug('CDR hourly view with search option')
    if form.is_valid():
        search_tag = 1
        if "from_date" in request.POST:
            from_date = request.POST['from_date']
            select_date = datetime(int(from_date[0:4]),
                                   int(from_date[5:7]),
                                   int(from_date[8:10]), 0, 0, 0, 0)
        else:
            from_date = tday.strftime('%Y-%m-%d')
            select_date = tday

        comp_days = int(variable_value(request, 'comp_days'))
        check_days = int(variable_value(request, 'check_days'))
        # check previous days
        if check_days == 2:
            compare_date_list = []
            compare_date_list.append(select_date)

            for i in range(1, int(comp_days) + 1):
                #select_date+relativedelta(weeks=-i)
                interval_date = select_date + relativedelta(weeks=-i)
                compare_date_list.append(interval_date)

        switch_id = form.cleaned_data.get('switch_id')
        if switch_id and int(switch_id) != 0:
            query_var['metadata.switch_id'] = int(switch_id)

        if from_date != '':
            end_date = from_date = select_date
            start_date = end_date + relativedelta(days=-int(comp_days))
            start_date = datetime(start_date.year, start_date.month,
                                  start_date.day, 0, 0, 0, 0)
            end_date = datetime(end_date.year, end_date.month,
                                end_date.day, 23, 59, 59, 999999)
            if check_days == 1:
                query_var['metadata.date'] = {
                    '$gte': start_date,
                    '$lt': end_date
                }

    if len(query_var) == 0:
        from_date = datetime.today()
        from_day = validate_days(from_date.year, from_date.month, from_date.day)
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
        query_var['metadata.accountcode'] = request.user.get_profile().accountcode

    if query_var:
        # Previous days
        if check_days == 2:
            for i in compare_date_list:
                s_date = datetime(i.year, i.month, i.day, 0, 0, 0, 0)
                e_date = datetime(i.year, i.month, i.day, 23, 59, 59, 999999)
                query_var['metadata.date'] = {'$gte': s_date, '$lt': e_date}

                call_min_data = get_hourly_report_for_date(s_date, e_date, query_var)
                call_per_hr_data = call_min_data['call_total_record']
                min_per_hr_data = call_min_data['min_total_record']

        # Same day of the week
        if check_days == 1:
            call_min_data = get_hourly_report_for_date(start_date, end_date, query_var)
            call_per_hr_data = call_min_data['call_total_record']
            min_per_hr_data = call_min_data['min_total_record']

        xdata = [i for i in range(0, 24)]
        extra_serie = {"tooltip": {"y_start": "There are ", "y_end": " calls"}}
        call_chartdata = {
            'x': xdata,
        }
        y_count = 1
        for i in call_per_hr_data:
            call_chartdata['name' + str(y_count)] = i
            call_chartdata['y' + str(y_count)] = call_per_hr_data[i]
            call_chartdata['extra' + str(y_count)] = extra_serie
            y_count += 1

        extra_serie = {"tooltip": {"y_start": "There are ", "y_end": " mins"}}
        min_chartdata = {
            'x': xdata,
        }
        y_count = 1
        for i in min_per_hr_data:
            min_chartdata['name' + str(y_count)] = i
            min_chartdata['y' + str(y_count)] = min_per_hr_data[i]
            min_chartdata['extra' + str(y_count)] = extra_serie
            y_count += 1

        logging.debug('CDR hourly view end')

        variables = {
            'action': action,
            'module': current_view(request),
            'form': form,
            'search_tag': search_tag,
            'from_date': from_date,
            'comp_days': comp_days,
            'call_charttype': call_charttype,
            'call_chartdata': call_chartdata,
            'call_chartcontainer': 'call_chartcontainer',
            'call_extra': {
                'x_is_date': False,
                'x_axis_format': 'AM_PM',
                'tag_script_js': True,
                'jquery_on_ready': True,
            },
            'min_charttype': min_charttype,
            'min_chartdata': min_chartdata,
            'min_chartcontainer': 'min_chartcontainer',
            'min_extra': {
                'x_is_date': False,
                'x_axis_format': 'AM_PM',
                'tag_script_js': False,
                'jquery_on_ready': True,
            },
        }
        return render_to_response('cdr/report_by_hour.html', variables, context_instance=RequestContext(request))


@check_cdr_exists
@check_user_accountcode
@login_required
def cdr_overview(request):
    """CDR graph by hourly/daily/monthly basis

    **Attributes**:

        * ``template`` - frontend/cdr_overview.html.html
        * ``form`` - CdrOverviewForm
        * ``mongodb_data_set`` - MONGO_CDRSTATS['DAILY_ANALYTIC']

    **Logic Description**:

        get all call records from mongodb collection for
        all monthly, daily, hourly analytics
    """
    logging.debug('CDR overview start')
    # initialize variables
    query_var = {}
    tday = datetime.today()
    search_tag = 0

    hourly_duration_charttype = hourly_call_charttype = "lineWithFocusChart"
    daily_duration_charttype = daily_call_charttype = "lineWithFocusChart"
    monthly_duration_charttype = monthly_call_charttype = "lineWithFocusChart"
    hourly_call_chartdata = {'x': []}
    hourly_duration_chartdata = {'x': []}
    daily_call_chartdata = {'x': []}
    daily_duration_chartdata = {'x': []}
    monthly_call_chartdata = {'x': []}
    monthly_duration_chartdata = {'x': []}

    action = 'tabs-1'
    form = CdrOverviewForm(request.POST or None)
    logging.debug('CDR overview with search option')
    if form.is_valid():
        search_tag = 1
        if "from_date" in request.POST:
            from_date = request.POST['from_date']
            start_date = ceil_strdate(from_date, 'start')
            start_hour_date = ceil_strdate(from_date, 'start', hour_min=True)
        else:
            from_date = tday.strftime('%Y-%m-%d %H:%M')

        if "to_date" in request.POST:
            to_date = request.POST['to_date']
            end_date = ceil_strdate(to_date, 'end')
            end_hour_date = ceil_strdate(to_date, 'end', hour_min=True)
        else:
            to_date = tday.strftime('%Y-%m-%d 23:55')

        switch_id = form.cleaned_data.get('switch_id')
        if switch_id and int(switch_id) != 0:
            query_var['metadata.switch_id'] = int(switch_id)

        if from_date and to_date:
            query_var['metadata.date'] = {
                '$gte': start_date,
                '$lt': end_date
            }

            month_start_date = datetime(start_date.year, start_date.month, 1, 0, 0, 0, 0)
            month_end_date = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, 999999)

    if len(query_var) == 0:
        tday = datetime.today()
        switch_id = 0
        # assign initial value in form fields
        form = CdrOverviewForm(initial={'from_date': tday.strftime('%Y-%m-%d 00:00'),
                                        'to_date': tday.strftime('%Y-%m-%d 23:55'),
                                        'switch_id': switch_id})

        start_date = datetime(tday.year, tday.month, tday.day, 0, 0, 0, 0)
        end_date = datetime(tday.year, tday.month, tday.day, 23, 59, 59, 999999)
        start_hour_date = ceil_strdate(tday.strftime('%Y-%m-%d 00:00'), 'start', hour_min=True)
        end_hour_date = ceil_strdate(tday.strftime('%Y-%m-%d 23:55'), 'end', hour_min=True)
        month_start_date = datetime(start_date.year, start_date.month, 1,
                                    0, 0, 0, 0)
        month_end_date = datetime(end_date.year, end_date.month, end_date.day,
                                  23, 59, 59, 999999)

        query_var['metadata.date'] = {'$gte': start_date, '$lt': end_date}

    if not request.user.is_superuser:  # not superuser
        query_var['metadata.accountcode'] = request.user.get_profile().accountcode

    if query_var:
        logging.debug('Map-reduce cdr overview analytic')

        # Collect Hourly data
        logging.debug('Aggregate cdr hourly overview')
        pipeline = pipeline_hourly_overview(query_var)

        logging.debug('Before Aggregate')
        list_data = mongodb.DBCON.command('aggregate',
                                          settings.MONGO_CDRSTATS['DAILY_ANALYTIC'],
                                          pipeline=pipeline)
        logging.debug('After Aggregate')

        xdata = []
        hourly_call_count_res = dict()
        hourly_call_duration_res = dict()
        if list_data:
            for doc in list_data['result']:
                a_Year = int(doc['_id']['date'][0:4])
                b_Month = int(doc['_id']['date'][4:6])
                c_Day = int(doc['_id']['date'][6:8])
                day_hours = dict()

                for dict_in_list in doc['call_per_hour']:
                    for key, value in dict_in_list.iteritems():
                        key = int(key)
                        # Get date from aggregate result array
                        graph_day = datetime(a_Year, b_Month, c_Day, key)

                        if graph_day >= start_hour_date and graph_day <= end_hour_date:
                            # convert date into timestamp value
                            dt = int(1000 * time.mktime(graph_day.timetuple()))

                            # prepare day_hours dict var with hour key
                            # and values are like call count, duration sum, switch id
                            if key in day_hours:
                                day_hours[key]['calldate__count'] += int(value)
                            else:
                                day_hours[key] = {
                                    'dt': dt,
                                    'calldate__count': int(value),
                                    'duration__sum': 0,
                                    'switch_id': int(doc['_id']['switch_id'])
                                }

                # update day_hours for duration
                for dict_in_list in doc['duration_per_hour']:
                    for key, value in dict_in_list.iteritems():
                        key = int(key)
                        # Get date from aggregate result array
                        graph_day = datetime(a_Year, b_Month, c_Day, key)
                        if graph_day >= start_hour_date and graph_day <= end_hour_date:
                            day_hours[int(key)]['duration__sum'] += int(value)

                for hr in day_hours:
                    # All switches hourly data
                    temp_dt = day_hours[hr]['dt']
                    temp_call_count = int(day_hours[hr]['calldate__count'])
                    temp_duration_sum = day_hours[hr]['duration__sum']

                    xdata.append(temp_dt)

                    sw_id = day_hours[hr]['switch_id']
                    if sw_id in hourly_call_count_res:
                        hourly_call_count_res[sw_id].append(temp_call_count)
                    else:
                        hourly_call_count_res[sw_id] = [temp_call_count]

                    if sw_id in hourly_call_duration_res:
                        hourly_call_duration_res[sw_id].append(convert_to_minute(temp_duration_sum))
                    else:
                        hourly_call_duration_res[sw_id] = [convert_to_minute(temp_duration_sum)]

            switch_count = len(hourly_call_duration_res.keys())
            if switch_id == 0 and switch_count > 1:
                # get total of no of switch
                total_call_list = []
                for i in hourly_call_count_res:
                    total_call_list.append(hourly_call_count_res[i])

                total_duration_list = []
                for i in hourly_call_duration_res:
                    total_duration_list.append(hourly_call_duration_res[i])

                total_hourly_call_count = [sum(x) for x in itertools.izip_longest(*total_call_list, fillvalue=0)]
                total_hourly_call_duration = [sum(x) for x in itertools.izip_longest(*total_duration_list, fillvalue=0)]

            # get unique data for x-axis
            xdata = list(set([i for i in xdata]))
            xdata = sorted(xdata)
            hourly_call_chartdata = {
                'x': xdata,
            }
            hourly_duration_chartdata = {
                'x': xdata,
            }

            int_count = 1
            extra_serie = {"tooltip": {"y_start": "", "y_end": " calls"},
                           "date_format": "%d %b %y %H:%M%p"}
            for i in hourly_call_count_res:
                hourly_call_chartdata['name' + str(int_count)] = str(get_switch_ip_addr(i))
                hourly_call_chartdata['y' + str(int_count)] = hourly_call_count_res[i]
                hourly_call_chartdata['extra' + str(int_count)] = extra_serie
                int_count += 1

            if switch_id == 0 and switch_count > 1:
                hourly_call_chartdata['name' + str(int_count)] = 'Total calls'
                hourly_call_chartdata['y' + str(int_count)] = total_hourly_call_count
                hourly_call_chartdata['extra' + str(int_count)] = extra_serie

            int_count = 1
            extra_serie = {"tooltip": {"y_start": "", "y_end": " mins"},
                           "date_format": "%d %b %y %H:%M%p"}
            for i in hourly_call_duration_res:
                hourly_duration_chartdata['name' + str(int_count)] = str(get_switch_ip_addr(i))
                hourly_duration_chartdata['y' + str(int_count)] = hourly_call_duration_res[i]
                hourly_duration_chartdata['extra' + str(int_count)] = extra_serie
                int_count += 1

            if switch_id == 0 and switch_count > 1:
                hourly_duration_chartdata['name' + str(int_count)] = 'Total duration'
                hourly_duration_chartdata['y' + str(int_count)] = total_hourly_call_duration
                hourly_duration_chartdata['extra' + str(int_count)] = extra_serie

        # Collect daily data
        logging.debug('Aggregate cdr daily analytic')
        pipeline = pipeline_daily_overview(query_var)

        logging.debug('Before Aggregate')
        list_data = mongodb.DBCON.command('aggregate',
                                          settings.MONGO_CDRSTATS['DAILY_ANALYTIC'],
                                          pipeline=pipeline)
        logging.debug('After Aggregate')

        xdata = []
        daily_call_count_res = dict()
        daily_call_duration_res = dict()
        if list_data:
            for doc in list_data['result']:
                # Get date from aggregate result array
                graph_day = datetime(int(doc['_id']['date'][0:4]),
                                     int(doc['_id']['date'][4:6]),
                                     int(doc['_id']['date'][6:8]),
                                     0, 0, 0, 0)
                # convert date into timestamp value
                dt = int(1000 * time.mktime(graph_day.timetuple()))

                xdata.append(dt)
                sw_id = doc['_id']['switch_id']
                if sw_id in daily_call_count_res:
                    daily_call_count_res[sw_id].append(int(doc['call_per_day']))
                else:
                    daily_call_count_res[sw_id] = [int(doc['call_per_day'])]

                if sw_id in daily_call_duration_res:
                    daily_call_duration_res[sw_id].append(convert_to_minute(doc['duration_per_day']))
                else:
                    daily_call_duration_res[sw_id] = [convert_to_minute(doc['duration_per_day'])]

            if switch_id == 0 and switch_count > 1:
                daily_total_call_list = []
                for i in daily_call_count_res:
                    daily_total_call_list.append(daily_call_count_res[i])

                daily_total_duration_list = []
                for i in daily_call_duration_res:
                    daily_total_duration_list.append(daily_call_duration_res[i])

                total_daily_call_count = [sum(x) for x in itertools.izip_longest(*daily_total_call_list, fillvalue=0)]
                total_daily_call_duration = [sum(x) for x in itertools.izip_longest(*daily_total_duration_list, fillvalue=0)]

            xdata = list(set([i for i in xdata]))
            xdata = sorted(xdata)
            daily_call_chartdata = {
                'x': xdata,
            }
            daily_duration_chartdata = {
                'x': xdata,
            }

            int_count = 1
            extra_serie = {"tooltip": {"y_start": "", "y_end": " calls"},
                           "date_format": "%d %b %Y"}
            for i in daily_call_count_res:
                daily_call_chartdata['name' + str(int_count)] = str(get_switch_ip_addr(i))
                daily_call_chartdata['y' + str(int_count)] = daily_call_count_res[i]
                daily_call_chartdata['extra' + str(int_count)] = extra_serie
                int_count += 1

            if switch_id == 0 and switch_count > 1:
                daily_call_chartdata['name' + str(int_count)] = 'Total calls'
                daily_call_chartdata['y' + str(int_count)] = total_daily_call_count
                daily_call_chartdata['extra' + str(int_count)] = extra_serie

            int_count = 1
            extra_serie = {"tooltip": {"y_start": "", "y_end": " mins"},
                           "date_format": "%d %b %Y"}
            for i in daily_call_duration_res:
                daily_duration_chartdata['name' + str(int_count)] = str(get_switch_ip_addr(i))
                daily_duration_chartdata['y' + str(int_count)] = daily_call_duration_res[i]
                daily_duration_chartdata['extra' + str(int_count)] = extra_serie
                int_count += 1

            if switch_id == 0 and switch_count > 1:
                daily_duration_chartdata['name' + str(int_count)] = 'Total duration'
                daily_duration_chartdata['y' + str(int_count)] = total_daily_call_duration
                daily_duration_chartdata['extra' + str(int_count)] = extra_serie

        # Collect monthly data
        logging.debug('Aggregate cdr monthly analytic')
        query_var['metadata.date'] = {
            '$gte': month_start_date,
            '$lt': month_end_date
        }
        pipeline = pipeline_monthly_overview(query_var)

        logging.debug('Before Aggregate')
        list_data = mongodb.DBCON.command('aggregate',
                                          settings.MONGO_CDRSTATS['MONTHLY_ANALYTIC'],
                                          pipeline=pipeline)
        logging.debug('After Aggregate')

        xdata = []
        monthly_call_count_res = dict()
        monthly_call_duration_res = dict()
        if list_data:
            for doc in list_data['result']:
                # Get date from aggregate result array
                graph_month = datetime(int(doc['_id']['date'][0:4]),
                                       int(doc['_id']['date'][4:6]),
                                       1, 0, 0, 0, 0)
                # convert date into timestamp value
                dt = int(1000 * time.mktime(graph_month.timetuple()))

                xdata.append(dt)
                sw_id = doc['_id']['switch_id']
                if sw_id in monthly_call_count_res:
                    monthly_call_count_res[sw_id].append(int(doc['call_per_month']))
                else:
                    monthly_call_count_res[sw_id] = [int(doc['call_per_month'])]

                if sw_id in monthly_call_duration_res:
                    monthly_call_duration_res[sw_id].append(convert_to_minute(doc['duration_per_month']))
                else:
                    monthly_call_duration_res[sw_id] = [convert_to_minute(doc['duration_per_month'])]

            if switch_id == 0 and switch_count > 1:
                monthly_total_call_list = []
                for i in monthly_call_count_res:
                    monthly_total_call_list.append(monthly_call_count_res[i])

                monthly_total_duration_list = []
                for i in monthly_call_duration_res:
                    monthly_total_duration_list.append(monthly_call_duration_res[i])

                total_monthly_call_count = [sum(x) for x in itertools.izip_longest(*monthly_total_call_list, fillvalue=0)]
                total_monthly_call_duration = [sum(x) for x in itertools.izip_longest(*monthly_total_duration_list, fillvalue=0)]

            xdata = list(set([i for i in xdata]))
            xdata = sorted(xdata)
            monthly_call_chartdata = {
                'x': xdata,
            }
            monthly_duration_chartdata = {
                'x': xdata,
            }

            int_count = 1
            extra_serie = {"tooltip": {"y_start": "", "y_end": " calls"},
                           "date_format": "%b %Y"}
            for i in monthly_call_count_res:
                monthly_call_chartdata['name' + str(int_count)] = str(get_switch_ip_addr(i))
                monthly_call_chartdata['y' + str(int_count)] = monthly_call_count_res[i]
                monthly_call_chartdata['extra' + str(int_count)] = extra_serie
                int_count += 1

            if switch_id == 0 and switch_count > 1:
                monthly_call_chartdata['name' + str(int_count)] = 'Total calls'
                monthly_call_chartdata['y' + str(int_count)] = total_monthly_call_count
                monthly_call_chartdata['extra' + str(int_count)] = extra_serie

            int_count = 1
            extra_serie = {"tooltip": {"y_start": "", "y_end": " mins"},
                           "date_format": "%b %Y"}
            for i in monthly_call_duration_res:
                monthly_duration_chartdata['name' + str(int_count)] = str(get_switch_ip_addr(i))
                monthly_duration_chartdata['y' + str(int_count)] = monthly_call_duration_res[i]
                monthly_duration_chartdata['extra' + str(int_count)] = extra_serie
                int_count += 1

            if switch_id == 0 and switch_count > 1:
                monthly_duration_chartdata['name' + str(int_count)] = 'Total duration'
                monthly_duration_chartdata['y' + str(int_count)] = total_monthly_call_duration
                monthly_duration_chartdata['extra' + str(int_count)] = extra_serie

        logging.debug('CDR daily view end')
        variables = {
            'action': action,
            'module': current_view(request),
            'form': form,
            'search_tag': search_tag,
            'start_date': start_date,
            'end_date': end_date,
            'hourly_call_chartdata': hourly_call_chartdata,
            'hourly_call_charttype': hourly_call_charttype,
            'hourly_call_chartcontainer': 'hourly_call_container',
            'hourly_call_extra': {
                'x_is_date': True,
                'x_axis_format': '%d %b %y %H%p',
                'tag_script_js': True,
                'jquery_on_ready': False,
            },
            'hourly_duration_chartdata': hourly_duration_chartdata,
            'hourly_duration_charttype': hourly_duration_charttype,
            'hourly_duration_chartcontainer': 'hourly_duration_container',
            'hourly_duration_extra': {
                'x_is_date': True,
                'x_axis_format': '%d %b %y %H %p',
                'tag_script_js': False,
                'jquery_on_ready': False,
            },
            'daily_call_chartdata': daily_call_chartdata,
            'daily_call_charttype': daily_call_charttype,
            'daily_call_chartcontainer': 'daily_call_container',
            'daily_call_extra': {
                'x_is_date': True,
                'x_axis_format': '%d %b %Y',
                'tag_script_js': False,
                'jquery_on_ready': False,
            },
            'daily_duration_chartdata': daily_duration_chartdata,
            'daily_duration_charttype': daily_duration_charttype,
            'daily_duration_chartcontainer': 'daily_duration_container',
            'daily_duration_extra': {
                'x_is_date': True,
                'x_axis_format': '%d %b %Y',
                'tag_script_js': False,
                'jquery_on_ready': False,
            },
            'monthly_call_chartdata': monthly_call_chartdata,
            'monthly_call_charttype': monthly_call_charttype,
            'monthly_call_chartcontainer': 'monthly_call_container',
            'monthly_call_extra': {
                'x_is_date': True,
                'x_axis_format': '%b %Y',
                'tag_script_js': False,
                'jquery_on_ready': False,
            },
            'monthly_duration_chartdata': monthly_duration_chartdata,
            'monthly_duration_charttype': monthly_duration_charttype,
            'monthly_duration_chartcontainer': 'monthly_duration_container',
            'monthly_duration_extra': {
                'x_is_date': True,
                'x_axis_format': '%b %Y',
                'tag_script_js': False,
                'jquery_on_ready': False,
            },
        }
        return render_to_response('cdr/overview.html', variables, context_instance=RequestContext(request))


@permission_required('user_profile.by_country', login_url='/')
@check_cdr_exists
@check_user_accountcode
@login_required
def cdr_country_report(request):
    """CDR country report

    **Attributes**:

        * ``template`` - frontend/cdr_country_report.html
        * ``form`` - CountryReportForm
        * ``mongodb_data_set`` - MONGO_CDRSTATS['DAILY_ANALYTIC']

    **Logic Description**:

        get all call records from mongodb collection for all countries
        to create country call
    """
    logging.debug('CDR country report view start')
    switch_id = 0
    query_var = {}
    search_tag = 0
    now = datetime.now()
    start_date = datetime(now.year, now.month, now.day, 0, 0, 0, 0)
    end_date = datetime(now.year, now.month, now.day, 23, 59, 59, 999999)
    from_date = start_date.strftime("%Y-%m-%d")
    to_date = end_date.strftime("%Y-%m-%d")
    # assign initial value in form fields
    total_calls = 0
    total_duration = 0
    form = CountryReportForm(request.POST or None, initial={'from_date': from_date,
                                                            'to_date': to_date})
    if form.is_valid():
        logging.debug('CDR country report view with search option')
        search_tag = 1
        if "from_date" in request.POST:
            # From
            start_date = from_date = form.cleaned_data.get('from_date')

        if "to_date" in request.POST:
            # To
            end_date = to_date = form.cleaned_data.get('to_date')

        country_id = form.cleaned_data.get('country_id')
        # convert list value in int
        country_id = [int(row) for row in country_id]
        if len(country_id) >= 1 and country_id[0] != 0:
            query_var['metadata.country_id'] = {'$in': country_id}

        switch_id = int(form.cleaned_data.get('switch_id'))
        if switch_id and switch_id != 0:
            query_var['metadata.switch_id'] = switch_id

        duration = form.cleaned_data.get('duration')
        duration_type = form.cleaned_data.get('duration_type')
        if duration:
            due = mongodb_int_filter(duration, duration_type)
            temp = []
            if due:
                for i in range(0, 24):
                    temp.append({'duration_hourly.%d' % (i): due})
                query_var['$or'] = temp

    query_var['metadata.date'] = {'$gte': start_date, '$lt': end_date}

    if not request.user.is_superuser:  # not superuser
        query_var['metadata.accountcode'] = request.user.get_profile().accountcode

    # Country daily data
    pipeline = pipeline_country_hourly_report(query_var)

    logging.debug('Before Aggregate')
    list_data = mongodb.DBCON.command('aggregate',
                                      settings.MONGO_CDRSTATS['DAILY_ANALYTIC'],
                                      pipeline=pipeline)
    xdata = []
    call_count_res = defaultdict(list)
    call_duration_res = defaultdict(list)

    if list_data:
        for doc in list_data['result']:
            # Get date from aggregate result array
            a_Year = int(doc['_id']['date'][0:4])
            b_Month = int(doc['_id']['date'][5:7])
            c_Day = int(doc['_id']['date'][8:10])

            day_hours = dict()

            for dict_in_list in doc['call_per_hour']:
                for key, value in dict_in_list.iteritems():
                    key = int(key)
                    graph_day = datetime(a_Year, b_Month, c_Day, key)
                    # convert date into timestamp value
                    dt = int(1000 * time.mktime(graph_day.timetuple()))

                    #Create day_hours dict with call count, duration sum, country id
                    if key in day_hours:
                        day_hours[key]['calldate__count'] += int(value)
                    else:
                        xdata.append(dt)
                        day_hours[key] = {
                            'dt': dt,
                            'calldate__count': int(value),
                            'duration__sum': 0,
                            'country_id': doc['_id']['country_id']
                        }

            #Update day_hours dict for duration sum
            for dict_in_list in doc['duration_per_hour']:
                for key, value in dict_in_list.iteritems():
                    key = int(key)
                    if key in day_hours:
                        day_hours[key]['duration__sum'] += int(value)

            # hours of day data append to total_record_final array
            for hr in day_hours:
                call_count_res[day_hours[hr]['country_id']].append(day_hours[hr]['calldate__count'])
                call_duration_res[day_hours[hr]['country_id']].append(day_hours[hr]['duration__sum'])

        xdata = list(set([i for i in xdata]))
        xdata = sorted(xdata)
        final_call_chartdata = {
            'x': xdata,
        }
        final_duration_chartdata = {
            'x': xdata,
        }
        int_count = 1
        extra_serie = {"tooltip": {"y_start": "", "y_end": " calls"}}
        for i in call_count_res:
            final_call_chartdata['name' + str(int_count)] = str(get_country_name(int(i)))
            final_call_chartdata['y' + str(int_count)] = call_count_res[i]
            final_call_chartdata['extra' + str(int_count)] = extra_serie
            int_count += 1

        int_count = 1
        extra_serie = {"tooltip": {"y_start": "", "y_end": " mins"}}
        for i in call_duration_res:
            final_duration_chartdata['name' + str(int_count)] = str(get_country_name(int(i)))
            final_duration_chartdata['y' + str(int_count)] = call_duration_res[i]
            final_duration_chartdata['extra' + str(int_count)] = extra_serie
            int_count += 1

        final_call_charttype = final_duration_charttype = "lineWithFocusChart"

    # World report
    logging.debug('Aggregate world report')
    pipeline = pipeline_country_report(query_var)

    logging.debug('Before Aggregate')
    list_data = mongodb.DBCON.command('aggregate',
                                      settings.MONGO_CDRSTATS['DAILY_ANALYTIC'],
                                      pipeline=pipeline)
    logging.debug('After Aggregate')
    country_analytic_array = []
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

        # country analytic pie chart data
        xdata = []
        ydata = []
        ydata2 = []
        for i in country_analytic_array:
            xdata.append(str(i[0]))
            #call_per_day - i[1]
            ydata.append(percentage(i[1], total_calls))
            #duration_per_day - i[2]
            ydata2.append(percentage(i[2], total_duration))

        extra_serie = {"tooltip": {"y_start": "", "y_end": " %"}}
        country_call_chartdata = {'x': xdata, 'y1': ydata, 'extra1': extra_serie}
        country_duration_chartdata = {'x': xdata, 'y1': ydata2, 'extra1': extra_serie}
        country_call_charttype = "pieChart"

    logging.debug('CDR country report view end')
    data = {
        'action': 'tabs-1',
        'module': current_view(request),
        'total_calls': total_calls,
        'total_duration': total_duration,
        'country_analytic': country_analytic_array,
        'form': form,
        'search_tag': search_tag,
        'NUM_COUNTRY': settings.NUM_COUNTRY,
        'country_call_charttype': country_call_charttype,
        'country_call_chartdata': country_call_chartdata,
        'country_call_chartcontainer': 'country_call_container',
        'country_call_extra': {
            'x_is_date': False,
            'x_axis_format': '',
            'tag_script_js': True,
            'jquery_on_ready': False,
        },
        'country_duration_chartdata': country_duration_chartdata,
        'country_duration_chartcontainer': 'country_duration_container',
        'country_duration_extra': {
            'x_is_date': False,
            'x_axis_format': '',
            'tag_script_js': True,
            'jquery_on_ready': False,
        },
        'final_call_chartdata': final_call_chartdata,
        'final_call_charttype': final_call_charttype,
        'final_call_chartcontainer': 'final_call_container',
        'final_call_extra': {
            'x_is_date': True,
            'x_axis_format': '%d %b %Y',
            'tag_script_js': True,
            'jquery_on_ready': False,
        },
        'final_duration_chartdata': final_duration_chartdata,
        'final_duration_charttype': final_duration_charttype,
        'final_duration_chartcontainer': 'final_duration_container',
        'final_duration_extra': {
            'x_is_date': True,
            'x_axis_format': '%d %b %Y',
            'tag_script_js': False,
            'jquery_on_ready': False,
        },
    }
    return render_to_response('cdr/country_report.html', data, context_instance=RequestContext(request))


@permission_required('user_profile.world_map', login_url='/')
@check_cdr_exists
@check_user_accountcode
@check_user_voipplan
@login_required
def world_map_view(request):
    """CDR world report

    **Attributes**:

        * ``template`` - frontend/world_map.html
        * ``form`` - WorldForm
        * ``mongodb_data_set`` - MONGO_CDRSTATS['DAILY_ANALYTIC']

    **Logic Description**:

        get all call records from mongodb collection for all countries
        to create country call
    """
    logging.debug('CDR world report view start')
    action = 'tabs-1'
    switch_id = 0
    query_var = {}
    search_tag = 0
    now = datetime.now()
    start_date = datetime(now.year, now.month, now.day, 0, 0, 0, 0)
    end_date = datetime(now.year, now.month, now.day, 23, 59, 59, 999999)
    from_date = start_date.strftime("%Y-%m-%d")
    to_date = end_date.strftime("%Y-%m-%d")
    # assign initial value in form fields
    form = WorldForm(request.POST or None, initial={'from_date': from_date, 'to_date': to_date})

    if form.is_valid():
        logging.debug('CDR world report view with search option')
        search_tag = 1
        if "from_date" in request.POST:
            # From
            from_date = form.cleaned_data.get('from_date')
            start_date = ceil_strdate(from_date, 'start')

        if "to_date" in request.POST:
            # To
            to_date = form.cleaned_data.get('to_date')
            end_date = ceil_strdate(to_date, 'end')

        switch_id = form.cleaned_data.get('switch_id')
        if switch_id and int(switch_id) != 0:
            query_var['metadata.switch_id'] = int(switch_id)

    query_var['metadata.date'] = {'$gte': start_date, '$lt': end_date}

    if not request.user.is_superuser:  # not superuser
        query_var['metadata.accountcode'] = request.user.get_profile().accountcode

    logging.debug('Aggregate world report')
    pipeline = pipeline_country_report(query_var)

    logging.debug('Before Aggregate')
    list_data = mongodb.DBCON.command('aggregate',
                                      settings.MONGO_CDRSTATS['DAILY_ANALYTIC'],
                                      pipeline=pipeline)
    logging.debug('After Aggregate')
    world_analytic_array = []
    if list_data:
        for doc in list_data['result']:
            # append data to world_analytic_array with following order
            # country id|country name|call count|call duration|country_id|buy cost|sell cost
            # _id = country id
            world_analytic_array.append((int(doc['_id']),
                                         get_country_name(int(doc['_id']), type='iso2'),
                                         int(doc['call_per_day']),
                                         doc['duration_per_day'],
                                         get_country_name(int(doc['_id'])),
                                         doc['buy_cost_per_day'],
                                         doc['sell_cost_per_day'],
                                         ))

    logging.debug('CDR world report view end')

    variables = {
        'module': current_view(request),
        'form': form,
        'search_tag': search_tag,
        'start_date': start_date,
        'end_date': end_date,
        'world_analytic_array': world_analytic_array,
        'action': action,
    }
    return render_to_response('cdr/world_map.html', variables, context_instance=RequestContext(request))
