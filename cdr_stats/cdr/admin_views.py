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
    
@staff_member_required
def list_invoice(request):
    invoice_list = Invoice.objects.all()
    data = {
        'invoice_list' : invoice_list,
    }
    return render_to_response('admin/cdr/invoice.html',data,context_instance=RequestContext(request))


@staff_member_required
def view_invoice(request, invoiceid):
    """ displays details about the invoice """
    invoice = Invoice.objects.get(pk = invoiceid)

    data = {
        'invoice_cnt' : InvoiceDetail.objects.filter(invoice=invoice).count(),
        'invoice' : invoice,
    }
    return render_to_response('admin/cdr/invoice_detail.html',data,context_instance=RequestContext(request))

