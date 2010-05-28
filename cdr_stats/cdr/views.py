from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template.context import RequestContext
from cdr.models import CDR
from grid import ExampleGrid
from cdr_stats.helpers import json_encode




# Create your views here.

def grid_handler(request):
    # handles pagination, sorting and searching
    grid = ExampleGrid()
    return HttpResponse(grid.get_json(request), mimetype="application/json")

def grid_config(request):
    # build a config suitable to pass to jqgrid constructor   
    grid = ExampleGrid()
    return HttpResponse(grid.get_config(), mimetype="application/json")

def show_jqgrid(request):
    return render_to_response('cdr/show_jqgrid.html', None,
           context_instance = RequestContext(request))

def show_graph(request):
    return render_to_response('cdr/show_graph.html', None,
           context_instance = RequestContext(request))


def login(request):
    return render_to_response('cdr/login.html', None,
           context_instance = RequestContext(request))
           
def index(request):
    return render_to_response('cdr/index.html', None,
           context_instance = RequestContext(request))




