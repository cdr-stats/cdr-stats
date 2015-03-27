#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2014 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from django.contrib import admin
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.conf.urls import patterns
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from country_dialcode.models import Country, Prefix
from cdr_alert.models import AlertRemovePrefix, Alarm, AlarmReport, Blacklist, Whitelist
from cdr_alert.forms import BWCountryForm
from django_lets_go.app_label_renamer import AppLabelRenamer

APP_LABEL = _('CDR Alert')
AppLabelRenamer(native_app_label='cdr_alert', app_label=APP_LABEL).main()


# AlertRemovePrefix
class AlertRemovePrefixAdmin(admin.ModelAdmin):
    list_display = ('id', 'label', 'prefix')
    search_fields = ('label', 'prefix')


# Alarm
class AlarmAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'period', 'type', 'alert_value',
                    'status', 'alert_condition')
    search_fields = ('name', 'type')


# Alarm Report
class AlarmReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'alarm', 'calculatedvalue', 'daterun')
    search_fields = ('alarm', 'calculatedvalue')


# Blacklist
class BlacklistAdmin(admin.ModelAdmin):
    list_display = ('id', 'phonenumber_prefix', 'country')

    def has_add_permission(self, request):
        return False

    def get_urls(self):
        urls = super(BlacklistAdmin, self).get_urls()
        my_urls = patterns('',
                           (r'^blacklist_by_country/$', self.admin_site.admin_view(self.blacklist_by_country)),
                           )
        return my_urls + urls

    def blacklist_by_country(self, request):
        """Add custom method in django admin view to import CSV file of
        Contacts

        **Attributes**:

            * ``form`` - BWCountryForm()
            * ``template`` - admin/cdr_alert/blacklist/blacklist_by_country.html

        **Logic Description**:


        **Important variable**:
        """
        opts = Blacklist._meta
        form = BWCountryForm('blacklist', request.POST or None)
        prefix_list = []
        if form.is_valid():
            country = int(request.POST['country'])
            prefix_list = Prefix.objects.values('prefix').filter(country_id=country)
            msg = _("successfully added prefix into blacklist")
            if request.POST.getlist('blacklist_country'):
                # blacklist whole country
                Blacklist.objects.create(
                    phonenumber_prefix=int(prefix_list[0]['prefix']),
                    country=Country.objects.get(pk=country),
                    user=request.user)

                messages.info(request, msg)
                return HttpResponseRedirect(reverse("admin:cdr_alert_blacklist_changelist"))

            else:
                values = request.POST.getlist('select')
                if values:
                    for i in values:
                        Blacklist.objects.create(
                            phonenumber_prefix=int(i),
                            country=Country.objects.get(pk=country),
                            user=request.user)

                    messages.info(request, msg)
                    return HttpResponseRedirect(reverse("admin:cdr_alert_blacklist_changelist"))

        ctx = RequestContext(request, {
            'title': _('blacklist by country'),
            'form': form,
            'opts': opts,
            'model_name': opts.object_name.lower(),
            'prefix_list': prefix_list,
        })
        return render_to_response('admin/cdr_alert/blacklist/blacklist_by_country.html', context_instance=ctx)


# Whitelist
class WhitelistAdmin(admin.ModelAdmin):

    """
    Whitelist Admin
    """
    list_display = ('id', 'phonenumber_prefix', 'country')

    def has_add_permission(self, request):
        return False

    def get_urls(self):
        urls = super(WhitelistAdmin, self).get_urls()
        my_urls = patterns('',
                           (r'^whitelist_by_country/$', self.admin_site.admin_view(self.whitelist_by_country)),
                           )
        return my_urls + urls

    def whitelist_by_country(self, request):
        """Add custom method in django admin view to import CSV file of
        Contacts

        **Attributes**:

            * ``form`` - BWCountryForm()
            * ``template`` - admin/cdr_alert/whitelist/whitelist_by_country.html

        **Logic Description**:


        **Important variable**:
        """
        opts = Whitelist._meta
        form = BWCountryForm('whitelist', request.POST or None)
        prefix_list = []

        if form.is_valid():
            country = int(request.POST['country'])
            prefix_list = Prefix.objects.values('prefix').filter(country_id=country)
            msg = _("successfully added prefix into whitelist")
            if request.POST.getlist('whitelist_country'):
                # whitelist whole country
                Whitelist.objects.create(
                    phonenumber_prefix=int(prefix_list[0]['prefix']),
                    country=Country.objects.get(pk=country),
                    user=request.user)

                messages.info(request, msg)
                return HttpResponseRedirect(reverse("admin:cdr_alert_whitelist_changelist"))
            else:
                values = request.POST.getlist('select')
                if values:
                    for i in values:
                        Whitelist.objects.create(
                            phonenumber_prefix=int(i),
                            country=Country.objects.get(pk=country),
                            user=request.user)

                    messages.info(request, msg)
                    return HttpResponseRedirect(reverse("admin:cdr_alert_whitelist_changelist"))

        ctx = RequestContext(request, {
            'title': _('whitelist by country'),
            'form': form,
            'opts': opts,
            'model_name': opts.object_name.lower(),
            'prefix_list': prefix_list,
        })
        return render_to_response('admin/cdr_alert/whitelist/whitelist_by_country.html', context_instance=ctx)


admin.site.register(AlertRemovePrefix, AlertRemovePrefixAdmin)
admin.site.register(Alarm, AlarmAdmin)
admin.site.register(AlarmReport, AlarmReportAdmin)
admin.site.register(Blacklist, BlacklistAdmin)
admin.site.register(Whitelist, WhitelistAdmin)
