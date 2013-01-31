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

from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.cache import cache_page
from django.shortcuts import render_to_response
from django.conf import settings
from django.utils.translation import gettext as _
from django.template.context import RequestContext
from voip_billing.models import VoIPRetailRate
from voip_billing.forms import PrefixRetailRrateForm, SimulatorForm, BillingForm,\
    HourlyBillingForm
from voip_billing.function_def import prefix_allowed_to_call
from voip_billing.rate_engine import rate_engine
from user_profile.models import UserProfile
from cdr.views import check_user_accountcode, check_cdr_exists, chk_account_code
#TODO: second time we import chk_account_code
from cdr.functions_def import chk_account_code
from cdr.aggregate import pipeline_daily_billing_report, pipeline_hourly_billing_report
from common.common_functions import current_view, ceil_strdate
from datetime import datetime
import logging
import time


@login_required
#@cache_page(60 * 5)
def retail_rate_view(request):
    """
    All Retail Rates are displayed & according to Destination No
    """
    template = 'voip_billing/retail_rate.html'
    form = PrefixRetailRrateForm()
    variables = RequestContext(request,
        {
            'module': current_view(request),
            'form': form,
            'user': request.user,
        })

    return render_to_response(template, variables,
           context_instance=RequestContext(request))


@login_required
def simulator(request):
    """
    Client Simulator
    To view rate according to VoIP Plan & Destination No.
    """
    template = 'voip_billing/simulator.html'
    error_msg = ""
    data = []
    form = SimulatorForm(request.user)
    # Get Voip Plan ID according to USER
    try:
        voipplan_id = UserProfile.objects.get(user=request.user).voipplan_id

        if request.method == 'POST':
            form = SimulatorForm(request.user, request.POST)
            if form.is_valid():
                # IS recipient_phone_no/destination no is valid prefix
                # (Not banned Prefix) ?
                destination_no = request.POST.get("destination_no")
                allowed = prefix_allowed_to_call(destination_no, voipplan_id)
                if allowed:
                    query = rate_engine(destination_no=destination_no, voipplan_id=voipplan_id)
                    for i in query:
                        r_r_plan = VoIPRetailRate.objects.get(id=i.rrid)
                        data.append((voipplan_id,
                                     r_r_plan.voip_retail_plan_id.name,
                                     i.retail_rate))
    except:
        error_msg = _('User is not attached with voip plan')

    data = {
        'module': current_view(request),
        'form': form,
        'data': data,
        'error_msg': error_msg,
    }
    return render_to_response(template, data,
        context_instance=RequestContext(request))


