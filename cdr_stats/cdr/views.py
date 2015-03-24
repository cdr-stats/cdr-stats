#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2014 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.utils.translation import gettext as _
from django.conf import settings
import six
from django_lets_go.common_functions import int_convert_to_minute,\
    percentage, getvar, unset_session_var, ceil_strdate
from django_lets_go.common_functions import get_pagination_vars
# from cdr.filters import CDRFilter
from switch.models import Switch
from user_profile.models import UserProfile
from cdr.functions_def import get_country_name, get_hangupcause_name,\
    get_switch_ip_addr, calculate_act_acd
from cdr.forms import CdrSearchForm, CountryReportForm, CdrOverviewForm, CompareCallSearchForm, \
    SwitchForm, WorldForm, EmailReportForm
# from cdr.forms import ConcurrentCallForm
from cdr.filters import get_filter_operator_int, get_filter_operator_str
from cdr.aggregate import pipeline_country_report,\
    pipeline_country_hourly_report,\
    pipeline_mail_report
from cdr.decorators import check_user_detail
from cdr.constants import CDR_COLUMN_NAME, Export_choice, COMPARE_WITH
from cdr.models import CDR
from aggregator.cdr import custom_sql_aggr_top_country, custom_sql_aggr_top_hangup_cause, \
    custom_sql_matv_voip_cdr_aggr_last24hour, \
    custom_sql_aggr_top_country_last24hour
from aggregator.pandas_cdr import get_report_cdr_per_switch, get_report_compare_cdr
from voip_billing.function_def import round_val
from bson.objectid import ObjectId
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import tablib
import time
import logging
# from common.helpers import pp


def show_menu(request):
    """Check if we suppose to show menu"""
    try:
        return request.GET.get('menu')
    except:
        return 'on'


