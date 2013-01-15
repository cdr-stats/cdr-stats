# Create your views here.
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.views.decorators.cache import cache_page
from django.shortcuts import render_to_response
from django.conf import settings
from django.template.context import RequestContext
from pymongo.connection import Connection
from pymongo.errors import ConnectionFailure


from voip_billing.models import VoIPRetailRate
from voip_billing.forms import PrefixRetailRrateForm, SimulatorForm, BillingForm
from voip_billing.function_def import variable_value, prefix_allowed_to_voip_call
from voip_billing.rate_engine import rate_engine
from user_profile.models import UserProfile
from cdr.views import check_user_accountcode, check_cdr_exists, chk_account_code
from cdr.functions_def import chk_account_code
from cdr.aggregate import pipeline_daily_billing_report
from common.common_functions import current_view, ceil_strdate
from datetime import datetime
import logging
import time


@login_required
@cache_page(60 * 5)
def retail_rate_view(request):
    """
    All Retail Rates are displayed & according to Destination No
    """
    template = 'voip_billing/retail_rate.html'
    form = PrefixRetailRrateForm()
    variables = RequestContext(request, {'module': current_view(request),
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
    # Assign form field value to local variable
    destination_no = variable_value(request, "destination_no")

    # Get SMS Plan ID according to USER
    dt = UserProfile.objects.get(user=request.user)
    voipplan_id = dt.voipplan_id #  variable_value(request, "plan_id")
    error = ""
    data = []

    form = SimulatorForm(request.user)

    if request.method == 'POST':
        form = SimulatorForm(request.user, request.POST)
        if form.is_valid():
            # IS recipient_phone_no/destination no is valid prefix
            # (Not banned Prefix) ?
            destination_no = request.POST.get("destination_no")

            allowed = prefix_allowed_to_voip_call(destination_no, voipplan_id)

            if allowed:
                query = rate_engine(destination_no=destination_no, voipplan_id=voipplan_id)
                for i in query:
                    r_r_plan = VoIPRetailRate.objects.get(id=i.rrid)
                    data.append((voipplan_id,
                                 r_r_plan.voip_retail_plan_id.name,
                                 i.retail_rate))

    data = {
        'module': current_view(request),
        'form': form,
        'data': data,
        'error': error,
    }
    return render_to_response(template, data,
                                context_instance=RequestContext(request))


#@permission_required('voip_billing.allow_cdr_view', login_url='/')
@check_cdr_exists
@check_user_accountcode
@login_required
def billing_report(request):
    template = 'voip_billing/billing_report.html'
    action = 'tabs-1'
    search_tag = 0
    tday = datetime.today()
    form = BillingForm(request.user)
    #plan_id = request.GET['plan_id']
    if request.method == 'POST':
        search_tag = 1
        form = BillingForm(request.user, request.POST)
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

        if "plan_id" in request.POST:
            plan_id = request.POST['plan_id']
    else:
        start_date = datetime(tday.year, tday.month, tday.day, 0, 0, 0, 0)
        end_date = datetime(tday.year, tday.month, tday.day, 23, 59, 59, 999999)

    query_var = {}
    query_var['metadata.date'] = {'$gte': start_date, '$lt': end_date}
    if not request.user.is_superuser:  # not superuser
        query_var['metadata.accountcode'] = chk_account_code(request)

    logging.debug('Aggregate cdr analytic')
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
                    'duration_sum': float(doc['sell_cost_per_day']),
                }

            total_data = daily_data.items()
            total_data = sorted(total_data, key=lambda k: k[0])


    data = {
        'module': current_view(request),
        'form': form,
        'search_tag': search_tag,
        'action': action,
        'total_data': total_data,
    }
    return render_to_response(template, data, context_instance=RequestContext(request))
