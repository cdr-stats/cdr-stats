from django.contrib import admin
from django.conf.urls import patterns
from django.utils.translation import ugettext as _
from django.template import RequestContext
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.db.models import Sum, Avg, Count

from voip_billing.tasks import VoIPbilling
from voip_billing.function_def import check_celeryd_process
from voip_report.models import VoIPCall_Report, VoIPCall
from voip_report.forms import VoipSearchForm, FileImport
from voip_report.function_def import voipcall_record_common_fun, get_disposition_id,\
    get_disposition_name
from user_profile.models import UserProfile
from datetime import datetime
import csv


class VoIPCall_ReportAdmin(admin.ModelAdmin):
    can_add = False
    detail_title = _("VoIPCall_Report")
    list_display = ('recipient_number', 'user', 'callid', 'dnid',
                    'uniqueid', 'callerid', 'disposition', 'sessiontime',
                    'destination_name', 'sessiontime_real', 'gateway',
                    'carrier_cost', 'retail_cost', 'voipplan_name', 'billed')

    def has_add_permission(self, request):
        """
        Remove Add permission on VoIP Call Report Model
        """
        if not self.can_add:
            return False
        return super(VoIPCall_ReportAdmin, self).has_add_permission(request)

    def get_urls(self):
        urls = super(VoIPCall_ReportAdmin, self).get_urls()
        my_urls = patterns('',
            (r'^$', self.admin_site.admin_view(self.changelist_view)),
            (r'^import_voip_report/$',
             self.admin_site.admin_view(self.import_voip_report)),
            (r'^export_voip_report/$',
             self.admin_site.admin_view(self.export_voip_report)),
        )
        return my_urls + urls
    
    def queryset(self, request):
        """
        Queryset will be changed as per the search parameter selection
        on changelist_view
        """
        kwargs = {}
        if request.method == 'POST':
            kwargs = voipcall_record_common_fun(request, form_require="no")
        else:
            tday = datetime.today()
            kwargs['updated_date__gte'] = datetime(tday.year,
                                                   tday.month,
                                                   tday.day, 0, 0, 0, 0)

        qs = super(VoIPCall_ReportAdmin, self).queryset(request)
        return qs.filter(**kwargs).order_by('-updated_date')

    def changelist_view(self, request, extra_context=None):
        """
        VoIP Report Record Listing with Search Option & Daily Call Report
        Search Parameters: By date, By status, By billed
        """
        opts = VoIPCall_Report._meta
        app_label = opts.app_label
        kwargs = {}
        form = VoipSearchForm()        
        if request.method == 'POST':
            form = voipcall_record_common_fun(request, form_require="yes")
            kwargs = voipcall_record_common_fun(request, form_require="no")                                   
        else:
            tday = datetime.today()
            kwargs['updated_date__gte'] = datetime(tday.year,
                                                   tday.month,
                                                   tday.day, 0, 0, 0, 0)

        # Session variable is used to get recrod set with searched option
        # into export file
        request.session['voipcall_record_qs'] = \
        super(VoIPCall_ReportAdmin, self).queryset(request).filter(**kwargs)\
        .order_by('-updated_date')        
        
        select_data =  {"updated_date": "SUBSTR(CAST(updated_date as CHAR(30)),1,10)"}
        total_data = ''
        """
        
        total_data = \
        VoIPCall_Report.objects.extra(select=select_data).values('updated_date')\
        .filter(**kwargs).annotate(Count('updated_date'))\        
        .annotate(Sum('carrier_cost')).annotate(Sum('retail_cost'))\
        .order_by('-updated_date')
        """
        # Get Total Rrecords from VoIPCall Report table for Daily Call Report
        kwargs['billed'] = True
        total_data = VoIPCall_Report.objects.extra(select=select_data)\
                     .values('starting_date')\
                     .filter(**kwargs).annotate(Count('starting_date'))\
                     .annotate(Sum('sessiontime_real'))\
                     .annotate(Avg('sessiontime_real'))\
                     .annotate(Sum('carrier_cost'))\
                     .annotate(Sum('retail_cost')).order_by('-starting_date')

        # Calcualte Profit
        profit = []
        key = 0
        for i in total_data:
            profit.append((key,
                           i['retail_cost__sum'] - i['carrier_cost__sum']))
            key = key + 1

        # Following code will count total voip calls, duration
        # carrier_cost, retail_cost Max profit
        if total_data.count() != 0:
            max_duration = max([x['sessiontime_real__sum'] for x in total_data])
            total_duration = sum([x['sessiontime_real__sum'] for x in total_data])
            total_calls = sum([x['starting_date__count'] for x in total_data])
            total_avg_duration = (sum([x['sessiontime_real__avg'] for x in total_data]))/total_data.count()
            total_carrier_cost = sum([x['carrier_cost__sum'] for x in total_data])
            total_retail_cost = sum([x['retail_cost__sum'] for x in total_data])
            total_profit = sum([x[1] for x in profit])
        else:
            max_duration = 0
            total_duration = 0
            total_calls = 0
            total_avg_duration = 0
            total_carrier_cost = 0
            total_retail_cost = 0
            total_profit = 0

        ctx = {
            'form': form,
            'total_data':  total_data.reverse(),
            'profit': profit,
            'total_duration':total_duration,
            'total_calls':total_calls,
            'total_avg_duration':total_avg_duration,
            'total_carrier_cost': total_carrier_cost,
            'total_retail_cost': total_retail_cost,
            'total_profit': total_profit,
            'max_duration':max_duration,
            'opts': opts,
            'model_name': opts.object_name.lower(),
            'app_label': _('VoIP Report'),
            'title': _('VoIP Call Report'),
        }
        return super(VoIPCall_ReportAdmin, self)\
               .changelist_view(request, extra_context=ctx)

    def import_voip_report(self, request):
        """
        Import CSV file of VoIP Report
        """
        opts = VoIPCall_Report._meta
        app_label = opts.app_label
        file_exts = ('.csv')
        rdr = ''
        msg = ''
        success_import_list = []
        error_import_list = []

        if request.method == 'POST':
            form = FileImport(request.POST, request.FILES)
            if form.is_valid():
                # col_no - field name
                #  0     - Recipient Phone No
                #  1     - Sender Phone No
                #  2     - Disposition
                #  3     - Sessiontime
                #  4     - Sessiontime real
                #  5     - Customer_id
                #  6     - Starting Date
                # Total no of records in CSV file
                records = csv.reader(request.FILES['csv_file'],
                                     delimiter=',', quotechar='"')
                total_rows = len(list(records))

                rdr = csv.reader(request.FILES['csv_file'],
                                 delimiter=',', quotechar='"')
                voipcall_record_count = 0

                if check_celeryd_process():
                    for row in rdr:
                        if (row > 0):
                            # Insert record

                            # To get delivery date
                            if len(row) == 7 and row[6] != '':
                                starting_date = datetime.strptime(row[6],
                                             '%Y-%m-%d %H:%M:%S')
                            else:
                                starting_date = datetime.now()
                            
                            user_voip_plan = \
                                UserProfile.objects.get(user=request.user)
                            voipplan_id = user_voip_plan.voipplan_id #  1
                            try:                        
                                # Create VoIP call record
                                voipcall = VoIPCall.objects.create(
                                         user=request.user,
                                         recipient_number=row[0],
                                         callid=1,
                                         callerid=row[1],
                                         dnid=1,
                                         nasipaddress='0.0.0.0',
                                         sessiontime=row[3],
                                         sessiontime_real=row[4],
                                         starting_date=starting_date,
                                         disposition=get_disposition_id(row[2]),
                                         )                                
                                
                                response = \
                                    VoIPbilling.delay(voipcall_id=voipcall.id,
                                                      voipplan_id=voipplan_id)

                                # Due to task voipcall_id is disconnected/blank
                                # So need to get back voipcall id
                                res = response.get()

                                # Created VoIPCall Report gets created date
                                #obj = \
                                #VoIPCall_Report.objects.get(pk=res['voipcall_id'])
                                #obj.created_date = starting_date
                                #obj.save()

                                # Voipcall status get changed according
                                # to disposition
                                response = voipcall._update_voip_call_status(
                                                            res['voipcall_id'])

                                voipcall_record_count = voipcall_record_count + 1
                                msg = '%d Record(s) are uploaded successfully\
                                      out of %d Record(s)!' % \
                                      (voipcall_record_count, total_rows)
                                success_import_list.append(row)
                            except:
                                error_import_list.append(row)
                                msg = _("Error : invalid value for import! \
                                       Please look at the import samples.")
                else:
                    msg = _("Error : Please Start Celeryd Service !!")
        else:
            form = FileImport()

        ctx = RequestContext(request, {
        'form': form,
        'opts': opts,
        'model_name': opts.object_name.lower(),
        'app_label': _('VoIP Report'),
        'success_import_list': success_import_list,
        'error_import_list': error_import_list,
        'msg': msg,
        'title': _('Import VoPI Report'),
        })
        return render_to_response(
               'admin/voip_report/voipcall_report/import_voip_report.html',
               context_instance=ctx)

    def export_voip_report(self, request):
        # get the response object, this can be used as a stream.
        response = HttpResponse(mimetype='text/csv')
        # force download.
        response['Content-Disposition'] = 'attachment;filename=export.csv'
        # the csv writer
        writer = csv.writer(response)

        # super(VoIPCall_ReportAdmin, self).queryset(request)
        qs = request.session['voipcall_record_qs']

        writer.writerow(['user', 'callid', 'callerid', 'dnid',
                         'recipient_number', 'starting_date','sessiontime',
                         'sessiontime_real', 'disposition', 'billed',
                         'carrier_cost', 'retail_cost', 'voipplan', 'gateway'])
        for i in qs:
            writer.writerow([i.user,
                             i.callid,
                             i.callerid,
                             i.dnid,
                             i.recipient_number,
                             i.starting_date,
                             i.sessiontime,
                             i.sessiontime_real,
                             get_disposition_name(i.disposition),
                             i.billed,
                             i.carrier_cost,
                             i.retail_cost,
                             i.voipplan,
                             i.gateway,
                             ])
        return response

admin.site.register(VoIPCall_Report, VoIPCall_ReportAdmin)