@permission_required('user_profile.search', login_url='/')
@check_user_detail('accountcode,voipplan')
@login_required
def cdr_view(request):
    """List of CDRs

    **Attributes**:

        * ``template`` - cdr/cdr_view.html
        * ``form`` - CdrSearchForm

    **Logic Description**:

        * get the call records as well as daily call analytics
          from postgresql according to search parameters
    """
    logging.debug('CDR View Start')
    result = 1  # default min
    switch_id = 0  # default all
    hangup_cause_id = 0  # default all
    destination, destination_type, accountcode = '', '', ''
    direction, duration, duration_type = '', '', ''
    caller_id_number, caller_id_number_type, country_id = '', '', ''
    action = 'tabs-1'
    menu = 'on'
    cdr_view_daily_data = {}
    records_per_page = settings.PAGE_SIZE

    form = CdrSearchForm(request.POST or None)
    if form.is_valid():
        logging.debug('CDR Search View')
        # set session var value
        field_list = ['destination', 'result', 'destination_type', 'accountcode',
                      'caller_id_number', 'caller_id_number_type', 'duration',
                      'duration_type', 'hangup_cause_id', 'switch_id', 'direction',
                      'country_id', 'export_query_var']
        unset_session_var(request, field_list)
        from_date = getvar(request, 'from_date', setsession=False)
        to_date = getvar(request, 'to_date', setsession=False)
        result = getvar(request, 'result', setsession=True)
        destination = getvar(request, 'destination', setsession=True)
        destination_type = getvar(request, 'destination_type', setsession=True)
        accountcode = getvar(request, 'accountcode', setsession=True)
        caller_id_number = getvar(request, 'caller_id_number', setsession=True)
        caller_id_number_type = getvar(request, 'caller_id_number_type', setsession=True)
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

        start_date = ceil_strdate(str(from_date), 'start', True)
        end_date = ceil_strdate(str(to_date), 'end', True)
        converted_start_date = start_date.strftime('%Y-%m-%d %H:%M')
        converted_end_date = end_date.strftime('%Y-%m-%d %H:%M')
        request.session['session_start_date'] = converted_start_date
        request.session['session_end_date'] = converted_end_date

    menu = show_menu(request)

    using_session = False
    # Display a specific page or sort
    if request.GET.get('page') or request.GET.get('sort_by'):
        using_session = True
        from_date = start_date = request.session.get('session_start_date')
        to_date = end_date = request.session.get('session_end_date')
        start_date = ceil_strdate(start_date, 'start', True)
        end_date = ceil_strdate(end_date, 'end', True)

        destination = request.session.get('session_destination')
        destination_type = request.session.get('session_destination_type')
        accountcode = request.session.get('session_accountcode')
        caller_id_number = request.session.get('session_caller_id_number')
        caller_id_number_type = request.session.get('session_caller_id_number_type')
        duration = request.session.get('session_duration')
        duration_type = request.session.get('session_duration_type')
        direction = request.session.get('session_direction')
        switch_id = request.session.get('session_switch_id')
        hangup_cause_id = request.session.get('session_hangup_cause_id')
        result = request.session.get('session_result')
        records_per_page = request.session.get('session_records_per_page')
        country_id = request.session['session_country_id']

    # Set default cause we display page for the first time
    if request.method == 'GET' and not using_session:
        tday = datetime.today()
        from_date = datetime(tday.year, tday.month, 1, 0, 0, 0, 0)
        last_day = ((datetime(tday.year, tday.month, 1, 23, 59, 59, 999999) +
                     relativedelta(months=1)) -
                    relativedelta(days=1)).strftime('%d')
        # to_date = tday.strftime('%Y-%m-' + last_day + ' 23:59')
        to_date = datetime(tday.year, tday.month, int(last_day), 23, 59, 59, 999999)
        start_date = ceil_strdate(str(from_date), 'start', True)
        end_date = ceil_strdate(str(to_date), 'end', True)

        converted_start_date = start_date.strftime('%Y-%m-%d %H:%M')
        converted_end_date = end_date.strftime('%Y-%m-%d %H:%M')
        request.session['session_start_date'] = converted_start_date
        request.session['session_end_date'] = converted_end_date
        request.session['session_result'] = 1
        field_list = [
            'destination', 'destination_type', 'accountcode',
            'caller_id_number', 'caller_id_number_type', 'duration',
            'duration_type', 'hangup_cause_id',
            'switch_id', 'direction', 'country_id']
        unset_session_var(request, field_list)
        request.session['session_records_per_page'] = records_per_page
        request.session['session_country_id'] = ''

    # Define no of records per page
    records_per_page = int(records_per_page)

    sort_col_field_list = ['id', 'caller_id_number', 'destination_number', 'starting_date']
    page_vars = get_pagination_vars(request, sort_col_field_list, default_sort_field='id')

    # kwargs = {'user': request.user}
    kwargs = {}
    if hangup_cause_id and hangup_cause_id != '0':
        kwargs['hangup_cause_id'] = int(hangup_cause_id)

    if switch_id and switch_id != '0':
        kwargs['switch_id'] = int(switch_id)

    if direction and direction != 'all':
        kwargs['direction'] = direction

    if len(country_id) >= 1 and country_id[0] != 0:
        kwargs['country_id__in'] = country_id

    if start_date:
        kwargs['starting_date__gte'] = start_date

    if end_date:
        kwargs['starting_date__lte'] = end_date

    if destination:
        operator_query = get_filter_operator_str('destination_number', destination_type)
        kwargs[operator_query] = destination

    if duration:
        operator_query = get_filter_operator_int('duration', duration_type)
        kwargs[operator_query] = duration

    if caller_id_number:
        operator_query = get_filter_operator_str('caller_id_number', caller_id_number_type)
        kwargs[operator_query] = caller_id_number

    # user are restricted to their own CDRs
    if not request.user.is_superuser:
        kwargs['user_id'] = request.user.id
        # TODO: CDR model also have accountcode, see exactly how it makes sense to use it.
        # we might want on the long term to have several accountcode per users
        #
        # daily_report_query_var['metadata.accountcode'] = request.user.userprofile.accountcode
        # query_var['accountcode'] = daily_report_query_var['metadata.accountcode']

    if request.user.is_superuser and accountcode:
        try:
            user_prof = UserProfile.objects.get(accountcode=accountcode)
            kwargs['user_id'] = user_prof.user.id
        except UserProfile.DoesNotExist:
            # cannot find a user for this accountcode
            pass

    cdrs = CDR.objects.filter(**kwargs).order_by(page_vars['sort_order'])
    page_cdr_list = cdrs[page_vars['start_page']:page_vars['end_page']]
    cdr_count = cdrs.count()

    logging.debug('Create cdr result')

    # store query_var in session without date
    export_kwargs = kwargs.copy()
    if 'starting_date__gte' in export_kwargs:
        export_kwargs['starting_date__gte'] = export_kwargs['starting_date__gte'].strftime('%Y-%m-%dT%H:%M:%S')
    if 'starting_date__lte' in export_kwargs:
        export_kwargs['starting_date__lte'] = export_kwargs['starting_date__lte'].strftime('%Y-%m-%dT%H:%M:%S')

    request.session['session_export_kwargs'] = export_kwargs

    form = CdrSearchForm(
        initial={
            'from_date': from_date,
            'to_date': to_date,
            'destination': destination,
            'destination_type': destination_type,
            'accountcode': accountcode,
            'caller_id_number': caller_id_number,
            'caller_id_number_type': caller_id_number_type,
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

    template_data = {
        'page_cdr_list': page_cdr_list,
        'cdrs': cdrs,
        'form': form,
        'cdr_count': cdr_count,
        'cdr_daily_data': {},
        'col_name_with_order': page_vars['col_name_with_order'],
        'menu': menu,
        'start_date': start_date,
        'end_date': end_date,
        'action': action,
        'result': result,
        'CDR_COLUMN_NAME': CDR_COLUMN_NAME,
        'records_per_page': records_per_page,
        'up_icon': '<i class="glyphicon glyphicon-chevron-up"></i>',
        'down_icon': '<i class="glyphicon glyphicon-chevron-down"></i>'
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
    format_type = request.GET['format']
    # get the response object, this can be used as a stream
    response = HttpResponse(content_type='text/%s' % format_type)
    # force download
    response['Content-Disposition'] = 'attachment;filename=export.%s' % format_type

    # get query_var from request.session
    start_date = request.session.get('session_start_date')
    end_date = request.session.get('session_end_date')
    start_date = ceil_strdate(start_date, 'start', True)
    end_date = ceil_strdate(end_date, 'end', True)

    if request.session.get('session_export_kwargs'):
        kwargs = request.session.get('session_export_kwargs')

    if start_date:
        kwargs['starting_date__gte'] = start_date
    if end_date:
        kwargs['starting_date__lte'] = end_date

    cdrs = CDR.objects.filter(**kwargs)

    headers = ('Call-date', 'CLID', 'Destination', 'Duration', 'Bill sec', 'Hangup cause',
               'AccountCode', 'Direction')

    list_val = []
    for cdr in cdrs:
        starting_date = str(cdr.starting_date)

        list_val.append((
            starting_date,
            cdr.caller_id_number + '-' + cdr.caller_id_name,
            cdr.destination_number,
            cdr.duration,
            cdr.billsec,
            get_hangupcause_name(cdr.hangup_cause_id),
            cdr.accountcode,
            cdr.direction,
        ))

    data = tablib.Dataset(*list_val, headers=headers)
    if format_type == Export_choice.XLS:
        response.write(data.xls)
    elif format_type == Export_choice.CSV:
        response.write(data.csv)
    elif format_type == Export_choice.JSON:
        response.write(data.json)

    return response


@permission_required('user_profile.cdr_detail', login_url='/')
@login_required
def cdr_detail(request, id, switch_id):
    """Detail of Call

    **Attributes**:

        * ``template`` - cdr/cdr_detail.html

    **Logic Description**:

        get the single call record in detail from mongodb collection
    """
    c_switch = get_object_or_404(Switch, id=switch_id)
    ipaddress = c_switch.ipaddress
    menu = show_menu(request)

    db_engine = settings.CDR_BACKEND[ipaddress]['db_engine']
    cdr_type = settings.CDR_BACKEND[ipaddress]['cdr_type']

    if cdr_type == 'freeswitch':
        # Connect on MongoDB Database
        host = settings.CDR_BACKEND[ipaddress]['host']
        port = settings.CDR_BACKEND[ipaddress]['port']
        db_name = settings.CDR_BACKEND[ipaddress]['db_name']
        table_name = settings.CDR_BACKEND[ipaddress]['table_name']
        user = settings.CDR_BACKEND[ipaddress]['user']
        password = settings.CDR_BACKEND[ipaddress]['password']
        try:
            connection = Connection(host, port)
            DBCON = connection[db_name]
            # DBCON.autentificate(user, password)
        except ConnectionFailure:
            raise Http404

        doc = DBCON[table_name].find({'_id': ObjectId(id)})
        data = {'row': list(doc), 'menu': menu}
        return render_to_response('cdr/detail_freeswitch.html', data, context_instance=RequestContext(request))

    elif cdr_type == 'asterisk':
        # Connect on Database
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
            (settings.ASTERISK_PRIMARY_KEY, table_name, settings.ASTERISK_PRIMARY_KEY, id))
        row = cursor.fetchone()
        if not row:
            raise Http404
        data = {'row': list(row), 'menu': menu}
        return render_to_response('cdr/detail_asterisk.html', data, context_instance=RequestContext(request))


@permission_required('user_profile.dashboard', login_url='/')
@check_user_detail('accountcode,voipplan')
@login_required
def cdr_dashboard(request):
    """CDR dashboard on the last 24 hours

    **Attributes**:

        * ``template`` - cdr/dashboard.html
        * ``form`` - SwitchForm

    **Logic Description**:

        Display calls aggregated information for the last 24hours, several report will be
        created and displayed such as hourly call report and hangup cause/country analytics.
    """
    logging.debug('CDR dashboard view start')
    form = SwitchForm(request.POST or None)

    if form.is_valid():
        logging.debug('CDR dashboard view with search option')
        switch_id = int(getvar(request, 'switch_id'))
    else:
        switch_id = 0

    # if not request.user.is_superuser:
        # query_var['metadata.accountcode'] = request.user.userprofile.accountcode

    # Get list of calls/duration for each of the last 24 hours
    (calls_hour_aggr, total_calls, total_duration, total_billsec, total_buy_cost, total_sell_cost) = custom_sql_matv_voip_cdr_aggr_last24hour(request.user, switch_id)
    # pp(calls_hour_aggr)

    # Get top 5 of country calls for last 24 hours
    country_data = custom_sql_aggr_top_country_last24hour(request.user, switch_id, limit=5)

    # Get top 10 of hangup cause calls for last 24 hours
    hangup_cause_data = custom_sql_aggr_top_hangup_cause(request.user, switch_id)

    # Build chart data for last 24h calls
    (xdata, ydata, ydata2, ydata3, ydata4, ydata5) = ([], [], [], [], [], [])
    for i in calls_hour_aggr:
        # start_time = int(time.mktime(datetime.datetime(2012, 6, 1).timetuple()) * 1000)
        start_time = (time.mktime(calls_hour_aggr[i]['calltime'].timetuple()) * 1000)
        xdata.append(start_time)
        ydata.append(str(calls_hour_aggr[i]['nbcalls']))
        ydata2.append(str(calls_hour_aggr[i]['duration']))
        ydata3.append(str(calls_hour_aggr[i]['billsec']))
        ydata4.append(str(calls_hour_aggr[i]['buy_cost']))
        ydata5.append(str(calls_hour_aggr[i]['sell_cost']))

    tooltip_date = "%d %b %y %H:%M %p"
    extra_serie1 = {"tooltip": {"y_start": "", "y_end": " calls"}, "date_format": tooltip_date}
    extra_serie2 = {"tooltip": {"y_start": "", "y_end": " sec"}, "date_format": tooltip_date}
    extra_serie3 = {"tooltip": {"y_start": "", "y_end": " sec"}, "date_format": tooltip_date}
    extra_serie4 = {"tooltip": {"y_start": "", "y_end": ""}, "date_format": tooltip_date}
    extra_serie5 = {"tooltip": {"y_start": "", "y_end": ""}, "date_format": tooltip_date}

    final_chartdata = {
        'x': xdata,
        'name1': 'Calls', 'y1': ydata, 'extra1': extra_serie1,
        'name2': 'Duration', 'y2': ydata2, 'extra2': extra_serie2,
        'name3': 'Billsec', 'y3': ydata3, 'extra3': extra_serie3,
        'name4': 'Buy cost', 'y4': ydata4, 'extra4': extra_serie4,
        'name5': 'Sell cost', 'y5': ydata5, 'extra5': extra_serie5,
    }
    final_charttype = "lineWithFocusChart"

    # Build pie chart data for last 24h calls per country
    (xdata, ydata) = ([], [])
    for country in country_data:
        xdata.append(get_country_name(country["country_id"]))
        ydata.append(percentage(country["nbcalls"], total_calls))

    color_list = ['#FFC36C', '#FFFF9D', '#BEEB9F', '#79BD8F', '#FFB391']
    extra_serie = {"tooltip": {"y_start": "", "y_end": " %"}, "color_list": color_list}
    country_analytic_chartdata = {'x': xdata, 'y1': ydata, 'extra1': extra_serie}
    country_analytic_charttype = "pieChart"

    # hangup analytic pie chart data
    (xdata, ydata) = ([], [])
    for i in hangup_cause_data:
        xdata.append(str(get_hangupcause_name(hangup_cause_data[i]["hangup_cause_id"])))
        ydata.append(str(percentage(hangup_cause_data[i]["nbcalls"], total_calls)))

    color_list = ['#2A343F', '#7E8282', '#EA9664', '#30998F', '#449935']
    extra_serie = {"tooltip": {"y_start": "", "y_end": " %"}, "color_list": color_list}
    hangup_analytic_chartdata = {'x': xdata, 'y1': ydata, 'extra1': extra_serie}
    hangup_analytic_charttype = "pieChart"

    logging.debug("Result calls_hour_aggr %d" % len(calls_hour_aggr))
    logging.debug("Result hangup_cause_data %d" % len(hangup_cause_data))
    logging.debug("Result country_data %d" % len(country_data))

    # Calculate the Average Time of Call
    metric_aggr = calculate_act_acd(total_calls, total_duration)

    country_extra = hangup_extra = {
        'x_is_date': False,
        'x_axis_format': '',
        'tag_script_js': True,
        'jquery_on_ready': True,
    }

    final_extra = {
        'x_is_date': True,
        'x_axis_format': '%H:%M',
        'tag_script_js': True,
        'jquery_on_ready': True,
    }

    logging.debug('CDR dashboard view end')
    variables = {
        'total_calls': total_calls,
        'total_duration': int_convert_to_minute(total_duration),
        'total_buy_cost': total_buy_cost,
        'total_sell_cost': total_sell_cost,
        'metric_aggr': metric_aggr,
        'country_data': country_data,
        'hangup_analytic': hangup_cause_data,
        'form': form,
        'final_chartdata': final_chartdata,
        'final_charttype': final_charttype,
        'final_chartcontainer': 'final_container',
        'final_extra': final_extra,
        'hangup_analytic_charttype': hangup_analytic_charttype,
        'hangup_analytic_chartdata': hangup_analytic_chartdata,
        'hangup_chartcontainer': 'hangup_piechart_container',
        'hangup_extra': hangup_extra,
        'country_analytic_charttype': country_analytic_charttype,
        'country_analytic_chartdata': country_analytic_chartdata,
        'country_chartcontainer': 'country_piechart_container',
        'country_extra': country_extra,
    }
    return render_to_response('cdr/dashboard.html', variables, context_instance=RequestContext(request))


def get_cdr_mail_report():
    """General function to get previous day CDR report"""
    # Get yesterday's CDR-Stats Mail Report
    query_var = {}
    yesterday = date.today() - timedelta(1)
    start_date = datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0, 0)
    end_date = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59, 999999)

    query_var['start_uepoch'] = {'$gte': start_date, '$lt': end_date}

    # find result from cdr_common collection
    mongo_cdr_result = mongodb.cdr_common.find(query_var).sort([('start_uepoch', -1)]).limit(10)

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
                country_analytic[country_id]['call_count'] += int(doc['call_count'])
                country_analytic[country_id]['duration_sum'] += doc['duration_sum']
                country_analytic[country_id]['buy_cost'] += float(doc['buy_cost'])
                country_analytic[country_id]['sell_cost'] += float(doc['sell_cost'])
            else:
                country_analytic[country_id] = {
                    'call_count': int(doc['call_count']),
                    'duration_sum': doc['duration_sum'],
                    'buy_cost': float(doc['buy_cost']),
                    'sell_cost': float(doc['sell_cost'])
                }
    # Calculate the Average Time of Call
    act_acd_array = calculate_act_acd(total_calls, total_duration)
    ACT = act_acd_array['ACT']
    ACD = act_acd_array['ACD']

    # sorting on country_analytic
    country_analytic = sorted(country_analytic.items(),
                              key=lambda k: (k[1]['call_count'],
                                             k[1]['duration_sum']),
                              reverse=True)

    # Create Hangup Cause analytic in percentage format
    hangup_analytic_array = []
    hangup_analytic = sorted(hangup_analytic.items(), key=lambda k: k[0])
    if len(hangup_analytic) != 0:
        total_hangup = sum([int(x[1]) for x in hangup_analytic])
        for i in hangup_analytic:
            hangup_analytic_array.append(
                (get_hangupcause_name(int(i[0])), "{0:.0f}%".format((float(i[1]) / float(total_hangup)) * 100)))

    mail_data = {
        'yesterday_date': start_date,
        'rows': mongo_cdr_result,
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
@check_user_detail('accountcode,voipplan')
@login_required
def mail_report(request):
    """Mail Report Template

    **Attributes**:

        * ``template`` - cdr/mail_report.html
        * ``form`` - MailreportForm
        * ``mongodb_data_set`` - mongodb.cdr_common

    **Logic Description**:

        get top 10 calls from mongodb collection & hnagupcause/country analytic
        to generate mail report
    """
    logging.debug('CDR mail report view start')
    msg = ''
    form = EmailReportForm(request.user, request.POST or None, instance=request.user.userprofile)
    if form.is_valid():
        form.save()
        msg = _('email ids are saved successfully.')

    mail_data = get_cdr_mail_report()
    logging.debug('CDR mail report view end')
    data = {
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

            call_total_record[str(called_time)[:10]] = [value for key, value in call_day_hours.iteritems()]

            # Min per hour
            for dict_in_list in doc['duration_per_hour']:
                # update day_hours via key
                for key, value in dict_in_list.iteritems():
                    min_day_hours[int(key)] += float(value) / 60

            min_total_record[str(called_time)[:10]] = \
                [round_val(value) for key, value in min_day_hours.iteritems()]

    logging.debug('After Aggregate')

    variables = {
        'call_total_record': call_total_record,
        'min_total_record': min_total_record,
    }
    return variables


@permission_required('user_profile.daily_comparison', login_url='/')
@check_user_detail('accountcode')
@login_required
def cdr_daily_comparison(request):
    """
    Hourly CDR graph that compare with previous dates

    **Attributes**:

        * ``template`` - cdr/daily_comparison.html
        * ``form`` - CompareCallSearchForm

    **Logic Description**:

        get the call records aggregated from the CDR table
        using the materialized view and compare with other date records


    # hourly_charttype = "lineWithFocusChart"
    # daily_charttype = "lineWithFocusChart"
    # hourly_chartdata = {'x': []}
    # daily_chartdata = {'x': []}
    # metric = 'nbcalls'  # Default metric

    """
    # Default
    metric = 'nbcalls'
    switch_id = 0
    hourly_charttype = "multiBarChart"
    hourly_chartdata = {'x': []}
    compare_days = 2
    compare_type = COMPARE_WITH.previous_days
    today_date = datetime.today()
    form = CompareCallSearchForm(request.POST or None,
                                 initial={'from_date': today_date.strftime('%Y-%m-%d'),
                                          'compare_days': compare_days,
                                          'compare_type': compare_type,
                                          'switch_id': 0})

    today_date = datetime(today_date.year, today_date.month, today_date.day)
    current_date = today_date

    if form.is_valid():
        from_date = getvar(request, 'from_date')
        current_date = ceil_strdate(str(from_date), 'start')
        # current_date = trunc_date_start(from_date)
        switch_id = getvar(request, 'switch_id')
        compare_days = int(getvar(request, 'compare_days'))
        metric = getvar(request, 'metric')

    kwargs = {}

    if switch_id and switch_id != '0':
        kwargs['switch_id'] = int(switch_id)

    xdata = [i for i in range(0, 24)]
    hourly_chartdata = {'x': xdata}

    y_count = 1
    for nday in range(1, compare_days + 1):
        start_date = current_date + relativedelta(days=-int(nday-1))
        start_date = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0, 0)
        end_date = current_date + relativedelta(days=-int(nday-1))
        end_date = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, 999999)
        # Get hourly Data
        hourly_data = get_report_compare_cdr(request.user, 'hour', start_date, end_date, switch_id)

        extra_serie = {
            "tooltip": {"y_start": "", "y_end": " " + metric}
        }
        # We only need to set x axis once, so let's do it for nbcalls
        # hourly_chartdata['x'] = hourly_data["nbcalls"]["x_timestamp"]
        for switch in hourly_data[metric]["columns"]:
            serie = get_switch_ip_addr(switch) + "_day_" + str(nday)
            hourly_chartdata['name' + str(y_count)] = serie
            hourly_chartdata['y' + str(y_count)] = hourly_data[metric]["values"][str(switch)]
            hourly_chartdata['extra' + str(y_count)] = extra_serie
            y_count += 1

    variables = {
        'form': form,
        'from_date': current_date,
        'metric': metric,
        'compare_days': compare_days,
        'hourly_charttype': hourly_charttype,
        'hourly_chartdata': hourly_chartdata,
        'hourly_chartcontainer': 'hourly_chartcontainer',
        'hourly_extra': {
            'x_is_date': False,
            'x_axis_format': '',
            'tag_script_js': True,
            'jquery_on_ready': True,
        },
    }
    return render_to_response('cdr/daily_comparison.html', variables, context_instance=RequestContext(request))