@permission_required('voip_report.daily_billing_report', login_url='/')
@check_cdr_exists
@check_user_accountcode
@login_required
def daily_billing_report(request):
    """CDR billing graph by daily basis

    **Attributes**:

        * ``template`` - voip_billing/daily_billing_report.html
        * ``form`` - BillingForm
        * ``mongodb_data_set`` - MONGO_CDRSTATS['DAILY_ANALYTIC']
        * ``aggregate`` - pipeline_daily_billing_report()

    **Logic Description**:

        get all call records from mongodb collection for
        daily billing analytics for given date
    """
    template = 'voip_billing/daily_billing_report.html'
    search_tag = 0
    tday = datetime.today()
    form = BillingForm(initial={'from_date': tday.strftime('%Y-%m-%d'),
                                'to_date': tday.strftime('%Y-%m-%d')})
    switch_id = 0
    if request.method == 'POST':
        search_tag = 1
        form = BillingForm(request.POST)
        if "from_date" in request.POST:
            from_date = request.POST['from_date']
            start_date = ceil_strdate(from_date, 'start')

        if "to_date" in request.POST:
            to_date = request.POST['to_date']
            end_date = ceil_strdate(to_date, 'end')

        if "switch" in request.POST:
            switch_id = request.POST['switch']
    else:
        start_date = datetime(tday.year, tday.month, tday.day, 0, 0, 0, 0)
        end_date = datetime(tday.year, tday.month, tday.day, 23, 59, 59, 999999)

    query_var = {}
    if switch_id and int(switch_id) != 0:
        query_var['metadata.switch_id'] = int(switch_id)

    query_var['metadata.date'] = {'$gte': start_date, '$lt': end_date}
    if not request.user.is_superuser:  # not superuser
        query_var['metadata.accountcode'] = chk_account_code(request)

    logging.debug('Aggregate daily billing analytic')
    pipeline = pipeline_daily_billing_report(query_var)

    logging.debug('Before Aggregate')
    list_data = settings.DBCON.command('aggregate',
                                       settings.MONGO_CDRSTATS['DAILY_ANALYTIC'],
                                       pipeline=pipeline)

    logging.debug('After Aggregate')
    daily_data = dict()
    total_data = []
    if list_data:
        for doc in list_data['result']:
            graph_day = datetime(int(doc['_id'][0:4]),
                                 int(doc['_id'][4:6]),
                                 int(doc['_id'][6:8]),
                                 0, 0, 0, 0)
            dt = int(1000 * time.mktime(graph_day.timetuple()))

            if dt in daily_data:
                daily_data[dt]['buy_cost_per_day'] += float(doc['buy_cost_per_day'])
                daily_data[dt]['sell_cost_per_day'] += float(doc['sell_cost_per_day'])
            else:
                daily_data[dt] = {
                    'buy_cost_per_day': float(doc['buy_cost_per_day']),
                    'sell_cost_per_day': float(doc['sell_cost_per_day']),
                }

            total_data = daily_data.items()
            total_data = sorted(total_data, key=lambda k: k[0])

    data = {
        'module': current_view(request),
        'form': form,
        'search_tag': search_tag,
        'total_data': total_data,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render_to_response(template, data, context_instance=RequestContext(request))


@permission_required('voip_report.hourly_billing_report', login_url='/')
@check_cdr_exists
@check_user_accountcode
@login_required
def hourly_billing_report(request):
    """CDR billing graph by hourly basis

    **Attributes**:

        * ``template`` - voip_billing/hourly_billing_report.html
        * ``form`` - HourlyBillingForm
        * ``mongodb_data_set`` - MONGO_CDRSTATS['DAILY_ANALYTIC']
        * ``aggregate`` - pipeline_hourly_billing_report()

    **Logic Description**:

        get all call records from mongodb collection for
        hourly billing analytics for given date
    """
    template = 'voip_billing/hourly_billing_report.html'
    search_tag = 0
    tday = datetime.today()
    form = HourlyBillingForm(initial={'from_date': tday.strftime('%Y-%m-%d')})
    switch_id = 0
    if request.method == 'POST':
        search_tag = 1
        form = HourlyBillingForm(request.POST)
        if "from_date" in request.POST:
            from_date = request.POST['from_date']
            start_date = ceil_strdate(from_date, 'start')

        start_date = datetime(start_date.year, start_date.month,
            start_date.day, 0, 0, 0, 0)
        end_date = datetime(start_date.year, start_date.month,
            start_date.day, 23, 59, 59, 999999)

        if "switch" in request.POST:
            switch_id = request.POST['switch']
    else:
        start_date = datetime(tday.year, tday.month, tday.day, 0, 0, 0, 0)
        end_date = datetime(tday.year, tday.month, tday.day, 23, 59, 59, 999999)

    query_var = {}

    if switch_id and int(switch_id) != 0:
        query_var['metadata.switch_id'] = int(switch_id)

    query_var['metadata.date'] = {'$gte': start_date, '$lt': end_date}
    if not request.user.is_superuser:  # not superuser
        query_var['metadata.accountcode'] = chk_account_code(request)

    logging.debug('Aggregate hourly billing analytic')
    pipeline = pipeline_hourly_billing_report(query_var)

    logging.debug('Before Aggregate')
    list_data = settings.DBCON.command('aggregate',
                                       settings.MONGO_CDRSTATS['DAILY_ANALYTIC'],
                                       pipeline=pipeline)

    logging.debug('After Aggregate')

    total_buy_record = {}
    total_sell_record = {}
    if list_data:
        for doc in list_data['result']:
            called_time = datetime(int(doc['_id'][0:4]),
                                   int(doc['_id'][4:6]),
                                   int(doc['_id'][6:8]))
            buy_hours = {}
            sell_hours = {}
            for hr in range(0, 24):
                buy_hours[hr] = 0
                sell_hours[hr] = 0

            for dict_in_list in doc['buy_cost_per_hour']:
                for key, value in dict_in_list.iteritems():
                    buy_hours[int(key)] += float(value)

            for dict_in_list in doc['sell_cost_per_hour']:
                for key, value in dict_in_list.iteritems():
                    sell_hours[int(key)] += float(value)

            total_buy_record[str(called_time)[:10]] = buy_hours
            total_sell_record[str(called_time)[:10]] = sell_hours

    data = {
        'module': current_view(request),
        'form': form,
        'search_tag': search_tag,
        'total_buy_record': total_buy_record,
        'total_sell_record': total_sell_record,
        'start_date': start_date,
    }
    return render_to_response(template, data, context_instance=RequestContext(request))
