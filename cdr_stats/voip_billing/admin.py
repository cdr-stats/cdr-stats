#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2013 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#
from django import forms
from django.contrib import admin
from django.conf.urls import patterns
from django.utils.translation import ugettext as _
from django.template import RequestContext
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.conf import settings
from django.contrib import messages

from country_dialcode.models import Prefix
from cdr.constants import Export_choice
from voip_billing.models import VoIPRetailRate, VoIPPlan, BanPlan,\
    VoIPPlan_BanPlan, BanPrefix, VoIPRetailPlan, VoIPPlan_VoIPRetailPlan,\
    VoIPCarrierPlan, VoIPCarrierRate, VoIPPlan_VoIPCarrierPlan
from voip_billing.forms import RetailRate_fileImport, CarrierRate_fileImport,\
    Carrier_Rate_fileExport, SimulatorForm, VoIPPlan_fileExport, CustomRateFilterForm,\
    Retail_Rate_fileExport, RebillForm
from voip_billing.constants import CONFIRMATION_TYPE
from voip_billing.widgets import AutocompleteModelAdmin
from voip_billing.function_def import rate_filter_range_field_chk
from voip_billing.rate_engine import rate_engine
from voip_billing.tasks import RebillingTask, ReaggregateTask
from user_profile.models import UserProfile
from django_lets_go.common_functions import variable_value, ceil_strdate
from django_lets_go.app_label_renamer import AppLabelRenamer
from django_lets_go.admin_custom_actions import export_as_csv_action
from mongodb_connection import mongodb
from datetime import datetime
import tablib
import csv

APP_LABEL = _('VoIP Billing')
AppLabelRenamer(native_app_label=u'voip_billing', app_label=APP_LABEL).main()


def prefix_qs():
    """
    Function To get Prefix Query Set with ASCII Order
    """
    if settings.DATABASES['default']['ENGINE'] == 'mysql':
        q = Prefix.objects.extra(
            select={
                'prefix': 'prefix',
                'destination': 'destination',
                'ascii_prefix': 'ASCII(prefix)',
            },
            tables=['dialcode_prefix'])
    else:
        q = Prefix.objects.extra(
            select={
                'prefix': 'prefix',
                'destination': 'destination',
                'ascii_prefix': 'lower(prefix)',
            }, tables=['dialcode_prefix'])
    q.group_by = ['prefix']
    q = q.extra(order_by=['ascii_prefix', 'prefix', 'destination'])
    return q


# TabularInline / StackedInline
class VoIPPlan_VoIPRetailPlanInline(admin.TabularInline):
    model = VoIPPlan_VoIPRetailPlan
    #max_num = 1
    extra = 1
    verbose_name = _('VoIP Plan | VoIP Retail Plan')
    verbose_name_plural = _('VoIP Plan | VoIP Retail Plan')


class VoIPPlan_VoIPCarrierPlanInline(admin.TabularInline):
    model = VoIPPlan_VoIPCarrierPlan
    #max_num = 1
    extra = 1
    verbose_name = _('VoIP Plan | VoIP Carrier Plan')
    verbose_name_plural = _('VoIP Plan | VoIP Carrier Plan')


class VoIPPlan_BanPlanInline(admin.TabularInline):
    model = VoIPPlan_BanPlan
    #max_num = 1
    extra = 1
    verbose_name = _('VoIP Plan | Ban Plan')
    verbose_name_plural = _('VoIP Plan | Ban Plan')


