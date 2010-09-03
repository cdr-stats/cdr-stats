from cdr.models import *
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def report(request):
    cdr_list = CDR.objects.all()[:20];
    data = {
        'cdr_list' : cdr_list,
    }
    return render_to_response('admin/cdr/report.html',data,context_instance=RequestContext(request))
    
