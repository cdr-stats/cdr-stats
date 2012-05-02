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
from django.contrib import messages
from django.conf.urls.defaults import *
from django.utils.translation import ugettext as _
from django.db.models import *
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
from django.conf import settings

from pymongo.connection import Connection
from pymongo.errors import ConnectionFailure

from cdr.models import *
from cdr.forms import *
from cdr_alert.models import Blacklist, Whitelist
from cdr_alert.tasks import blacklist_whitelist_notification
from country_dialcode.models import Prefix
from common.common_functions import striplist

from random import choice
from uuid import uuid1
from datetime import *
import calendar
import time
import sys
import random
import json, ast
import re
import csv


# Switch
class SwitchAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'ipaddress', 'key_uuid')
    list_filter = ['name', 'ipaddress',]
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
        file_exts = ('.csv', )
        rdr = ''  # will contain CSV data
        msg = ''
        success_import_list = []
        error_import_list = []
        type_error_import_list = []
        if request.method == 'POST':
            form = CDR_FileImport(request.user, request.POST, request.FILES)
            if form.is_valid():
                #print request.POST
                cdr_field_list = {}
                for i in CDR_FIELD_LIST:
                    cdr_field_list[i] = int(request.POST[i])

                #print sorted(cdr_field_list, key=lambda key: cdr_field_list[key])
                #print sorted(cdr_field_list, key=cdr_field_list.get)
                countMap = {}
                for v in cdr_field_list.itervalues():
                    countMap[v] = countMap.get(v, 0) + 1
                uni = [ (k, v) for k, v in cdr_field_list.iteritems() if countMap[v] == 1]
                uni = sorted(uni, key=lambda uni: uni[1])
                if len(uni) == len(CDR_FIELD_LIST):
                    print "start import"
                    #print uni
                    # col_no - field name
                    #  0     - caller_id_number
                    #  1     - caller_id_name
                    #  2     - destination_number
                    #  3     - duration
                    #  4     - billsec
                    #  5     - hangup_cause_id
                    #  6     - direction
                    #  7     - uuid
                    #  8     - remote_media_ip
                    #  9     - start_uepoch
                    #  10    - answer_uepoch
                    #  11    - end_uepoch
                    #  12    - mduration
                    #  13    - billmsec
                    #  14    - read_codec
                    #  15    - write_codec
                    # To count total rows of CSV file
                    records = csv.reader(request.FILES['csv_file'],
                                         delimiter=',', quotechar='"')
                    total_rows = len(list(records))

                    rdr = csv.reader(request.FILES['csv_file'],
                                     delimiter=',', quotechar='"')
                    contact_record_count = 0
                    # Read each Row
                    for row in rdr:
                        if (row and str(row[0]) > 0):
                            row = striplist(row)
                            try:
                                get_cdr_from_row = {}
                                row_counter = 0
                                for j in uni:
                                    get_cdr_from_row[j[0]] = row[row_counter]
                                    row_counter = row_counter + 1

                                start_uepoch = datetime.fromtimestamp(int(get_cdr_from_row['start_uepoch'][:10]))
                                answer_uepoch = datetime.fromtimestamp(int(get_cdr_from_row['end_uepoch'][:10]))
                                end_uepoch = datetime.fromtimestamp(int(get_cdr_from_row['end_uepoch'][:10]))

                                # Check Destination number
                                destination_number = get_cdr_from_row['destination_number']

                                # number startswith 0 or `+` sign
                                #remove leading +
                                sanitized_destination = re.sub("^\++","",destination_number)
                                #remove leading 011
                                sanitized_destination = re.sub("^011+","",sanitized_destination)
                                #remove leading 00
                                sanitized_destination = re.sub("^0+","",sanitized_destination)

                                prefix_list = prefix_list_string(sanitized_destination)

                                authorized = 1 # default
                                #check desti against whiltelist
                                authorized = chk_prefix_in_whitelist(prefix_list)
                                if authorized:
                                    authorized = 1 # allowed destination
                                else:
                                    #check desti against blacklist
                                    authorized = chk_prefix_in_blacklist(prefix_list)
                                    if not authorized:
                                        authorized = 0 # not allowed destination

                                country_id = get_country_id(prefix_list)

                                #print get_cdr_from_row
                                """
                                # Prepare global CDR
                                cdr_record = {
                                    'switch_id': switch.id,
                                    'caller_id_number': get_cdr_from_row['caller_id_number'],
                                    'caller_id_name': get_cdr_from_row['caller_id_name'],
                                    'destination_number': get_cdr_from_row['destination_number'],
                                    'duration': int(get_cdr_from_row['destination_number']),
                                    'billsec': int(get_cdr_from_row['destination_number']),
                                    'hangup_cause_id': get_hangupcause_id(get_cdr_from_row['destination_number']),
                                    'accountcode': get_cdr_from_row['destination_number'],
                                    'direction': get_cdr_from_row['destination_number'],
                                    'uuid': get_cdr_from_row['destination_number'],
                                    'remote_media_ip': get_cdr_from_row['destination_number'],
                                    'start_uepoch': get_cdr_from_row['destination_number'],
                                    'answer_uepoch': get_cdr_from_row['destination_number'],
                                    'end_uepoch': get_cdr_from_row['destination_number'],
                                    'mduration': get_cdr_from_row['destination_number'],
                                    'billmsec': get_cdr_from_row['destination_number'],
                                    'read_codec': get_cdr_from_row['destination_number'],
                                    'write_codec': get_cdr_from_row['destination_number'],
                                    'cdr_type': ,
                                    'cdr_object_id': ,
                                    'country_id': ,
                                    'authorized': ,
                                    }
                                """


                                try:
                                    # check if prefix is already
                                    # existing in the retail plan or not

                                    msg = _('CDR already exists !!')
                                    error_import_list.append(row)
                                except:
                                    # if not, insert record
                                    cdr_record_count =\
                                    cdr_record_count + 1
                                    msg =\
                                    _('%(cdr_record_count)s Cdr(s) are uploaded, out of %(total_rows)s row(s) !!')\
                                    % {'cdr_record_count': cdr_record_count,
                                       'total_rows': total_rows}
                                    # (cdr_record_count, total_rows)
                                    success_import_list.append(row)
                            except:
                                msg = _("Error : invalid value for import! Check import samples.")
                                type_error_import_list.append(row)
                else:
                    msg = _("Error : invalid value in filed selection order.")
        else:
            form = CDR_FileImport(request.user)

        ctx = RequestContext(request, {
            'title': _('Import CDR'),
            'form': form,
            'opts': opts,
            'model_name': opts.object_name.lower(),
            'app_label': _('Switch'),
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
