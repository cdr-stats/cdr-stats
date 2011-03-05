from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response
from django.db.models import *
from django.template.context import RequestContext
from django.conf import settings
from django.utils.translation import gettext as _
from django.db.models.loading import get_model

from datetime import *
from dateutil import parser
from dateutil.relativedelta import *
from sets import *
import string
from inspect import stack, getmodule

from cdr_stats.helpers import json_encode
from cdr.backend import BackendNotFound, BackendNotConfigured, get_cdr_backend, run_backend_view
from cdr.models import AsteriskCDR as CDR
from cdr.forms import *
from grid import ExampleGrid


def current_view():
    return stack()[1][3]


@login_required
def grid_handler(request):
    # handles pagination, sorting and searching
    grid = ExampleGrid()

    # To add dynamic query set
    grid.queryset  = request.session['cdr_queryset']

    return HttpResponse(grid.get_json(request), mimetype="application/json")

@login_required
def grid_config(request):
    # build a config suitable to pass to jqgrid constructor
    grid = ExampleGrid()

    # To add dynamic query set
    grid.queryset  = request.session['cdr_queryset']

    return HttpResponse(grid.get_config(), mimetype="application/json")


@login_required
def show_cdr(request): 
    return run_backend_view(request, current_view())



@login_required
def show_graph_by_month(request):
    return run_backend_view(request, current_view())


@login_required
def show_graph_by_day(request):
    return run_backend_view(request, current_view())
    

@login_required
def show_graph_by_hour(request):
    return run_backend_view(request, current_view())

    
@login_required
def show_concurrent_calls(request):
    return run_backend_view(request, current_view())


@login_required
def show_global_report(request):
    return run_backend_view(request, current_view())


@login_required
def show_dashboard(request):
    return run_backend_view(request, current_view())


def export_to_csv(request):
    return run_backend_view(request, current_view())


def login_view(request):
    template = 'cdr/index.html'
    errorlogin = ''
    if request.method == 'POST':
        try:
            action = request.POST['action']
        except (KeyError):
            action = "login"

        if action=="logout":
            logout(request)
        else:
            loginform = loginForm(request.POST)
            if loginform.is_valid():
                cd = loginform.cleaned_data
                user = authenticate(username=cd['user'], password=cd['password'])
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
                return HttpResponseRedirect('/')
    else :
        loginform = None;

    data = {
        'loginform' : loginform,
        'errorlogin' : errorlogin,
        'news' : get_news(),
        'is_authenticated' : request.user.is_authenticated()
    }
    return render_to_response(template, data,context_instance = RequestContext(request))


def logout_view(request):
	logout(request)
	return HttpResponseRedirect('/')



def index(request):
    template = 'cdr/index.html'
    errorlogin = ''
    loginform = loginForm()
    
    data = {'module': current_view(),
            'loginform' : loginform,
            'errorlogin' : errorlogin,
            'news' : get_news(),
    }
    return render_to_response(template, data,
           context_instance = RequestContext(request))


def pleaselog(request):
    template = 'cdr/index.html'
    loginform = loginForm()
    
    data = {
        'loginform' : loginform,
        'notlogged' : True,
        'news' : get_news(),
    }
    return render_to_response(template, data,
           context_instance = RequestContext(request))


