# CDR-Stats License
#
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2015 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from django.contrib import admin
from import_cdr.models import CDRImport
from import_export import resources
from import_export.admin import ImportExportModelAdmin


class CDRImportResource(resources.ModelResource):

    class Meta:
        model = CDRImport
        using = 'import_cdr'
        # fields = ('switch', 'cdr_source_type', 'callid', 'caller_id_number', 'caller_id_name', 'destination_number', 'dialcode', 'state', 'channel', 'starting_date', 'duration', 'billsec', 'progresssec', 'answersec', 'waitsec', 'hangup_cause_id', 'hangup_cause', 'direction', 'country_code', 'accountcode', 'buy_rate', 'buy_cost', 'sell_rate', 'sell_cost',)
        import_id_fields = ('callid',)
        exclude = ('id', 'imported', )


class MultiDBModelAdmin(admin.ModelAdmin):
    # A handy constant for the name of the alternate database.
    using = 'import_cdr'

    def save_model(self, request, obj, form, change):
        # Tell Django to save objects to the 'other' database.
        obj.save(using=self.using)

    def delete_model(self, request, obj):
        # Tell Django to delete objects from the 'other' database
        obj.delete(using=self.using)

    def get_queryset(self, request):
        # Tell Django to look for objects on the 'other' database.
        return super(MultiDBModelAdmin, self).get_queryset(request).using(self.using)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        # Tell Django to populate ForeignKey widgets using a query
        # on the 'other' database.
        return super(MultiDBModelAdmin, self).formfield_for_foreignkey(db_field, request=request, using=self.using, **kwargs)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        # Tell Django to populate ManyToMany widgets using a query
        # on the 'other' database.
        return super(MultiDBModelAdmin, self).formfield_for_manytomany(db_field, request=request, using=self.using, **kwargs)


# CDRImport
# class CDRImportAdmin(MultiDBModelAdmin, ImportExportModelAdmin):
class CDRImportAdmin(MultiDBModelAdmin, ImportExportModelAdmin):
    list_display = ('id', 'cdr_source_type', 'callid', 'switch', 'destination_number', 'dialcode', 'caller_id_number',
                    'duration', 'hangup_cause', 'direction', 'starting_date', 'hangup_cause_id', 'hangup_cause',
                    'accountcode', 'imported', )
    search_fields = ('destination_number', 'caller_id_number',)
    resource_class = CDRImportResource

admin.site.register(CDRImport, CDRImportAdmin)
