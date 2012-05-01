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

from cdr.models import *
from cdr.forms import CDR_FileImport, CDR_FIELD_LIST
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
        Contacts

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
                # col_no - field name
                #  0     - date
                #  1     - destination
                #  2     - account_code
                #  3     - country_id
                #  4     - switch_id
                #  5     - duration
                #  6     - bill sec
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
                            # check field type
                            int(row[5])

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
                                _('%(contact_record_count)s Cdr(s) are uploaded, out of %(total_rows)s row(s) !!')\
                                % {'cdr_record_count': contact_record_count,
                                   'total_rows': total_rows}
                                # (cdr_record_count, total_rows)
                                success_import_list.append(row)
                        except:
                            msg = _("Error : invalid value for import! Check import samples.")
                            type_error_import_list.append(row)
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
            })
        template = 'admin/cdr/switch/import_cdr.html'
        return render_to_response(template, context_instance=ctx)

admin.site.register(Switch, SwitchAdmin)


# HangupCause
class HangupCauseAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'enumeration', 'cause', 'description')
    search_fields = ('code', 'enumeration',)

admin.site.register(HangupCause, HangupCauseAdmin)
