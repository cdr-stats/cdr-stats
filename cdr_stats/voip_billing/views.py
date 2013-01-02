# Create your views here.
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.views.decorators.cache import cache_page
from django.shortcuts import render_to_response
from django.db.models import *
from django.template.context import RequestContext
from django.utils.translation import ugettext as _
from voip2bill.voip_billing.models import *
from voip2bill.voip_billing.forms import *
from voip2bill.voip_billing.function_def import *
from voip2bill.voip_billing.tasks import *
from voip2bill.user_profile.models import *
from helpers import json_encode
from inspect import stack, getmodule
from datetime import *
from random import *


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


def index(request):
    """
    Index page
    """
    template = 'voip_billing/index.html'
    errorlogin = ''
    loginform = LoginForm()

    data = {'module': current_view(request),
            'loginform' : loginform,
            'errorlogin' : errorlogin,
    }
    return render_to_response(template, data,
           context_instance=RequestContext(request))


def login_view(request):
    template = 'voip_billing/index.html'
    errorlogin = ''
    if request.method == 'POST':
        try:
            action = request.POST['action']
        except (KeyError):
            action = "login"

        if action=="logout":
            logout(request)            
        else:
            loginform = LoginForm(request.POST)            
            if loginform.is_valid():                
                cd = loginform.cleaned_data
                user = authenticate(username=cd['user'],
                                    password=cd['password'])
                if user is not None:
                    if user.is_active:
                        login(request, user)
                        # Redirect to a success page.                        
                    else:
                        # Return a 'disabled account' error message
                        errorlogin = _('Disabled Account') #True
                else:
                    # Return an 'invalid login' error message.
                    errorlogin = _('Invalid Login.') #True
            else:
                # Return an 'Valid User Credentials' error message.
                errorlogin = _('Enter Valid User Credentials.') #True                
    else:
        loginform = LoginForm()

    data = {
        'loginform' : loginform,
        'errorlogin' : errorlogin,
        'is_authenticated' : request.user.is_authenticated()
    }
    return render_to_response(template, data,
           context_instance = RequestContext(request))


def logout_view(request):
	logout(request)
	return HttpResponseRedirect('/')