def trunc_date_start(date, trunc_hour_min=False):
    """
    Convert a string date to a start date

    trunc_min allows to trunc the date to the minute
    """
    if isinstance(date, six.string_types):
        date = datetime.strptime(date, '%Y-%m-%d %H:%M')

    (hour, minute, second, millisec) = (0, 0, 0, 0)
    # if not trunc_hour_min:
    #     return datetime(date.year, date.month, date.day, date.hour, date.minute, 0, 0)
    # return start date
    return datetime(date.year, date.month, date.day, hour, minute, second, millisec)


def trunc_date_end(date, trunc_hour_min=False):
    """
    Convert a string date to a end date

    trunc_min allows to trunc the date to the minute
    """
    if isinstance(date, six.string_types):
        date = datetime.strptime(date, '%Y-%m-%d %H:%M')

    (hour, minute, second, millisec) = (23, 59, 59, 999999)
    # if not trunc_hour_min:
    #     return datetime(date.year, date.month, date.day, date.hour, date.minute, 0, 0)
    # return end date
    return datetime(date.year, date.month, date.day, hour, minute, second, millisec)


@permission_required('user_profile.overview', login_url='/')
@check_user_detail('accountcode')
@login_required
def cdr_overview(request):
    """CDR graph by hourly/daily/monthly basis

    **Attributes**:

        * ``template`` - cdr/overview.html
        * ``form`` - CdrOverviewForm

    **Logic Description**:

        Get Call records from Postgresql table and build
        all monthly, daily, hourly analytics
    """
    # initialize variables
    hourly_charttype = "lineWithFocusChart"
    daily_charttype = "lineWithFocusChart"
    hourly_chartdata = {'x': []}
    daily_chartdata = {'x': []}
    metric = 'nbcalls'  # Default metric

    action = 'tabs-1'
    tday = datetime.today()
    switch_id = 0
    # assign initial value in form fields
    form = CdrOverviewForm(request.POST or None,
                           initial={'from_date': tday.strftime('%Y-%m-%d 00:00'),
                                    'to_date': tday.strftime('%Y-%m-%d 23:55'),
                                    'switch_id': switch_id})
    start_date = trunc_date_start(tday)
    end_date = trunc_date_end(tday)

    logging.debug('CDR overview with search option')
    if form.is_valid():
        from_date = getvar(request, 'from_date')
        to_date = getvar(request, 'to_date')
        start_date = trunc_date_start(from_date)
        end_date = trunc_date_end(to_date)
        switch_id = getvar(request, 'switch_id')
        metric = getvar(request, 'metric')

    kwargs = {}

    if switch_id and switch_id != '0':
        kwargs['switch_id'] = int(switch_id)

    # Sanitize metric
    if metric not in ['nbcalls', 'duration', 'billsec', 'buy_cost', 'sell_cost']:
        metric = 'nbcalls'

    hourly_data = get_report_cdr_per_switch(request.user, 'hour', start_date, end_date, switch_id)
    daily_data = get_report_cdr_per_switch(request.user, 'day', start_date, end_date, switch_id)

    extra_serie = {
        "tooltip": {"y_start": "", "y_end": " " + metric},
        "date_format": "%d %b %y %H:%M%p"
    }
    for switch in hourly_data[metric]["columns"]:
        hourly_chartdata['x'] = hourly_data[metric]["x_timestamp"]
        hourly_chartdata['name' + str(switch)] = get_switch_ip_addr(switch)
        hourly_chartdata['y' + str(switch)] = hourly_data[metric]["values"][str(switch)]
        hourly_chartdata['extra' + str(switch)] = extra_serie

    for switch in daily_data[metric]["columns"]:
        daily_chartdata['x'] = daily_data[metric]["x_timestamp"]
        daily_chartdata['name' + str(switch)] = get_switch_ip_addr(switch)
        daily_chartdata['y' + str(switch)] = daily_data[metric]["values"][str(switch)]
        daily_chartdata['extra' + str(switch)] = extra_serie

    total_calls = hourly_data["nbcalls"]["total"]
    total_duration = hourly_data["duration"]["total"]
    total_billsec = hourly_data["billsec"]["total"]
    total_buy_cost = hourly_data["buy_cost"]["total"]
    total_sell_cost = hourly_data["sell_cost"]["total"]

    # Calculate the Average Time of Call
    metric_aggr = calculate_act_acd(total_calls, total_duration)

    # Get top 5 of country calls
    country_data = custom_sql_aggr_top_country(request.user, switch_id, 10, start_date, end_date)

    variables = {
        'action': action,
        'form': form,
        'start_date': start_date,
        'end_date': end_date,
        'metric': metric,
        'hourly_chartdata': hourly_chartdata,
        'hourly_charttype': hourly_charttype,
        'hourly_chartcontainer': 'hourly_container',
        'hourly_extra': {
            'x_is_date': True,
            'x_axis_format': '%d %b %y %H%p',
            'tag_script_js': True,
            'jquery_on_ready': False,
        },
        'daily_chartdata': daily_chartdata,
        'daily_charttype': daily_charttype,
        'daily_chartcontainer': 'daily_container',
        'daily_extra': {
            'x_is_date': True,
            'x_axis_format': '%d %b %Y',
            'tag_script_js': False,
            'jquery_on_ready': False,
        },
        'total_calls': total_calls,
        'total_duration': total_duration,
        'total_billsec': total_billsec,
        'total_buy_cost': total_buy_cost,
        'total_sell_cost': total_sell_cost,
        'metric_aggr': metric_aggr,
        'country_data': country_data,
    }
    return render_to_response('cdr/overview.html', variables, context_instance=RequestContext(request))


