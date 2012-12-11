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
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.conf import settings
from django.contrib import messages
from common.common_functions import striplist
from cdr.models import Switch, HangupCause, CDR_TYPE
from cdr.forms import CDR_FileImport, CDR_FIELD_LIST, CDR_FIELD_LIST_NUM
from cdr.functions_def import get_hangupcause_id, get_hangupcause_id_from_name
from cdr.import_cdr_freeswitch_mongodb import apply_index, chk_ipaddress,\
    CDR_COMMON, common_function_to_create_analytic, generate_global_cdr_record
from cdr_alert.functions_blacklist import chk_destination

from pymongo.connection import Connection
from pymongo.errors import ConnectionFailure

import datetime
import csv
import sys


def get_value_from_uni(j, row, field_name):
    """Get value from unique dict list

    >>> j = ['abc', 2, 3]

    >>> field_name = 'abc'

    >>> row = [1, 2, 3]

    >>> get_value_from_uni(j, row, field_name)
    '2'
    """
    if j[0] == field_name:
        return row[j[1] - 1]
    else:
        return ''

"""
Asterisk cdr col

accountcode - 1
caller_id_number - 2
destination_number - 3
duration - 13
billsec - 14
hangup_cause_id - 15
uuid - 4
start_uepoch - 17
"""

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
            (r'^diagnose/$',
             self.admin_site.admin_view(self.diagnose)),
        )
        return my_urls + urls

    def diagnose(self, request):
        opts = Switch._meta
        app_label = opts.app_label

        #loop within the Mongo CDR Import List
        for ipaddress in settings.CDR_BACKEND:

            #Connect to Database
            db_name = settings.CDR_BACKEND[ipaddress]['db_name']
            table_name = settings.CDR_BACKEND[ipaddress]['table_name']
            db_engine = settings.CDR_BACKEND[ipaddress]['db_engine']
            cdr_type = settings.CDR_BACKEND[ipaddress]['cdr_type']
            host = settings.CDR_BACKEND[ipaddress]['host']
            port = settings.CDR_BACKEND[ipaddress]['port']

            if db_engine != 'mongodb' or cdr_type != 'freeswitch':
                messages.error(request, "This function is intended for mongodb and freeswitch")

            data = chk_ipaddress(ipaddress)
            ipaddress = data['ipaddress']
            switch = data['switch']
            collection_data = {}

            #Connect on MongoDB Database
            try:
                connection = Connection(host, port)
                DBCON = connection[db_name]
                messages.success(request, "Connected to MongoDB: %s" % (ipaddress))

                CDR = DBCON[table_name]

                CDR_COMMON = settings.DBCON[settings.MONGO_CDRSTATS['CDR_COMMON']]
                DAILY_ANALYTIC = settings.DBCON[settings.MONGO_CDRSTATS['DAILY_ANALYTIC']]
                MONTHLY_ANALYTIC = settings.DBCON[settings.MONGO_CDRSTATS['MONTHLY_ANALYTIC']]
                CONC_CALL = settings.DBCON[settings.MONGO_CDRSTATS['CONC_CALL']]
                CONC_CALL_AGG = settings.DBCON[settings.MONGO_CDRSTATS['CONC_CALL_AGG']]

                collection_data = {
                    'cdr': CDR.find().count(),
                    'CDR_COMMON': CDR_COMMON.find().count(),
                    'DAILY_ANALYTIC': DAILY_ANALYTIC.find().count(),
                    'MONTHLY_ANALYTIC': MONTHLY_ANALYTIC.find().count(),
                    'CONC_CALL': CONC_CALL.find().count(),
                    'CONC_CALL_AGG': CONC_CALL_AGG.find().count()
                }

            except ConnectionFailure, e:
                messages.error(request,
                    "Please review the 'CDR_BACKEND' Settings in your file /usr/share/cdr-stats/settings_local.py make sure the settings, username, password are correct. Check also that the backend authorize a connection from your server")
                messages.info(request,
                    "After changes in your 'CDR_BACKEND' settings, you will need to restart celery: $ /etc/init.d/newfies-celeryd restart")

        ctx = RequestContext(request, {
            'title': _('Diagnose CDR-Stats'),
            'opts': opts,
            'model_name': opts.object_name.lower(),
            'collection_data': collection_data,
            'app_label': app_label,
            'settings': settings,
        })
        template = 'admin/diagnose.html'
        return render_to_response(template, context_instance=ctx)

    def import_cdr(self, request):
        """Add custom method in django admin view to import CSV file of
        cdr

        **Attributes**:

            * ``form`` - CDR_FileImport
            * ``template`` - admin/cdr/switch/import_cdr.html

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
                uni = [(k, v) for k, v in field_list.iteritems() if countMap[v] == 1]
                uni = sorted(uni, key=lambda uni: uni[1])

                # if order list matched with CDR_FIELD_LIST count
                if len(uni) == len(CDR_FIELD_LIST) - len(field_notin_list):

                    # To count total rows of CSV file
                    records = csv.reader(
                        request.FILES['csv_file'], delimiter=',', quotechar='"')
                    total_rows = len(list(records))

                    rdr = csv.reader(
                        request.FILES['csv_file'], delimiter=',', quotechar='"')
                    cdr_record_count = 0

                    #Store cdr in list to insert by bulk
                    cdr_bulk_record = []
                    local_count_import = 0
                    PAGE_SIZE = 1000

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
                                    caller_id_name = get_value_from_uni(j, row, 'caller_id_name')
                                    caller_id_number = get_value_from_uni(j, row, 'caller_id_number')
                                    direction = get_value_from_uni(j, row, 'direction')
                                    remote_media_ip = get_value_from_uni(j, row, 'remote_media_ip')
                                    answer_uepoch = get_value_from_uni(j, row, 'answer_uepoch')
                                    end_uepoch = get_value_from_uni(j, row, 'end_uepoch')
                                    mduration = get_value_from_uni(j, row, 'mduration')
                                    billmsec = get_value_from_uni(j, row, 'billmsec')
                                    read_codec = get_value_from_uni(j, row, 'read_codec')
                                    write_codec = get_value_from_uni(j, row, 'write_codec')
                                    row_counter = row_counter + 1

                                if len(field_notin_list) != 0:
                                    for i in field_notin_list:
                                        if i == 'accountcode':
                                            accountcode = request.POST[i + "_csv"]

                                if not accountcode:
                                    accountcode = get_cdr_from_row['accountcode']

                                # Mandatory fields to import
                                switch_id = int(request.POST['switch'])
                                caller_id_number = get_cdr_from_row['caller_id_number']
                                duration = int(get_cdr_from_row['duration'])
                                billsec = int(get_cdr_from_row['billsec'])

                                if request.POST.get('import_asterisk') \
                                    and request.POST['import_asterisk'] == 'on':
                                    hangup_cause_name = "_".join(get_cdr_from_row['hangup_cause_id'].upper().split(' '))
                                    hangup_cause_id =\
                                        get_hangupcause_id_from_name(hangup_cause_name)
                                else:
                                    hangup_cause_id =\
                                        get_hangupcause_id(int(get_cdr_from_row['hangup_cause_id']))

                                start_uepoch = \
                                    datetime.datetime.fromtimestamp(int(float(get_cdr_from_row['start_uepoch'])))

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
                                cdr_record = generate_global_cdr_record(switch_id, caller_id_number,
                                    caller_id_name, destination_number, duration, billsec, hangup_cause_id,
                                    accountcode, direction, uuid, remote_media_ip, start_uepoch, answer_uepoch,
                                    end_uepoch, mduration, billmsec, read_codec, write_codec,
                                    'CSV_IMPORT', '', country_id, authorized)

                                # check if cdr is already existing in cdr_common
                                cdr_data = settings.DBCON[settings.MONGO_CDRSTATS['CDR_COMMON']]
                                query_var = {}
                                query_var['uuid'] = uuid
                                record_count = cdr_data.find(query_var).count()

                                if record_count >= 1:
                                    msg = _('CDR already exists !!')
                                    error_import_list.append(row)
                                else:
                                    # if not, insert record
                                    # record global CDR

                                    # Append cdr to bulk_cdr list
                                    cdr_bulk_record.append(cdr_record)

                                    local_count_import = local_count_import + 1
                                    if local_count_import == PAGE_SIZE:
                                        CDR_COMMON.insert(cdr_bulk_record)
                                        local_count_import = 0
                                        cdr_bulk_record = []

                                    date_start_uepoch = get_cdr_from_row['start_uepoch']
                                    common_function_to_create_analytic(date_start_uepoch, start_uepoch,
                                        switch_id, country_id, accountcode, hangup_cause_id, duration)

                                    cdr_record_count = cdr_record_count + 1

                                    msg =\
                                        _('%(cdr_record_count)s Cdr(s) are uploaded, out of %(total_rows)s row(s) !!')\
                                            % {'cdr_record_count': cdr_record_count,
                                               'total_rows': total_rows}
                                    success_import_list.append(row)
                            except:
                                msg = _("Error : invalid value for import")
                                type_error_import_list.append(row)

                    # remaining record
                    if cdr_bulk_record:
                        CDR_COMMON.insert(cdr_bulk_record)
                        local_count_import = 0
                        cdr_bulk_record = []

                    if cdr_record_count > 0:
                        # Apply index
                        apply_index(shell=True)
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
