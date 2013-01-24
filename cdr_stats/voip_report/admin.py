#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2012 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#
from django.contrib import admin
from django.conf.urls import patterns
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.db.models import Sum, Avg, Count
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.views.main import ERROR_FLAG
from django.conf import settings
from django.contrib import messages

from voip_billing.tasks import VoIPbilling
from voip_billing.forms import FileImport
from voip_billing.function_def import check_celeryd_process
from voip_report.models import VoIPCall_Report, VoIPCall
from voip_report.forms import VoipSearchForm, RebillForm
from voip_report.function_def import get_disposition_id, get_disposition_name
from user_profile.models import UserProfile
from common.common_functions import variable_value, ceil_strdate
from datetime import datetime
import csv


def return_query_string(query_string, para):
    """
    Function is used in voipcall_search_admin_form_fun

    >>> return_query_string('key=1', 'key_val=apple')
    'key=1&key_val=apple'
    >>> return_query_string(False, 'key_val=apple')
    'key_val=apple'
    """
    if query_string:
        query_string += '&%s' % (para)
    else:
        query_string = para
    return query_string


def voipcall_search_admin_form_fun(request):
    """Return query string for Voipcall_Report Changelist_view"""
    start_date = ''
    end_date = ''
    if request.POST.get('from_date'):
        start_date = request.POST.get('from_date')

    if request.POST.get('to_date'):
        end_date = request.POST.get('to_date')

    # Assign form field value to local variable
    disposition = variable_value(request, 'status')
    billed = variable_value(request, 'billed')
    query_string = ''

    if start_date and end_date:
        date_string = 'updated_date__gte=' + start_date +\
                      '&updated_date__lte=' + end_date + '+23%3A59%3A59'
        query_string = return_query_string(query_string, date_string)

    if start_date and end_date == '':
        date_string = 'updated_date__gte=' + start_date
        query_string = return_query_string(query_string, date_string)

    if start_date == '' and end_date:
        date_string = 'updated_date__lte=' + end_date
        query_string = return_query_string(query_string, date_string)

    if disposition and disposition != 'all':
        disposition_string = 'disposition__exact=' + disposition
        query_string = return_query_string(query_string,
            disposition_string)

    if billed and billed != 'ALL':
        billed_string = 'billed__exact=' + billed
        query_string = return_query_string(query_string, billed_string)

    return query_string


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
            (r'^rebilling/$',
             self.admin_site.admin_view(self.rebilling)),
        )
        return my_urls + urls

    def changelist_view(self, request, extra_context=None):
        """
        Override changelist_view method of django-admin for search parameters

        **Attributes**:

            * ``form`` - VoipSearchForm
            * ``template`` - admin/dialer_cdr/voipcall/change_list.html

        **Logic Description**:

            * VoIP report Record Listing with search option & Daily Call Report
              search Parameters: by date, by status and by billed.
        """
        opts = VoIPCall_Report._meta
        query_string = ''

        if request.method == 'POST':
            query_string = voipcall_search_admin_form_fun(request)
            return HttpResponseRedirect("/admin/%s/%s/?%s"
                                        % (opts.app_label, opts.object_name.lower(), query_string))
        else:
            status = ''
            tday = datetime.today()
            to_date = from_date = tday.strftime('%Y-%m-%d')
            if request.GET.get('updated_date__gte'):
                from_date = variable_value(request, 'updated_date__gte')
            if request.GET.get('updated_date__lte'):
                to_date = variable_value(request, 'updated_date__lte')[0:10]
            if request.GET.get('disposition__exact'):
                status = variable_value(request, 'disposition__exact')
            if request.GET.get('billed__exact'):
                #TODO: var billed never used
                billed = variable_value(request, 'billed')
            form = VoipSearchForm(initial={'status': status,
                                           'from_date': from_date,
                                           'to_date': to_date})

        ChangeList = self.get_changelist(request)
        try:
            cl = ChangeList(request, self.model, self.list_display,
                self.list_display_links, self.list_filter, self.date_hierarchy,
                self.search_fields, self.list_select_related,
                self.list_per_page, self.list_max_show_all, self.list_editable,
                self)
        except IncorrectLookupParameters:
            if ERROR_FLAG in request.GET.keys():
                return render_to_response('admin/invalid_setup.html',
                    {'title': _('Database error')})
            return HttpResponseRedirect('%s?%s=1' % (request.path, ERROR_FLAG))

        kwargs = {}
        if request.META['QUERY_STRING'] == '':
            tday = datetime.today()
            kwargs['updated_date__gte'] = datetime(tday.year, tday.month, tday.day, 0, 0, 0, 0)
            cl.root_query_set.filter(**kwargs)

        cl.formset = None
        # Session variable get record set with searched option into export file
        request.session['admin_voipcall_record_qs'] = cl.root_query_set

        selection_note_all = ungettext('%(total_count)s selected',
            'All %(total_count)s selected', cl.result_count)

        select_data = {"updated_date": "SUBSTR(CAST(updated_date as CHAR(30)),1,10)"}

        # Get Total Rrecords from VoIPCall Report table for Daily Call Report
        kwargs['billed'] = True
        total_data = VoIPCall_Report.objects.extra(select=select_data)\
            .values('updated_date')\
            .filter(**kwargs).annotate(Count('updated_date'))\
            .annotate(Sum('sessiontime_real'))\
            .annotate(Avg('sessiontime_real'))\
            .annotate(Sum('carrier_cost'))\
            .annotate(Sum('retail_cost')).order_by('-updated_date')

        # Calcualte Profit
        profit = []
        key = 0
        for i in total_data:
            profit.append((key, i['retail_cost__sum'] - i['carrier_cost__sum']))
            key = key + 1

        # Following code will count total voip calls, duration
        # carrier_cost, retail_cost Max profit
        if total_data.count() != 0:
            max_duration = max([x['sessiontime_real__sum'] for x in total_data])
            total_duration = sum([x['sessiontime_real__sum'] for x in total_data])
            total_calls = sum([x['updated_date__count'] for x in total_data])
            total_avg_duration = (sum([x['sessiontime_real__avg'] for x in total_data])) / total_data.count()
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
            'selection_note': _('0 of %(cnt)s selected') % {'cnt': len(cl.result_list)},
            'selection_note_all': selection_note_all % {'total_count': cl.result_count},
            'cl': cl,
            'form': form,
            'opts': opts,
            'model_name': opts.object_name.lower(),
            'app_label': _('VoIP Report'),
            'title': _('VoIP Call Report'),
            'total_data': total_data,
            'total_duration': total_duration,
            'total_calls': total_calls,
            'total_avg_duration': total_avg_duration,
            'total_carrier_cost': total_carrier_cost,
            'total_retail_cost': total_retail_cost,
            'total_profit': total_profit,
            'max_duration': max_duration,
        }
        return super(VoIPCall_ReportAdmin, self).changelist_view(request, extra_context=ctx)

    def import_voip_report(self, request):
        """
        Import CSV file of VoIP Report
        """
        opts = VoIPCall_Report._meta
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
                            voipplan_id = user_voip_plan.voipplan_id
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

                                response = VoIPbilling.delay(voipcall_id=voipcall.id,
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
            'title': _('Import VoIP Report'),
        })
        return render_to_response('admin/voip_report/voipcall_report/import_voip_report.html',
               context_instance=ctx)

    def export_voip_report(self, request):
        # get the response object, this can be used as a stream.
        response = HttpResponse(mimetype='text/csv')
        # force download.
        response['Content-Disposition'] = 'attachment;filename=export.csv'
        # the csv writer
        writer = csv.writer(response)

        # super(VoIPCall_ReportAdmin, self).queryset(request)
        qs = request.session['admin_voipcall_record_qs']

        writer.writerow(['user', 'callid', 'callerid', 'dnid',
                         'recipient_number', 'starting_date', 'sessiontime',
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

    def rebilling(self, request):
        """
        Re-billing successful voip calls
        """
        opts = VoIPCall_Report._meta
        call_rebill_list = []
        if request.method == 'POST':
            form = RebillForm(request.POST)
            if "from_date" in request.POST:
                # From
                from_date = request.POST['from_date']
                start_date = ceil_strdate(from_date, 'start')

            if "to_date" in request.POST:
                # To
                to_date = request.POST['to_date']
                end_date = ceil_strdate(to_date, 'end')

            kwargs = {}
            kwargs['billed'] = True
            if start_date and end_date:
                kwargs['updated_date__range'] = (start_date, end_date)
            if start_date and end_date == '':
                kwargs['updated_date__gte'] = start_date
            if start_date == '' and end_date:
                kwargs['updated_date__lte'] = end_date

            call_rebill_list = VoIPCall_Report.objects.filter(**kwargs).update(billed=False)
            #if call_rebill_list:
            #    for call in call_rebill_list:
            #        # call re-bill
            #        call._bill(call.id, call.voipplan_id)

            #TODO: Update cdr_common buy_cost/sell_cost + daily/monthly aggregate
            daily_query_var = {}
            daily_query_var['metadata.date'] = {'$gte': start_date.strftime('%Y-%m-%d'),
                                                '$lt': end_date.strftime('%Y-%m-%d')}

            daily_data = settings.DBCON[settings.MONGO_CDRSTATS['DAILY_ANALYTIC']]
            daily_data.remove(daily_query_var)

            monthly_query_var = {}
            monthly_query_var['metadata.date'] = {'$gte': start_date.strftime('%Y-%m'),
                                                  '$lt': end_date.strftime('%Y-%m')}

            monthly_data = settings.DBCON[settings.MONGO_CDRSTATS['MONTHLY_ANALYTIC']]
            monthly_data.remove(monthly_query_var)
            msg = _('Re-billing is done')
            messages.info(request, msg)
        else:
            tday = datetime.today()
            to_date = from_date = tday.strftime('%Y-%m-%d')
            form = RebillForm(initial={'from_date': from_date, 'to_date': to_date})

        ctx = RequestContext(request, {
            'form': form,
            'opts': opts,
            'model_name': opts.object_name.lower(),
            'app_label': _('VoIP Report'),
            'title': _('Rebill VoIP Call'),
            'call_rebill_list': call_rebill_list,
        })
        return render_to_response('admin/voip_report/voipcall_report/rebilling.html',
            context_instance=ctx)

admin.site.register(VoIPCall_Report, VoIPCall_ReportAdmin)
