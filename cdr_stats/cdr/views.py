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
from aggregator.aggregate_cdr import custom_sql_aggr_top_country, custom_sql_aggr_top_hangup_last24hours, \
    custom_sql_matv_voip_cdr_aggr_last24hours, \
    custom_sql_aggr_top_country_last24hours
from aggregator.pandas_cdr import get_report_cdr_per_switch, get_report_compare_cdr, \
    get_report_cdr_per_country
from voip_billing.function_def import round_val
from bson.objectid import ObjectId
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import json
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

        * ``template`` - cdr/list.html
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

    # Build filter for CDR.object
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

        Retrieve calls records from Postgresql according to search
        parameters, then export the result into CSV/XLS/JSON file
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
def cdr_detail(request, cdr_id):
    """Detail of Call

    **Attributes**:

        * ``template`` - cdr/cdr_detail.html

    **Logic Description**:

        Get details from CDR through the jsonb data field
    """
    menu = show_menu(request)

    try:
        cdr = CDR.objects.get(id=cdr_id)
    except CDR.DoesNotExist:
        raise Http404

    data = {
        'cdr': cdr,
        'cdr_data': cdr.data,
        'menu': menu
    }
    return render_to_response('cdr/cdr_detail.html',
                              data, context_instance=RequestContext(request))


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
    (calls_hour_aggr, total_calls, total_duration, total_billsec, total_buy_cost, total_sell_cost) = custom_sql_matv_voip_cdr_aggr_last24hours(request.user, switch_id)

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

    # Get top 5 of country calls for last 24 hours
    country_data = custom_sql_aggr_top_country_last24hours(request.user, switch_id, limit=5)

    # Build pie chart data for last 24h calls per country
    (xdata, ydata) = ([], [])
    for country in country_data:
        xdata.append(get_country_name(country["country_id"]))
        ydata.append(percentage(country["nbcalls"], total_calls))

    color_list = ['#FFC36C', '#FFFF9D', '#BEEB9F', '#79BD8F', '#FFB391']
    extra_serie = {"tooltip": {"y_start": "", "y_end": " %"}, "color_list": color_list}
    country_analytic_chartdata = {'x': xdata, 'y1': ydata, 'extra1': extra_serie}
    country_analytic_charttype = "pieChart"

    country_extra = {
        'x_is_date': False,
        'x_axis_format': '',
        'tag_script_js': True,
        'jquery_on_ready': True,
    }

    # Get top 10 of hangup cause calls for last 24 hours
    hangup_cause_data = custom_sql_aggr_top_hangup_last24hours(request.user, switch_id)

    # hangup analytic pie chart data
    (xdata, ydata) = ([], [])
    for hangup_cause in hangup_cause_data:
        xdata.append(str(get_hangupcause_name(hangup_cause["hangup_cause_id"])))
        ydata.append(str(percentage(hangup_cause["nbcalls"], total_calls)))

    color_list = ['#2A343F', '#7E8282', '#EA9664', '#30998F', '#449935']
    extra_serie = {"tooltip": {"y_start": "", "y_end": " %"}, "color_list": color_list}
    hangup_analytic_chartdata = {'x': xdata, 'y1': ydata, 'extra1': extra_serie}
    hangup_analytic_charttype = "pieChart"

    hangup_extra = country_extra

    logging.debug("Result calls_hour_aggr %d" % len(calls_hour_aggr))
    logging.debug("Result hangup_cause_data %d" % len(hangup_cause_data))
    logging.debug("Result country_data %d" % len(country_data))

    # Calculate the Average Time of Call
    metric_aggr = calculate_act_acd(total_calls, total_duration)

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