# VoIPPlan
class VoIPPlanAdmin(admin.ModelAdmin):
    fieldsets = (
        (_('VoIP Plan'), {
            #'classes':('collapse', ),
            'fields': ('name', 'pubname', 'lcrtype',),
        }),
    )
    list_display = ('id', 'name', 'lcrtype', 'updated_date',)
    list_display_links = ('name', )
    list_filter = ['lcrtype', 'created_date']
    ordering = ('id', )
    inlines = [
        VoIPPlan_VoIPRetailPlanInline,
        VoIPPlan_VoIPCarrierPlanInline,
        VoIPPlan_BanPlanInline
    ]

    def get_urls(self):
        urls = super(VoIPPlanAdmin, self).get_urls()
        my_urls = patterns('',
            (r'^simulator/$', self.admin_site.admin_view(self.simulator)),
            (r'^export/$', self.admin_site.admin_view(self.export)),
            (r'^rebilling/$', self.admin_site.admin_view(self.rebilling)),
        )
        return my_urls + urls

    def simulator(self, request):
        """
        Admin Simulator
        To view rate according to VoIP Plan & Destination No.
        """
        opts = VoIPPlan._meta

        # Assign form field value to local variable
        destination_no = variable_value(request, "destination_no")
        voipplan_id = variable_value(request, "plan_id")

        data = []
        form = SimulatorForm(request.user, request.POST or None)
        if form.is_valid():
            destination_no = request.POST.get("destination_no")
            voipplan_id = request.POST.get("plan_id")
            query = rate_engine(destination_no=destination_no, voipplan_id=voipplan_id)

            for i in query:
                c_r_plan = VoIPCarrierRate.objects.get(id=i.crid)
                r_r_plan = VoIPRetailRate.objects.get(id=i.rrid)
                data.append((voipplan_id,
                             c_r_plan.voip_carrier_plan_id.id,
                             c_r_plan.voip_carrier_plan_id.name,
                             r_r_plan.voip_retail_plan_id.id,
                             r_r_plan.voip_retail_plan_id.name,
                             i.crid, i.carrier_rate,
                             i.rrid, i.retail_rate, i.rt_prefix))

        ctx = RequestContext(request,
            {
                'title': _('VoIP Simulator'),
                'form': form,
                'opts': opts,
                'model_name': opts.object_name.lower(),
                'app_label': APP_LABEL,
                'data': data,
            })
        return render_to_response('admin/voip_billing/voipplan/simulator.html', context_instance=ctx)

    def export(self, request):
        """
        Export Carrier Rate into CSV file
        """
        opts = VoIPPlan._meta
        form = VoIPPlan_fileExport(request.POST or None, initial={'export_to': Export_choice.CSV})
        if form.is_valid():
            if "plan_id" in request.POST:
                format_type = request.POST.get('export_to')
                response = HttpResponse(mimetype='text/%s' % format_type)
                response['Content-Disposition'] = 'attachment;filename=export_voipplan.%s' % format_type

                voipplan_id = request.POST['plan_id']
                sql_statement = (
                    'SELECT voipbilling_voip_retail_rate.prefix, '
                    'Min(retail_rate) as minrate, dialcode_prefix.destination '
                    'FROM voipbilling_voip_retail_rate '
                    'INNER JOIN voipbilling_voipplan_voipretailplan '
                    'ON voipbilling_voipplan_voipretailplan.voipretailplan_id = '
                    'voipbilling_voip_retail_rate.voip_retail_plan_id '
                    'LEFT JOIN dialcode_prefix ON dialcode_prefix.prefix = '
                    'voipbilling_voip_retail_rate.prefix '
                    'WHERE voipplan_id=%s '
                    'GROUP BY voipbilling_voip_retail_rate.prefix, dialcode_prefix.destination')

                from django.db import connection
                cursor = connection.cursor()
                cursor.execute(sql_statement, [voipplan_id, ])
                row = cursor.fetchall()

                # Content writing in file
                headers = ('prefix', 'rate', 'destination')
                list_val = []
                for record in row:
                    rate = record[1]
                    if format_type == 'json':
                        rate = str(record[1])

                    list_val.append((
                        record[0],
                        rate,
                        record[2],
                    ))
                data = tablib.Dataset(*list_val, headers=headers)
                if format_type == Export_choice.XLS:
                    response.write(data.xls)
                elif format_type == Export_choice.CSV:
                    response.write(data.csv)
                elif format_type == Export_choice.JSON:
                    response.write(data.json)
                return response

        ctx = RequestContext(request, {
            'title': _('Export VoIP Plan'),
            'form': form,
            'opts': opts,
            'model_name': opts.object_name.lower(),
            'app_label': APP_LABEL,
        })
        return render_to_response('admin/voip_billing/voipplan/export.html', context_instance=ctx)

    def rebilling(self, request):
        """
        Re-billing successful voip calls
        """
        opts = VoIPPlan._meta
        # default values for form
        tday = datetime.today()
        to_date = from_date = tday.strftime('%Y-%m-%d')
        form = RebillForm(request.POST or None,
                          initial={'from_date': from_date, 'to_date': to_date,
                                   'confirmation': CONFIRMATION_TYPE.NO})
        call_rebill_count = 0
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

            call_kwargs = {}
            daily_kwargs = {}
            monthly_kwargs = {}
            if start_date and end_date:
                call_kwargs['start_uepoch'] = {'$gte': start_date, '$lt': end_date}

                # get kwargs for aggregate
                daily_kwargs['metadata.date'] = {'$gte': start_date.strftime('%Y-%m-%d'),
                                                 '$lt': end_date.strftime('%Y-%m-%d')}
                monthly_kwargs['metadata.date'] = {'$gte': start_date.strftime('%Y-%m'),
                                                   '$lt': end_date.strftime('%Y-%m')}

            user_profile = UserProfile.objects.get(user=request.user)
            if not request.user.is_superuser:  # not superuser
                call_kwargs['accountcode'] = user_profile.accountcode
                monthly_kwargs['metadata.accountcode'] =\
                    daily_kwargs['metadata.accountcode'] = call_kwargs['accountcode']

            # Get total no of calls which are going to rebill
            call_rebill_count = mongodb.cdr_common.find(call_kwargs).count()

            if "confirmation" in request.POST:
                confirmation = request.POST.get('confirmation')
                # To confirm re-billing
                if confirmation == CONFIRMATION_TYPE.NO:
                    request.POST['confirmation'] = CONFIRMATION_TYPE.YES
                    form.fields['from_date'].widget = form.fields['to_date'].widget = forms.HiddenInput()
                    ctx = RequestContext(request, {
                        'form': form,
                        'start_date': start_date,
                        'end_date': end_date,
                        'opts': opts,
                        'model_name': opts.object_name.lower(),
                        'app_label': APP_LABEL,
                        'title': _('Rebill VoPI Call'),
                        'call_rebill_count': call_rebill_count,
                        'CONFIRMATION_TYPE': CONFIRMATION_TYPE,
                    })
                    return render_to_response('admin/voip_billing/voipplan/rebilling.html', context_instance=ctx)

                voipplan_id = user_profile.voipplan_id

                # re-billing is confirmed by user
                if confirmation == CONFIRMATION_TYPE.YES:
                    if call_rebill_count != 0:
                        # Rebill all calls
                        RebillingTask.delay(call_kwargs, voipplan_id)

                        # Re-aggregate calls to re-generate daily/monthly analytics
                        ReaggregateTask.delay(daily_kwargs, monthly_kwargs, call_kwargs)

                    msg = _('Re-billing is done')
                    messages.info(request, msg)
                    request.POST['confirmation'] = CONFIRMATION_TYPE.NO
                    call_rebill_count = 0

        ctx = RequestContext(request, {
            'form': form,
            'opts': opts,
            'model_name': opts.object_name.lower(),
            'app_label': APP_LABEL,
            'title': _('Rebill VoIP Call'),
            'call_rebill_count': call_rebill_count,
        })
        return render_to_response('admin/voip_billing/voipplan/rebilling.html', context_instance=ctx)

