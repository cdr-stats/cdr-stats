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
from django.conf.urls.defaults import patterns
from django.utils.translation import ugettext as _

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.conf import settings
from common.common_functions import striplist

from cdr.models import Switch, HangupCause
from cdr.forms import CDR_FileImport, CDR_FIELD_LIST, CDR_FIELD_LIST_NUM
from cdr.functions_def import get_hangupcause_id
from cdr.import_cdr_freeswitch_mongodb import apply_index,\
                                              CDR_COMMON,\
                                              DAILY_ANALYTIC,\
                                              MONTHLY_ANALYTIC,\
                                              create_daily_analytic,\
                                              create_monthly_analytic

from cdr_alert.functions_blacklist import chk_destination

import datetime
import csv


def get_value_from_uni(j, row, field_name):
    """Get value from unique dict list"""
    if j[0] == field_name:
        return row[j[1] - 1]
    else:
        return ''

# Switch
class SwitchAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'ipaddress', 'key_uuid')
    list_filter = ['name', 'ipaddress']
    search_fields = ('name', 'ipaddress',)

    def get_urls(self):
        urls = super(SwitchAdmin, self).get_urls()
        my_urls = patterns('',
            (r'^import_cdr/$',
             self.admin_site.admin_view(self.import_cdr)),
        )
        return my_urls + urls

    def import_cdr(self, request):
        """Add custom method in django admin view to import CSV file of
        cdr

        **Attributes**:

            * ``form`` - CDR_FileImport
            * ``template`` - admin/cdr/switch/import_contact.html

        **Logic Description**:


        **Important variable**:

            * total_rows - Total no. of records in the CSV file
            * retail_record_count - No. of records which are imported from
              The CSV file
        """
        opts = Switch._meta
        app_label = opts.app_label
        rdr = ''  # will contain CSV data
        msg = ''
        success_import_list = []
        error_import_list = []
        type_error_import_list = []

        #TODO : Too many indentation in the code, refact, less if, for

        #TODO : respect DRY principale, some of the code is duplicate
        #from import tasks

        if request.method == 'POST':
            form = CDR_FileImport(request.user, request.POST, request.FILES)

            if form.is_valid():

                field_list = {}
                field_notin_list = []
                for i in CDR_FIELD_LIST:
                    if int(request.POST[i]) != 0:
                        field_list[i] = int(request.POST[i])
                    else:
                        field_notin_list.append((i))

                # perform sorting & get unique order list
                countMap = {}
                for v in field_list.itervalues():
                    countMap[v] = countMap.get(v, 0) + 1
                uni = [(k, v) for k, v in field_list.iteritems() \
                            if countMap[v] == 1]
                uni = sorted(uni, key=lambda uni: uni[1])

                # if order list matched with CDR_FIELD_LIST count
                if len(uni) == len(CDR_FIELD_LIST) - len(field_notin_list):

                    # To count total rows of CSV file
                    records = csv.reader(request.FILES['csv_file'],
                                         delimiter=',', quotechar='"')
                    total_rows = len(list(records))

                    rdr = csv.reader(request.FILES['csv_file'],
                                     delimiter=',', quotechar='"')
                    cdr_record_count = 0

                    # Read each Row
                    for row in rdr:
                        if (row and str(row[0]) > 0):
                            row = striplist(row)
                            try:
                                accountcode = ''
                                # extra fields to import
                                caller_id_name = ''
                                direction = 'outbound'
                                remote_media_ip = ''
                                answer_uepoch = ''
                                end_uepoch = ''
                                mduration = ''
                                billmsec = ''
                                write_codec = ''
                                read_codec = ''
                                get_cdr_from_row = {}
                                row_counter = 0
                                for j in uni:
                                    get_cdr_from_row[j[0]] = row[j[1] - 1]
                                    #get_cdr_from_row[j[0]] = row[row_counter]
                                    caller_id_name = \
                                        get_value_from_uni(j, row, 'caller_id_name')
                                    caller_id_number = \
                                        get_value_from_uni(j, row, 'caller_id_number')
                                    direction = \
                                        get_value_from_uni(j, row, 'direction')
                                    remote_media_ip = \
                                        get_value_from_uni(j, row, 'remote_media_ip')
                                    answer_uepoch = \
                                        get_value_from_uni(j, row, 'answer_uepoch')
                                    end_uepoch = \
                                        get_value_from_uni(j, row, 'end_uepoch')
                                    mduration = \
                                        get_value_from_uni(j, row, 'mduration')
                                    billmsec = \
                                        get_value_from_uni(j, row, 'billmsec')
                                    read_codec = \
                                        get_value_from_uni(j, row, 'read_codec')
                                    write_codec = \
                                        get_value_from_uni(j, row, 'write_codec')

                                    row_counter = row_counter + 1

                                if len(field_notin_list) != 0:
                                    for i in field_notin_list:
                                        if i == 'accountcode':
                                            accountcode = int(request.POST[i + "_csv"])

                                if not accountcode:
                                    accountcode = int(get_cdr_from_row['accountcode'])


                                # Mandatory fields to import
                                switch_id = int(request.POST['switch'])
                                caller_id_number = get_cdr_from_row['caller_id_number']
                                duration = int(get_cdr_from_row['duration'])
                                billsec = int(get_cdr_from_row['billsec'])
                                hangup_cause_id = \
                                    get_hangupcause_id(int(get_cdr_from_row['hangup_cause_id']))
                                start_uepoch = \
                                    datetime.datetime.fromtimestamp(int(get_cdr_from_row['start_uepoch']))
                                destination_number = get_cdr_from_row['destination_number']
                                uuid = get_cdr_from_row['uuid']

                                destination_data = chk_destination(destination_number)
                                authorized = destination_data['authorized']
                                country_id = destination_data['country_id']

                                # Extra fields to import
                                if answer_uepoch:
                                    answer_uepoch = \
                                        datetime.datetime.fromtimestamp(int(answer_uepoch[:10]))
                                if end_uepoch:
                                    end_uepoch = \
                                        datetime.datetime.fromtimestamp(int(end_uepoch[:10]))

                                # Prepare global CDR
                                cdr_record = {
                                    'switch_id': int(request.POST['switch']),
                                    'caller_id_number': caller_id_number,
                                    'caller_id_name': caller_id_name,
                                    'destination_number': destination_number,
                                    'duration': duration,
                                    'billsec': billsec,
                                    'hangup_cause_id': hangup_cause_id,
                                    'accountcode': accountcode,
                                    'direction': direction,
                                    'uuid': uuid,
                                    'remote_media_ip': remote_media_ip,
                                    'start_uepoch': start_uepoch,
                                    'answer_uepoch': answer_uepoch,
                                    'end_uepoch': end_uepoch,
                                    'mduration': mduration,
                                    'billmsec': billmsec,
                                    'read_codec': read_codec,
                                    'write_codec': write_codec,
                                    'cdr_type': 'CSV_IMPORT',
                                    'cdr_object_id': '',
                                    'country_id': country_id,
                                    'authorized': authorized,
                                    }

                                try:
                                    # check if cdr is already existing in cdr_common
                                    cdr_data = settings.DBCON[settings.MG_CDR_COMMON]
                                    query_var = {}
                                    query_var['uuid'] = uuid
                                    record_count = cdr_data.find(query_var).count()
                                    if record_count >= 1:
                                        msg = _('CDR already exists !!')
                                        error_import_list.append(row)
                                    else:
                                        # if not, insert record
                                        # record global CDR
                                        CDR_COMMON.insert(cdr_record)

                                        # start_uepoch = get_cdr_from_row['start_uepoch']
                                        daily_date = datetime.datetime.\
                                            fromtimestamp(int(get_cdr_from_row['start_uepoch'][:10]))

                                        # insert daily analytic record
                                        create_daily_analytic(daily_date, switch.id, country_id,
                                                              accountcode, hangup_cause_id,
                                                              duration)

                                        # MONTHLY_ANALYTIC
                                        # insert monthly analytic record
                                        create_monthly_analytic(daily_date, start_uepoch, switch.id,
                                                                country_id, accountcode, duration)

                                        cdr_record_count = cdr_record_count + 1

                                        msg =\
                                        _('%(cdr_record_count)s Cdr(s) are uploaded, out of %(total_rows)s row(s) !!')\
                                        % {'cdr_record_count': cdr_record_count,
                                           'total_rows': total_rows}
                                        success_import_list.append(row)
                                except:
                                    msg = _("Error : invalid value for import")
                                    type_error_import_list.append(row)

                            except:
                                msg = _("Error : invalid value for import")
                                type_error_import_list.append(row)

                    if cdr_record_count > 0:
                        apply_index()
                        # Apply index
                        DAILY_ANALYTIC.ensure_index([("metadata.date", -1)])
                        CDR_COMMON.ensure_index([("start_uepoch", -1)])
                else:
                    msg = _("Error : importing several times the same column")
        else:
            form = CDR_FileImport(request.user)

        ctx = RequestContext(request, {
            'title': _('Import CDR'),
            'form': form,
            'opts': opts,
            'model_name': opts.object_name.lower(),
            'app_label': app_label,
            'rdr': rdr,
            'msg': msg,
            'success_import_list': success_import_list,
            'error_import_list': error_import_list,
            'type_error_import_list': type_error_import_list,
            'CDR_FIELD_LIST': list(CDR_FIELD_LIST),
            'CDR_FIELD_LIST_NUM': list(CDR_FIELD_LIST_NUM),
            })
        template = 'admin/cdr/switch/import_cdr.html'
        return render_to_response(template, context_instance=ctx)

admin.site.register(Switch, SwitchAdmin)


# HangupCause
class HangupCauseAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'enumeration', 'cause', 'description')
    search_fields = ('code', 'enumeration',)

admin.site.register(HangupCause, HangupCauseAdmin)