def get_cdr_mail_report(user):
    """
    General function to get previous day CDR report
    """
    # Get yesterday's CDR-Stats Mail Report
    yesterday = date.today() - timedelta(1)
    start_date = trunc_date_start(yesterday)
    end_date = trunc_date_end(yesterday)

    # Build filter for CDR.object
    kwargs = {}
    if start_date:
        kwargs['starting_date__gte'] = start_date

    if end_date:
        kwargs['starting_date__lte'] = end_date

    # user are restricted to their own CDRs
    if not user.is_superuser:
        kwargs['user_id'] = user.id

    cdrs = CDR.objects.filter(**kwargs)[:10]

    # Get list of calls/duration for each of the last 24 hours
    (calls_hour_aggr, total_calls, total_duration, total_billsec, total_buy_cost, total_sell_cost) = custom_sql_matv_voip_cdr_aggr_last24hours(user, switch_id=0)

    # Get top 5 of country calls for last 24 hours
    country_data = custom_sql_aggr_top_country_last24hours(user, switch_id=0, limit=5)

    # Get top 10 of hangup cause calls for last 24 hours
    hangup_cause_data = custom_sql_aggr_top_hangup_last24hours(user, switch_id=0)

    # Calculate the Average Time of Call
    metric_aggr = calculate_act_acd(total_calls, total_duration)

    mail_data = {
        'yesterday_date': start_date,
        'rows': cdrs,
        'total_duration': total_duration,
        'total_calls': total_calls,
        'total_buy_cost': total_buy_cost,
        'total_sell_cost': total_sell_cost,
        'metric_aggr': metric_aggr,
        'country_data': country_data,
        'hangup_cause_data': hangup_cause_data,
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

    **Logic Description**:

        get top 10 calls Postgresql & hangup / country analytic
        to generate mail report
    """
    logging.debug('CDR mail report view start')
    msg = ''
    form = EmailReportForm(request.user, request.POST or None, instance=request.user.userprofile)
    if form.is_valid():
        form.save()
        msg = _('email ids are saved successfully.')

    mail_data = get_cdr_mail_report(request.user)

    data = {
        'yesterday_date': mail_data['yesterday_date'],
        'rows': mail_data['rows'],
        'form': form,
        'total_duration': mail_data['total_duration'],
        'total_calls': mail_data['total_calls'],
        'total_buy_cost': mail_data['total_buy_cost'],
        'total_sell_cost': mail_data['total_sell_cost'],
        'metric_aggr': mail_data['metric_aggr'],
        'country_data': mail_data['country_data'],
        'hangup_cause_data': mail_data['hangup_cause_data'],
        'msg': msg,
    }
    return render_to_response('cdr/mail_report.html', data, context_instance=RequestContext(request))


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

    # check metric is valid
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

    # Get top 10 of country calls
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
    metric = 'nbcalls'
    tday = datetime.today()

    switch_id = 0
    hourly_charttype = "lineWithFocusChart"
    hourly_chartdata = {'x': []}
    country_id_list = []
    total_metric = 0

    # assign initial value in form fields
    form = CountryReportForm(request.POST or None,
                             initial={'from_date': tday.strftime('%Y-%m-%d 00:00'),
                                    'to_date': tday.strftime('%Y-%m-%d 23:55'),
                                    'switch_id': switch_id})

    start_date = trunc_date_start(tday)
    end_date = trunc_date_end(tday)

    if form.is_valid():
        from_date = getvar(request, 'from_date')
        to_date = getvar(request, 'to_date')
        start_date = trunc_date_start(from_date)
        end_date = trunc_date_end(to_date)
        switch_id = getvar(request, 'switch_id')
        metric = getvar(request, 'metric')
        country_id = form.cleaned_data['country_id']
        # convert list value in int
        country_id_list = [int(row) for row in country_id]

    # check metric is valid
    if metric not in ['nbcalls', 'duration', 'billsec', 'buy_cost', 'sell_cost']:
        metric = 'nbcalls'

    hourly_data = get_report_cdr_per_country(request.user, 'hour', start_date, end_date, switch_id, country_id_list)

    extra_serie = {
        "tooltip": {"y_start": "", "y_end": " " + metric},
        "date_format": "%d %b %y %H:%M%p"
    }
    for country in hourly_data[metric]["columns"]:
        hourly_chartdata['x'] = hourly_data[metric]["x_timestamp"]
        hourly_chartdata['name' + str(country)] = str(get_country_name(int(country)))
        hourly_chartdata['y' + str(country)] = hourly_data[metric]["values"][str(country)]
        hourly_chartdata['extra' + str(country)] = extra_serie

    total_calls = hourly_data["nbcalls"]["total"]
    total_duration = hourly_data["duration"]["total"]
    total_billsec = hourly_data["billsec"]["total"]
    total_buy_cost = hourly_data["buy_cost"]["total"]
    total_sell_cost = hourly_data["sell_cost"]["total"]

    # Calculate the Average Time of Call
    metric_aggr = calculate_act_acd(total_calls, total_duration)

    # Get top 10 of country calls
    top_country = 10
    country_data = custom_sql_aggr_top_country(request.user, switch_id, top_country, start_date, end_date)

    # Build pie chart data for last 24h calls per country
    (xdata, ydata) = ([], [])
    for country in country_data:
        xdata.append(get_country_name(country["country_id"]))
        ydata.append(percentage(country["nbcalls"], total_calls))

    color_list = ['#FFC36C', '#FFFF9D', '#BEEB9F', '#79BD8F', '#FFB391',
        '#58A6A6', '#86BF30', '#F2D022', '#D9AA1E', '#D98236']

    extra_serie = {"tooltip": {"y_start": "", "y_end": " %"}, "color_list": color_list}
    country_analytic_chartdata = {'x': xdata, 'y1': ydata, 'extra1': extra_serie}
    country_analytic_charttype = "pieChart"

    country_extra = {
        'x_is_date': False,
        'x_axis_format': '',
        'tag_script_js': True,
        'jquery_on_ready': True,
    }

    # -------------- Build data to pass to Request ---------------
    data = {
        'action': 'tabs-1',
        'total_metric': total_metric,
        'start_date': start_date,
        'end_date': end_date,
        'metric': metric,
        'form': form,
        'NUM_COUNTRY': settings.NUM_COUNTRY,
        'hourly_charttype': hourly_charttype,
        'hourly_chartdata': hourly_chartdata,
        'hourly_chartcontainer': 'hourly_container',
        'hourly_extra': {
            'x_is_date': True,
            'x_axis_format': '%d %b %Y',
            'tag_script_js': True,
            'jquery_on_ready': False,
        },
        'total_calls': total_calls,
        'total_duration': total_duration,
        'total_billsec': total_billsec,
        'total_buy_cost': total_buy_cost,
        'total_sell_cost': total_sell_cost,
        'metric_aggr': metric_aggr,
        'country_data': country_data,

        'country_analytic_charttype': country_analytic_charttype,
        'country_analytic_chartdata': country_analytic_chartdata,
        'country_chartcontainer': 'country_piechart_container',
        'country_extra': country_extra,
        'top_country': top_country,
    }
    return render_to_response('cdr/country_report.html', data, context_instance=RequestContext(request))


def generate_crate(max_num):
    """
    helper function to generate well distributed grates
    """
    increment = max_num / 7
    base = max_num / 10
    grades = []
    for i in range(0, 7):
        x = i * increment
        grades.append(int(base * round(float(x) / base)))

    # Add the max too
    grades.append(max_num)
    return grades


@permission_required('user_profile.world_map', login_url='/')
@check_user_detail('accountcode,voipplan')
@login_required
def world_map_view(request):
    """CDR world report

    **Attributes**:

        * ``template`` - cdr/world_map.html
        * ``form`` - WorldForm
    """
    logging.debug('CDR world report view start')
    action = 'tabs-1'
    switch_id = 0
    tday = datetime.today()
    # Assign initial value in form fields
    form = WorldForm(request.POST or None,
                     initial={'from_date': tday.strftime('%Y-%m-%d 00:00'),
                              'to_date': tday.strftime('%Y-%m-%d 23:55'),
                              'switch_id': switch_id})

    start_date = trunc_date_start(tday)
    end_date = trunc_date_end(tday)

    if form.is_valid():
        from_date = getvar(request, 'from_date')
        to_date = getvar(request, 'to_date')
        start_date = trunc_date_start(from_date)
        end_date = trunc_date_end(to_date)
        switch_id = getvar(request, 'switch_id')

    # Get top 10 of country calls
    top_country = 300
    country_data = custom_sql_aggr_top_country(request.user, switch_id, top_country, start_date, end_date)

    world_analytic_array = []
    max_nbcalls = 0
    for country in country_data:
        # append data to world_analytic_array with following order
        # country id|country name|call count|call duration|country_id|buy cost|sell cost
        # TODO: remove int()
        country_data = {}
        country_data["country_id"] = int(country["country_id"])
        country_data["country_iso3"] = get_country_name(int(country["country_id"]), type='iso3').upper()
        country_data["country_name"] = get_country_name(int(country["country_id"]))
        country_data["nbcalls"] = int(country["nbcalls"])
        if country_data["nbcalls"] > max_nbcalls:
            max_nbcalls = country_data["nbcalls"]
        country_data["duration"] = int(country["duration"])
        country_data["billsec"] = int(country["billsec"])
        country_data["buy_cost"] = float(country["buy_cost"])
        country_data["sell_cost"] = float(country["sell_cost"])
        world_analytic_array.append(country_data)

    max_nbcalls = int(round(max_nbcalls, -3))

    call_crates = generate_crate(max_nbcalls)

    variables = {
        'form': form,
        'start_date': start_date,
        'end_date': end_date,
        'world_analytic_array': world_analytic_array,
        'action': action,
        'call_crates': call_crates,
    }
    return render_to_response('cdr/world_map.html',
                              variables, context_instance=RequestContext(request))
