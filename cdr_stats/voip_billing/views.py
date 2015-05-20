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
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from voip_billing.models import VoIPRetailRate
from voip_billing.forms import PrefixRetailRateForm, SimulatorForm, BillingReportForm
from voip_billing.function_def import prefix_allowed_to_call
from voip_billing.rate_engine import rate_engine
from voip_billing.constants import RATE_COLUMN_NAME
from aggregator.pandas_cdr import get_report_cdr_per_switch
from aggregator.aggregate_cdr import custom_sql_aggr_top_country
from cdr.decorators import check_user_detail
from cdr.functions_def import get_switch_ip_addr, calculate_act_acd
from cdr.constants import Export_choice
from common.helpers import trunc_date_start, trunc_date_end
from django_lets_go.common_functions import getvar, get_pagination_vars
from datetime import datetime
import logging
import requests
import ast
import tablib
from apirest.view_voip_rate import find_rates


def rest_api_call(request, api_url):
    final_rate_list = []
    response = False
    try:
        response = requests.get(api_url, auth=(request.user, request.user), timeout=1.0)
        logging.debug('API requests.get response: ' + response)
    except requests.exceptions.Timeout:
        # Todo: we may want to deal with error nicely
        logging.debug('API Timeout Error : ' + api_url)
    except:
        logging.debug('API Error : ' + api_url)

    if response and response.status_code == 200:
        # due to string response of API, we need to convert response in to array
        rate_list = response.content.replace('[', '').replace(']', '').replace('}, {', '}|{').split('|')
        for i in rate_list:
            if i:
                # convert string into dict
                final_rate_list.append(ast.literal_eval(i))
    return final_rate_list


@permission_required('user_profile.call_rate', login_url='/')
@login_required
@check_user_detail('voipplan')
def voip_rates(request):
    """List voip call rates according to country prefix

    **Attributes**:

        * ``template`` - voip_billing/rates.html
        * ``form`` - PrefixRetailRateForm

    **Logic Description**:

        get all call rates from voip rate API and list them in template
        with pagination & sorting column
    """
    form = PrefixRetailRateForm(request.POST or None)
    final_rate_list = []
    # Get pagination data

    sort_col_field_list = ['prefix', 'retail_rate', 'destination']
    page_data = get_pagination_vars(request, sort_col_field_list, default_sort_field='prefix')

    sort_order = page_data['sort_order']
    order = 'ASC'
    if "-" in sort_order:
        order = 'DESC'
        sort_order = sort_order[1:]

    dialcode = ''
    if form.is_valid():
        dialcode = request.POST.get('prefix')
        request.session['dialcode'] = dialcode
    else:
        # pagination with prefix code
        if (request.session.get('dialcode') and (request.GET.get('page') or request.GET.get('sort_by'))):
            dialcode = request.session.get('dialcode')
            form = PrefixRetailRateForm(initial={'prefix': dialcode})
        else:
            # Reset variables
            request.session['dialcode'] = ''
            dialcode = ''
    if hasattr(request.user, 'userprofile'):
        voipplan_id = request.user.userprofile.voipplan_id
        if dialcode:
            final_rate_list = find_rates(voipplan_id, dialcode=dialcode, sort_field=sort_order, order=order)
        else:
            final_rate_list = find_rates(voipplan_id, dialcode=None, sort_field=sort_order, order=order)
    else:
        final_rate_list = []

    variables = {
        'form': form,
        'rate_list': final_rate_list,
        'rate_list_count': len(final_rate_list),
        'col_name_with_order': page_data['col_name_with_order'],
        'RATE_COLUMN_NAME': RATE_COLUMN_NAME,
        'sort_order': sort_order,
        'up_icon': '<i class="glyphicon glyphicon-chevron-up"></i>',
        'down_icon': '<i class="glyphicon glyphicon-chevron-down"></i>'
    }
    return render_to_response('voip_billing/rates.html',
                              variables,
                              context_instance=RequestContext(request))


@permission_required('user_profile.export_call_rate', login_url='/')
@login_required
def export_rate(request):
    """
    **Logic Description**:

        get the prifix rates  from voip rate API
        according to search parameters & store into csv file
    """
    format_type = request.GET['format']
    response = HttpResponse(content_type='text/%s' % format_type)
    response['Content-Disposition'] = 'attachment;filename=call_rate.%s' % format_type

    headers = ('prefix', 'destination', 'retail_rate')

    final_result = []
    if request.session.get('session_api_url'):
        api_url = request.session['session_api_url']
        final_result = rest_api_call(request, api_url)

    list_val = []
    for row in final_result:
        list_val.append((row['prefix'], row['prefix__destination'], row['retail_rate']))

    data = tablib.Dataset(*list_val, headers=headers)

    if format_type == Export_choice.XLS:
        response.write(data.xls)
    elif format_type == Export_choice.CSV:
        response.write(data.csv)
    elif format_type == Export_choice.JSON:
        response.write(data.json)

    return response


