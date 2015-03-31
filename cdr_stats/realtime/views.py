#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2015 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.conf import settings
from django_lets_go.common_functions import getvar, ceil_strdate
from switch.models import Switch
from cdr.functions_def import get_switch_ip_addr
from cdr.forms import ConcurrentCallForm, SwitchForm
from cdr.decorators import check_user_detail
from datetime import datetime
from collections import defaultdict
import time
import logging


@permission_required('user_profile.concurrent_calls', login_url='/')
@check_user_detail('accountcode')
@login_required
def cdr_concurrent_calls(request):
    """CDR view of concurrent calls

    **Attributes**:

        * ``template`` - cdr/graph_concurrent_calls.html
        * ``form`` - ConcurrentCallForm
        * ``mongodb_data_set`` - MONGO_CDRSTATS['CONC_CALL_AGG'] (map-reduce collection)

    **Logic Description**:

        get all concurrent call records from mongodb map-reduce collection for
        current date
    """
    logging.debug('CDR concurrent view start')
    now = datetime.today()
    from_date = now.strftime('%Y-%m-%d')
    start_date = datetime(now.year, now.month, now.day, 0, 0, 0, 0)
    end_date = datetime(now.year, now.month, now.day, 23, 59, 59, 0)

    query_var = {}
    switch_id = 0

    form = ConcurrentCallForm(request.POST or None, initial={'from_date': from_date})
    logging.debug('CDR concurrent view with search option')

    if form.is_valid():
        from_date = getvar(request, 'from_date')
        switch_id = getvar(request, 'switch_id')

        start_date = ceil_strdate(from_date, 'start')
        end_date = ceil_strdate(from_date, 'end')

        if switch_id and int(switch_id) != 0:
            query_var['switch_id'] = int(switch_id)

    query_var['date'] = {'$gte': start_date, '$lt': end_date}

    if not request.user.is_superuser:  # not superuser
        query_var['accountcode'] = request.user.userprofile.accountcode

    xdata = []
    charttype = "stackedAreaChart"
    call_count_res = defaultdict(list)

    if query_var:
        # calls_in_day = mongodb.conc_call_agg.find(query_var).sort([('date', 1)])
        calls_in_day = {}

        for d in calls_in_day:
            # convert date into timestamp value
            ts = time.mktime(d['date'].timetuple())
            tsint = int(ts * 1000)
            xdata.append(str(tsint))
            call_count_res[d['switch_id']].append(d['numbercall'])

        int_count = 1
        chartdata = {'x': xdata}
        extra_serie = {"tooltip": {"y_start": "", "y_end": " concurrent calls"},
                       "date_format": "%d %b %Y %I:%M:%S %p"}
        for i in call_count_res:
            chartdata['name' + str(int_count)] = str(get_switch_ip_addr(i))
            chartdata['y' + str(int_count)] = call_count_res[i]
            chartdata['extra' + str(int_count)] = extra_serie
            int_count += 1

        logging.debug('CDR concurrent view end')
        data = {
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
@check_user_detail('accountcode')
@login_required
def cdr_realtime(request):
    """Call realtime view

    **Attributes**:

        * ``template`` - cdr/realtime.html
        * ``form`` - SwitchForm
        * ``mongodb_collection`` - MONGO_CDRSTATS['CONC_CALL_AGG'] (map-reduce collection)

    **Logic Description**:

        get all call records from mongodb collection for
        concurrent analytics
    """
    logging.debug('CDR realtime view start')
    query_var = {}
    switch_id = 0
    list_switch = Switch.objects.all()
    form = SwitchForm(request.POST or None)
    if form.is_valid():
        switch_id = int(getvar(request, 'switch_id'))
        if switch_id and switch_id != 0:
            query_var['value.switch_id'] = switch_id

    now = datetime.now()
    start_date = datetime(now.year, now.month, now.day, 0, 0, 0, 0)
    end_date = datetime(now.year, now.month, now.day, 23, 59, 59, 999999)

    query_var['value.call_date'] = {'$gte': start_date, '$lt': end_date}
    if not request.user.is_superuser:  # not superuser
        query_var['value.accountcode'] = request.user.userprofile.accountcode

    # calls_in_day = mongodb.conc_call_agg.find(query_var).sort([('_id.g_Millisec', -1)])
    calls_in_day = {}

    final_data = []
    for d in calls_in_day:
        dt = int(d['_id']['g_Millisec'])
        final_data.append((dt, int(d['value']['numbercall__max'])))

    logging.debug('Realtime view end')
    variables = {
        'form': form,
        'final_data': final_data,
        'list_switch': list_switch,
        'colorgraph1': '180, 0, 0',
        'colorgraph2': '0, 180, 0',
        'colorgraph3': '0, 0, 180',
        'realtime_graph_maxcall': settings.REALTIME_Y_AXIS_LIMIT,
    }
    return render_to_response('cdr/graph_realtime.html', variables, context_instance=RequestContext(request))