admin.site.register(VoIPPlan, VoIPPlanAdmin)


#BanPlan
class BanPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_date', 'updated_date')
    list_display_links = ('name', )

admin.site.register(BanPlan, BanPlanAdmin)


#BanPrefix
class BanPrefixAdmin(AutocompleteModelAdmin):
    list_display = ('prefix_with_name', 'ban_plan', 'updated_date')
    list_display_links = ('prefix_with_name', )
    list_filter = ['ban_plan']
    related_search_fields = {
        'prefix': ('prefix', 'destination'),
    }

    def get_urls(self):
        urls = super(BanPrefixAdmin, self).get_urls()
        my_urls = patterns('',
            (r'^search/$', self.admin_site.admin_view(self.search)),
        )
        return my_urls + urls

admin.site.register(BanPrefix, BanPrefixAdmin)


#VoIPRetailPlan
class VoIPRetailPlanAdmin(admin.ModelAdmin):
    fieldsets = (
        (_('VoIP Retail Plan'), {
            #'classes': ('collapse', ),
            'fields': ('name', 'description', 'metric',),
        }),
    )
    list_display = ('id', 'name', 'description', 'metric', 'updated_date',)
    list_display_links = ('name',)
    ordering = ('id',)
    list_filter = ['metric', 'name']
    inlines = [
        VoIPPlan_VoIPRetailPlanInline,
    ]