@permission_required('user_profile.simulator', login_url='/')
@check_user_detail('voipplan')
@login_required
def simulator(request):
    """Client Simulator
    To view rate according to VoIP Plan & Destination No.

    **Attributes**:

        * ``template`` - voip_billing/simulator.html
        * ``form`` - SimulatorForm

    **Logic Description**:

        get min call rates for destination from rate_engine and display them in template
    """
    data = []
    form = SimulatorForm(request.user, request.POST or None)
    # Get Voip Plan ID according to USER

    if form.is_valid():
        # IS recipient_phone_no/destination no is valid prefix
        # (Not banned Prefix) ?
        destination_no = request.POST.get("destination_no")
        if hasattr(request.user, 'userprofile'):
            voipplan_id = request.user.userprofile.voipplan_id
            allowed = prefix_allowed_to_call(destination_no, voipplan_id)
            if allowed:
                rates = rate_engine(voipplan_id=voipplan_id, dest_number=destination_no)
                for rate in rates:
                    r_r_plan = VoIPRetailRate.objects.get(id=rate.rrid)
                    data.append((voipplan_id,
                                 r_r_plan.voip_retail_plan_id.name,
                                 rate.retail_rate))
    data = {
        'form': form,
        'data': data,
    }
    return render_to_response('voip_billing/simulator.html',
                              data,
                              context_instance=RequestContext(request))


@permission_required('user_profile.billing_report', login_url='/')
@check_user_detail('accountcode,voipplan')
@login_required
def billing_report(request):
    """CDR billing graph by daily basis

    **Attributes**:

        * ``template`` - voip_billing/billing_report.html
        * ``form`` - BillingReportForm

    **Logic Description**:

        Retrieve call records from PostgreSQL and build the
        daily billing analytics for given date range
    """
    switch_id = 0
    tday = datetime.today()
    total_data = []
    charttype = "lineWithFocusChart"
    hourly_chartdata = {"x": []}

    form = BillingReportForm(request.POST or None,
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

    metrics = ['buy_cost', 'sell_cost']

    hourly_data = get_report_cdr_per_switch(request.user, 'hour', start_date, end_date, switch_id)

    hourly_chartdata['x'] = hourly_data["nbcalls"]["x_timestamp"]

    i = 0
    for metric in metrics:
        extra_serie = {
            "tooltip": {"y_start": "", "y_end": " " + metric},
            "date_format": "%d %b %y %H:%M%p"
        }
        for switch in hourly_data[metric]["columns"]:
            i = i + 1
            hourly_chartdata['name' + str(i)] = get_switch_ip_addr(switch) + "_" + metric
            hourly_chartdata['y' + str(i)] = hourly_data[metric]["values"][str(switch)]
            hourly_chartdata['extra' + str(i)] = extra_serie

    total_calls = hourly_data["nbcalls"]["total"]
    total_duration = hourly_data["duration"]["total"]
    total_billsec = hourly_data["billsec"]["total"]
    total_buy_cost = hourly_data["buy_cost"]["total"]
    total_sell_cost = hourly_data["sell_cost"]["total"]

    # Calculate the Average Time of Call
    metric_aggr = calculate_act_acd(total_calls, total_duration)

    # Get top 10 of country calls
    country_data = custom_sql_aggr_top_country(request.user, switch_id, 10, start_date, end_date)

    data = {
        'form': form,
        'total_data': total_data,
        'start_date': start_date,
        'end_date': end_date,
        'charttype': charttype,
        'chartdata': hourly_chartdata,
        'chartcontainer': 'chart_container',
        'extra': {
            'x_is_date': True,
            'x_axis_format': '%d %b %Y',
            'tag_script_js': True,
            'jquery_on_ready': True,
        },
        'total_calls': total_calls,
        'total_duration': total_duration,
        'total_billsec': total_billsec,
        'total_buy_cost': total_buy_cost,
        'total_sell_cost': total_sell_cost,
        'metric_aggr': metric_aggr,
        'country_data': country_data,
    }
    return render_to_response('voip_billing/billing_report.html',
                              data,
                              context_instance=RequestContext(request))
