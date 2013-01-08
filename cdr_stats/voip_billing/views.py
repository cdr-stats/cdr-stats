# Create your views here.
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.views.decorators.cache import cache_page
from django.shortcuts import render_to_response

from django.template.context import RequestContext

from voip_billing.forms import PrefixRetailRrateForm, SimulatorForm
from voip_billing.function_def import variable_value, prefix_allowed_to_voip_call,\
    simulator_function
from user_profile.models import UserProfile
from inspect import stack, getmodule


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


def current_view(request):
    name = getmodule(stack()[1][0]).__name__
    return stack()[1][3]


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
    data = ""

    if request.method == 'POST':
        # IS recipient_phone_no/destination no is valid prefix
        # (Not banned Prefix) ?
        allowed = prefix_allowed_to_voip_call(destination_no, voipplan_id)

        if allowed:
            data = simulator_function(request, "client")

    form = SimulatorForm(request.user,
                         initial={'destination_no': destination_no,
                                  'plan_id': voipplan_id})
    variables = RequestContext(request, {'module': current_view(request),
                                         'form': form,
                                         'data': data,
                                         'error': error,
                                        })
    return render_to_response(template, variables,
                                context_instance=RequestContext(request))


