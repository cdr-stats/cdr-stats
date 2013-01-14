# Create your views here.
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.views.decorators.cache import cache_page
from django.shortcuts import render_to_response

from django.template.context import RequestContext
from voip_billing.models import VoIPRetailRate
from voip_billing.forms import PrefixRetailRrateForm, SimulatorForm, BillingForm
from voip_billing.function_def import variable_value, prefix_allowed_to_voip_call
from voip_billing.rate_engine import rate_engine
from user_profile.models import UserProfile
from common.common_functions import current_view



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


@login_required
def billing_report(request):
    template = 'voip_billing/billing_report.html'
    action = 'tabs-1'

    form = BillingForm(request.user)
    if request.method == 'POST':
        form = BillingForm(request.user, request.POST)

    data = {
        'module': current_view(request),
        'form': form,
        #'data': data,
        'action': action,
    }
    return render_to_response(template, data, context_instance=RequestContext(request))
