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


def show_cdr(request):
    return render_to_response('cdr/show_cdr.html', None,
           context_instance = RequestContext(request))
           
           
def login(request):
    return render_to_response('cdr/login.html')

def index(request):
    cdr_list = CDR.objects.all()
    return render_to_response('cdr/index.html', {'cdr_list': cdr_list})



## JSON Pages
class JsonResponse(HttpResponse):
    def __init__(self, data):
        HttpResponse.__init__(self, content=json_encode(data), mimetype="application/json")


def json_cdr(request):
    import math

    selected_items = CDR.objects.all()
    page = 1
    total_pages = 0
    count = 0
    
    if request.REQUEST.has_key('nd'):
        limit = float(request.REQUEST['rows'])
        page = float(request.REQUEST['page'])
        sidx = request.REQUEST['sidx']
        sord = request.REQUEST['sord']
        set = request.REQUEST['set']

        start = limit * (page - 1)
        end = start + limit

        if sord == "desc":
            sord_hr = "-"
        else:
            sord_hr = ""

        #count = Volume.objects.filter(vicepartition__server__name=server_name).exclude(type__name="BK").count()
        count = CDR.objects.all().count()
        total_pages = math.ceil(count / limit)

        #selected_items = Volume.objects.filter(vicepartition__server__name=server_name).exclude(type__name="BK").order_by("%s%s" % (sord_hr, sidx))[int(start):int(end)]
        selected_items = CDR.objects.order_by("%s%s" % (sord_hr, sidx))[int(start):int(end)]

    data = []
    for line in selected_items:
        data.append({'id':line.acctid, 'cell':[
        		line.acctid,
                line.src,
                line.dst,
                line.calldate,
                line.clid,
                line.dcontext,
                line.channel,
                line.dstchannel,
                line.lastapp,
                line.lastdata,
                line.duration,
                line.billsec,
                line.disposition,
                line.disposition,
                line.amaflags,
                line.accountcode,
                line.uniqueid,
                line.userfield,
                line.test
            ]
            })

    return JsonResponse({
        "rows":data,
        "page":page,
        "total":total_pages,
        "records":count,
    })