@permission_required('user_profile.by_country', login_url='/')
@check_user_detail('accountcode')
@login_required
def cdr_country_report(request):
    """CDR country report

    **Attributes**:

        * ``template`` - cdr/country_report.html
        * ``form`` - CountryReportForm

    **Logic Description**:

        get all call records from mongodb collection for all countries
        to create country call
    """
    logging.debug('CDR country report view start')
    switch_id = 0
    query_var = {}
    country_call_charttype = "pieChart"
    final_call_charttype = "lineWithFocusChart"
    final_duration_charttype = "lineWithFocusChart"
    country_call_chartdata = {'x': []}
    country_duration_chartdata = {'x': []}
    final_call_chartdata = {'x': []}
    final_duration_chartdata = {'x': []}

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
        from_date = getvar(request, 'from_date')
        start_date = ceil_strdate(str(from_date), 'start')

        to_date = getvar(request, 'to_date')
        end_date = ceil_strdate(str(to_date), 'end')
        switch_id = int(getvar(request, 'switch_id'))
        country_id = getvar(request, 'country_id')
        # convert list value in int
        country_id = [int(row) for row in country_id]
        if len(country_id) >= 1 and country_id[0] != 0:
            query_var['metadata.country_id'] = {'$in': country_id}

        if switch_id and switch_id != 0:
            query_var['metadata.switch_id'] = switch_id

    query_var['metadata.date'] = {'$gte': start_date, '$lt': end_date}
    if not request.user.is_superuser:  # not superuser
        query_var['metadata.accountcode'] = request.user.userprofile.accountcode

    # Country daily data
    # pipeline = pipeline_country_hourly_report(query_var)

    logging.debug('Before Aggregate')
    # list_data = mongodb.DBCON.command('aggregate',
    #                                   settings.MONGO_CDRSTATS['DAILY_ANALYTIC'],
    #                                   pipeline=pipeline)
    list_data = {}

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

                    # Create day_hours dict with call count, duration sum, country id
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

            # Update day_hours dict for duration sum
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
        final_call_chartdata = {'x': xdata}
        final_duration_chartdata = {'x': xdata}
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

    # World report
    # pipeline = pipeline_country_report(query_var)
    # list_data = mongodb.DBCON.command('aggregate',
    #                                   settings.MONGO_CDRSTATS['DAILY_ANALYTIC'],
    #                                   pipeline=pipeline)
    list_data = {}

    logging.debug('After Aggregate')
    country_analytic_array = []
    if list_data:
        for doc in list_data['result']:
            # country id - country name - call count - call duration - country_id
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
            # call_per_day - i[1]
            ydata.append(percentage(i[1], total_calls))
            # duration_per_day - i[2]
            ydata2.append(percentage(i[2], total_duration))

        extra_serie = {"tooltip": {"y_start": "", "y_end": " %"}}
        country_call_chartdata = {'x': xdata, 'y1': ydata, 'extra1': extra_serie}
        country_duration_chartdata = {'x': xdata, 'y1': ydata2, 'extra1': extra_serie}

    logging.debug('CDR country report view end')
    data = {
        'action': 'tabs-1',
        'total_calls': total_calls,
        'total_duration': total_duration,
        'country_analytic': country_analytic_array,
        'form': form,
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
@check_user_detail('accountcode,voipplan')
@login_required
def world_map_view(request):
    """CDR world report

    **Attributes**:

        * ``template`` - cdr/world_map.html
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
    now = datetime.now()
    start_date = datetime(now.year, now.month, now.day, 0, 0, 0, 0)
    end_date = datetime(now.year, now.month, now.day, 23, 59, 59, 999999)
    from_date = start_date.strftime("%Y-%m-%d")
    to_date = end_date.strftime("%Y-%m-%d")
    # assign initial value in form fields
    form = WorldForm(request.POST or None, initial={'from_date': from_date, 'to_date': to_date})

    if form.is_valid():
        logging.debug('CDR world report view with search option')
        from_date = getvar(request, 'from_date')
        start_date = ceil_strdate(str(from_date), 'start')

        to_date = getvar(request, 'to_date')
        end_date = ceil_strdate(str(to_date), 'end')
        switch_id = int(getvar(request, 'switch_id'))

        if switch_id and switch_id != 0:
            query_var['metadata.switch_id'] = switch_id

    query_var['metadata.date'] = {'$gte': start_date, '$lt': end_date}

    if not request.user.is_superuser:  # not superuser
        query_var['metadata.accountcode'] = request.user.userprofile.accountcode

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
        'form': form,
        'start_date': start_date,
        'end_date': end_date,
        'world_analytic_array': world_analytic_array,
        'action': action,
    }
    return render_to_response('cdr/world_map.html', variables, context_instance=RequestContext(request))