admin.site.register(VoIPRetailPlan, VoIPRetailPlanAdmin)


#VoIPRetailRate
class VoIPRetailRateAdmin(AutocompleteModelAdmin):
    fieldsets = (
        (_('VoIP Retail Rate'), {
            #'classes':('collapse', ),
            'fields': ('voip_retail_plan_id', 'prefix', 'retail_rate'),
        }),
    )
    list_display = ('id', 'voip_retail_plan_name', 'prefix_with_name',
                    'retail_rate', 'updated_date',)
    list_display_links = ('id',)
    list_editable = ['retail_rate']
    list_filter = ['updated_date', 'voip_retail_plan_id', 'prefix']
    search_fields = ('retail_rate',)
    valid_lookups = ('updated_date', 'voip_retail_plan_id', 'prefix')
    related_search_fields = {
        'prefix': ('prefix', 'destination'),
    }
    actions = [export_as_csv_action("Export selected retail rates as CSV file",
               fields=['voip_retail_plan_id', 'prefix', 'retail_rate'],
               header=False)]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Override Foreign Key Query set on Add/Edit admin-page of Retail Rate
        """
        if db_field.name == "prefix":
            kwargs["queryset"] = prefix_qs()
        return super(VoIPRetailRateAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)

    def get_urls(self):
        urls = super(VoIPRetailRateAdmin, self).get_urls()
        my_urls = patterns('',
            (r'^$', self.admin_site.admin_view(self.changelist_view)),
            (r'^import_rr/$', self.admin_site.admin_view(self.import_rr)),
            (r'^export_rr/$', self.admin_site.admin_view(self.export_rr)),
            (r'^search/$', self.admin_site.admin_view(self.search)),
        )
        return my_urls + urls

    def queryset(self, request):
        """
        Queryset will be changed as per the Rate filter selection
        on changelist_view
        """
        # Assign form field value to local variable
        rate = variable_value(request, 'rate')
        rate_range = variable_value(request, 'rate_range')

        kwargs = rate_filter_range_field_chk(rate, rate_range, "retail_rate")
        qs = super(VoIPRetailRateAdmin, self).queryset(request)

        if kwargs != '':
            return qs.filter(**kwargs).order_by('retail_rate')
        else:
            return qs.filter(**kwargs)

    def changelist_view(self, request, extra_context=None):
        """
        VoIP Retail Rate Listing & Custom Rate Filter (>,>=,=,<=,<)
        """
        form = CustomRateFilterForm(request.POST or None)
        ctx = {
            'title': _('Select VoIP Retail Rate to Change'),
            'form': form,
        }
        return super(VoIPRetailRateAdmin, self).changelist_view(request, extra_context=ctx)

    def export_rr(self, request):
        """
        Export Retail Rate into CSV file
        """
        opts = VoIPRetailRate._meta
        form = Retail_Rate_fileExport(request.POST or None,
                                      initial={'export_to': Export_choice.CSV})

        if form.is_valid():
            format_type = request.POST.get('export_to')
            response = HttpResponse(mimetype='text/%s' % format_type)
            response['Content-Disposition'] = 'attachment;filename=export_retail_rate.%s' % format_type
            qs = VoIPRetailRate.objects.values('prefix', 'retail_rate').filter(voip_retail_plan_id=request.POST['plan_id'])

            # Content writing in file
            headers = ('prefix', 'rate')
            list_val = []
            for row in qs:
                rate = row['retail_rate']
                if format_type == 'json':
                    rate = str(row['retail_rate'])

                list_val.append((row['prefix'], rate))

            data = tablib.Dataset(*list_val, headers=headers)
            if format_type == Export_choice.XLS:
                response.write(data.xls)
            elif format_type == Export_choice.CSV:
                response.write(data.csv)
            elif format_type == Export_choice.JSON:
                response.write(data.json)
            return response

        ctx = RequestContext(request, {
            'title': _('Export Retail Rate'),
            'form': form,
            'opts': opts,
            'model_name': opts.object_name.lower(),
            'app_label': APP_LABEL,
        })
        return render_to_response('admin/voip_billing/voipretailrate/export_rr.html', context_instance=ctx)

    def import_rr(self, request):
        """
        Import CSV file of Retail Rate

        Note :-

        total_rows - Total no. of records of CSV file
        retail_record_count - No. of records which are imported from CSV file
        """
        opts = VoIPRetailRate._meta
        form = RetailRate_fileImport(request.POST or None, request.FILES or None)
        rdr = ''  # will contain CSV data
        msg = ''
        success_import_list = []
        error_import_list = []
        type_error_import_list = []

        if form.is_valid():
            # col_no - field name
            #  0     - Prefix
            #  1     - Retail Rate
            # To count total rows of CSV file
            records = csv.reader(request.FILES['csv_file'], delimiter=',', quotechar='"')
            total_rows = len(list(records))

            rdr = csv.reader(request.FILES['csv_file'], delimiter=',', quotechar='"')
            retail_record_count = 0
            # Read each Row
            for row in rdr:
                if (row and str(row[0]) > 0):
                    try:
                        # check field type
                        int(row[0])
                        float(row[1])

                        # Check row[0] available or not in Prefix table
                        pfix = Prefix.objects.get(prefix=row[0])
                        if pfix is not None:
                            voip_retail_plan = VoIPRetailPlan.objects.get(
                                pk=request.POST['plan_id'])
                            try:
                                # check if prefix is already
                                # exist with retail plan or not
                                VoIPRetailRate.objects.get(
                                    voip_retail_plan_id=voip_retail_plan,
                                    prefix=pfix)
                                msg = _('Retail Rate(s) are already exist !!')
                                error_import_list.append(row)
                            except:
                                # if not, insert record
                                VoIPRetailRate.objects.create(
                                    voip_retail_plan_id=voip_retail_plan,
                                    prefix=pfix,
                                    retail_rate=row[1])
                                retail_record_count = retail_record_count + 1
                                msg = '%d Retail Rate(s) are uploaded successfully out of %d row(s) !!'\
                                      % (retail_record_count, total_rows)
                                success_import_list.append(row)
                        else:
                            msg = _('Error: Prefix is not in the Prefix table')
                    except:
                        msg = _("Error : invalid value for import! Please look at the import samples.")
                        type_error_import_list.append(row)

        ctx = RequestContext(request, {
            'title': _('Import Retail Rate'),
            'form': form,
            'opts': opts,
            'model_name': opts.object_name.lower(),
            'app_label': APP_LABEL,
            'rdr': rdr,
            'msg': msg,
            'success_import_list': success_import_list,
            'error_import_list': error_import_list,
            'type_error_import_list': type_error_import_list,
        })
        return render_to_response('admin/voip_billing/voipretailrate/import_rr.html', context_instance=ctx)
admin.site.register(VoIPRetailRate, VoIPRetailRateAdmin)


#VoIPCarrierPlan
class VoIPCarrierPlanAdmin(admin.ModelAdmin):
    fieldsets = (
        (_('VoIP Carrier Plan'), {
            #'classes':('collapse', ),
            'fields': ('name', 'description', 'metric',
                       'voip_provider_id'),
        }),
    )
    list_display = ('id', 'name', 'metric', 'voip_provider_id', 'callsent', 'updated_date')
    list_display_links = ('name',)
    list_filter = ['name', 'updated_date']
    ordering = ('id',)
    inlines = [
        VoIPPlan_VoIPCarrierPlanInline,
    ]

    def get_readonly_fields(self, request, obj=None):
        if obj:  # In edit mode
            return ('callsent',) + self.readonly_fields
        return self.readonly_fields

admin.site.register(VoIPCarrierPlan, VoIPCarrierPlanAdmin)


#VoIPCarrierRate
class VoIPCarrierRateAdmin(AutocompleteModelAdmin):
    fieldsets = (
        (_('VoIP Carrier Rate'), {
            #'classes': ('collapse', ),
            'fields': ('voip_carrier_plan_id', 'prefix', 'carrier_rate',),
        }),
    )
    list_display = ('id', 'voip_carrier_plan_name', 'prefix_with_name',
                    'carrier_rate', 'updated_date',)
    list_display_links = ('id', )
    list_filter = ['updated_date', 'voip_carrier_plan_id', 'prefix']
    list_editable = ['carrier_rate']
    search_fields = ('carrier_rate',)
    valid_lookups = ('updated_date', 'voip_carrier_plan_id', 'prefix')
    related_search_fields = {
        'prefix': ('prefix', 'destination'),
    }
    actions = [export_as_csv_action("Export selected carrier rates as CSV file",
        fields=['voip_carrier_plan_id', 'prefix', 'carrier_rate'],
        header=False)]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Override Foreign Key Query set on Add/Edit admin-page of Carrier Rate
        """
        if db_field.name == "prefix":
            kwargs["queryset"] = prefix_qs()
        return super(VoIPCarrierRateAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def get_urls(self):
        urls = super(VoIPCarrierRateAdmin, self).get_urls()
        my_urls = patterns('',
            (r'^$', self.admin_site.admin_view(self.changelist_view)),
            (r'^import_cr/$', self.admin_site.admin_view(self.import_cr)),
            (r'^export_cr/$', self.admin_site.admin_view(self.export_cr)),
            (r'^search/$', self.admin_site.admin_view(self.search)),
        )
        return my_urls + urls

    def queryset(self, request):
        """
        Queryset will be changed as per the Custom Rate Filter selection
        on changelist_view
        """
        kwargs = {}

        # Assign form field value to local variable
        rate = variable_value(request, 'rate')
        rate_range = variable_value(request, 'rate_range')

        kwargs = rate_filter_range_field_chk(rate, rate_range, "carrier_rate")
        qs = super(VoIPCarrierRateAdmin, self).queryset(request)
        if kwargs is not None:
            return qs.filter(**kwargs).order_by('carrier_rate')
        else:
            return qs.filter(**kwargs)

    def changelist_view(self, request, extra_context=None):
        """
        VoIP Carrier Rate Listing & Custom Rate Filter (>,>=,=,<=,<)
        """
        form = CustomRateFilterForm(request.POST or None)
        ctx = {
            'title': _('Select VoIP Carrier Rate to Change'),
            'form': form,
        }
        return super(VoIPCarrierRateAdmin, self).changelist_view(request, extra_context=ctx)

    def export_cr(self, request):
        """
        Export Carrier Rate into CSV file
        """
        opts = VoIPCarrierRate._meta
        form = Carrier_Rate_fileExport(request.POST or None, initial={'export_to': Export_choice.CSV})
        if form.is_valid():
            format_type = request.POST.get('export_to')
            response = HttpResponse(mimetype='text/%s' % format_type)
            response['Content-Disposition'] = 'attachment;filename=export_carrier_rate.%s' % format

            qs = VoIPCarrierRate.objects.values('prefix', 'carrier_rate').filter(
                voip_carrier_plan_id=request.POST['plan_id'])

            # Content writing in file
            headers = ('prefix', 'rate')
            list_val = []
            for row in qs:
                rate = row['carrier_rate']
                if format_type == 'json':
                    rate = str(row['carrier_rate'])
                list_val.append((row['prefix'], rate))

            data = tablib.Dataset(*list_val, headers=headers)
            if format_type == Export_choice.XLS:
                response.write(data.xls)
            elif format_type == Export_choice.CSV:
                response.write(data.csv)
            elif format_type == Export_choice.JSON:
                response.write(data.json)
            return response

        ctx = RequestContext(request, {
            'title': _('Export Carrier Rate'),
            'form': form,
            'opts': opts,
            'model_name': opts.object_name.lower(),
            'app_label': APP_LABEL,
        })
        return render_to_response('admin/voip_billing/voipcarrierrate/export_cr.html', context_instance=ctx)

    def import_cr(self, request):
        """
        Import CSV file of Carrier Rate

        Note :-

        total_rows - Total no. of records of CSV file
        carrier_record_count- No. of records which are imported from CSV file
        retail_record_count - No. of records which are calculated based on the
                              profit(%) & carrier rates
        """
        opts = VoIPCarrierRate._meta
        form = CarrierRate_fileImport(request.POST or None, request.FILES or None)
        rdr = ''  # will contain CSV data
        msg = ''
        cr_success_import_list = []
        rr_success_import_list = []
        cr_error_import_list = []
        rr_error_import_list = []
        type_error_import_list = []

        if form.is_valid():
            # Checked form field - "chk" - check_box value
            if "chk" in request.POST:
                if request.POST['chk'] == "on":
                    profit_per = request.POST['profit_percentage']
                    voip_retail_plan = VoIPRetailPlan.objects.get(pk=request.POST['retail_plan_id'])

            # col_no - field name
            #  0     - Prefix
            #  1     - Carrier Rate
            # Total no of records in CSV file
            records = csv.reader(request.FILES['csv_file'], delimiter=',', quotechar='"')
            total_rows = len(list(records))

            rdr = csv.reader(request.FILES['csv_file'], delimiter=',', quotechar='"')
            carrier_record_count = 0
            retail_record_count = 0

            # To count total rows of CSV file
            for row in rdr:
                if (row and row[0] > 0):
                    try:
                        # check field type
                        int(row[0])
                        float(row[1])

                        pfix = Prefix.objects.get(prefix=row[0])
                        if pfix is not None:
                            voip_carrier_plan = VoIPCarrierPlan.objects.get(
                                pk=request.POST['plan_id'])
                            try:
                                # check if prefix is alredy exist with
                                # retail plan or not
                                VoIPCarrierRate.objects.get(
                                    voip_carrier_plan_id=voip_carrier_plan,
                                    prefix=pfix)

                                msg = _('Carrier Rates are already exist !!')
                                cr_error_import_list.append(row)

                                # Checked form field - "chk"\
                                # - check_box value
                                if "chk" in request.POST:
                                    if request.POST['chk'] == "on":
                                        VoIPRetailRate.objects.get(
                                            voip_retail_plan_id=voip_retail_plan,
                                            prefix=pfix)
                                        msg = _('Carrier/Retail Rates are already exist !!')
                                        rr_error_import_list.append(row)
                            except:
                                # if not, insert record
                                VoIPCarrierRate.objects.create(
                                    voip_carrier_plan_id=voip_carrier_plan,
                                    prefix=pfix, carrier_rate=row[1])
                                carrier_record_count = carrier_record_count + 1

                                msg = '%d Carrier Rate(s) are uploaded \
                                       successfully out of %d row(s)!!' \
                                       % (carrier_record_count, total_rows)
                                cr_success_import_list.append(row)

                                # Checked form field - "chk"
                                # - check_box value
                                if "chk" in request.POST:
                                    if request.POST['chk'] == "on":

                                        # Calculate New Retail Rate
                                        new_rate = (float(row[1]) * (float(profit_per) / 100) + float(row[1]))

                                        VoIPRetailRate.objects.create(
                                            voip_retail_plan_id=voip_retail_plan,
                                            prefix=pfix,
                                            retail_rate=str(new_rate))

                                        retail_record_count = retail_record_count + 1
                                        msg = '%d Carrier Rate(s) are \
                                              uploaded successfully with  \
                                              %d Retail Rate(s) \
                                              out of %d row(s) !!' % \
                                              (carrier_record_count,
                                               retail_record_count,
                                               total_rows)
                                        rr_success_import_list.append((row[0], str(new_rate)))
                        else:
                            msg = _('Error: Prefix is not in the Prfix table')
                    except:
                        msg = _("Error : invalid value for import! \
                               Please look at the import samples.")
                        type_error_import_list.append(row)

        ctx = RequestContext(request, {
            'title': _('Import Carrier Rate'),
            'form': form,
            'opts': opts,
            'model_name': opts.object_name.lower(),
            'app_label': APP_LABEL,
            'rdr': rdr,
            'msg': msg,
            'cr_success_import_list': cr_success_import_list,
            'cr_error_import_list': cr_error_import_list,
            'rr_success_import_list': rr_success_import_list,
            'rr_error_import_list': rr_error_import_list,
            'type_error_import_list': type_error_import_list,
        })
        return render_to_response('admin/voip_billing/voipcarrierrate/import_cr.html', context_instance=ctx)
admin.site.register(VoIPCarrierRate, VoIPCarrierRateAdmin)
