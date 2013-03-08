# -*- coding: utf-8 -*-
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

from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _

from dajaxice.decorators import dajaxice_register
from dajax.core import Dajax

from cdr_alert.models import Whitelist, Blacklist
from country_dialcode.models import Country, Prefix


alert = _('alert').capitalize()

blacklist_word = _('blacklist')
whitelist_word = _('whitelist')

success_msg = _('has been successfully added in')
delete_success_msg = _('has been successfully deleted from')
delete_all_success_msg = _('All dialcode are successfully deleted from')
info_msg = _('is already added in')
error_msg = _('has not been added in')
delete_error_msg = _('has not been deleted from')

blacklist_success = '<div class="alert alert-success">' + alert + ' : (%s) ' + success_msg + ' ' + blacklist_word + '</div>'
blacklist_delete_success = '<div class="alert alert-success">' + alert + ' : (%s) ' + delete_success_msg + ' ' + blacklist_word + '</div>'
blacklist_delete_all_success = '<div class="alert alert-success">' + alert + ' :  ' + delete_all_success_msg + ' ' + blacklist_word + '</div>'
blacklist_info = '<div class="alert alert-info">' + alert + ' : (%s) ' + info_msg + ' ' + blacklist_word + '</div>'
blacklist_error = '<div class="alert alert-error">' + alert + ' : (%s) ' + error_msg + ' ' + blacklist_word + '</div>'
blacklist_delete_error = '<div class="alert alert-error">' + alert + ' : (%s) ' + delete_error_msg + ' ' + blacklist_word + '</div>'


whitelist_success = '<div class="alert alert-success">' + alert + ' : (%s) ' + success_msg + ' ' + whitelist_word + '</div>'
whitelist_delete_success = '<div class="alert alert-success">' + alert + ' : (%s) ' + delete_success_msg + ' ' + whitelist_word + '</div>'
whitelist_delete_all_success = '<div class="alert alert-success">' + alert + ' :  ' + delete_all_success_msg + ' ' + whitelist_word + '</div>'
whitelist_info = '<div class="alert alert-info">' + alert + ' : (%s) ' + info_msg + ' ' + whitelist_word + '</div>'
whitelist_error = '<div class="alert alert-error">' + alert + ' : (%s) ' + error_msg + ' ' + whitelist_word + '</div>'
whitelist_delete_error = '<div class="alert alert-error">' + alert + ' : (%s) ' + delete_error_msg + ' ' + whitelist_word + '</div>'


def get_html_table(request, default_name='blacklist'):
    col = 5  # group by columns
    html_table = '<table class="table table-striped table-bordered table-condensed">'
    if default_name == 'blacklist':
        prefix_list = Blacklist.objects.filter(user=request.user).order_by('id')
        prefix_list_count = prefix_list.count()
        html_table += '<tr><td>\
            <input type="checkbox" onclick="toggleChecked_blacklist(this.checked);"></td></tr>'

    if default_name == 'whitelist':
        prefix_list = Whitelist.objects.filter(user=request.user).order_by('id')
        prefix_list_count = prefix_list.count()
        html_table += '<tr><td>\
            <input type="checkbox" onclick="toggleChecked_whitelist(this.checked);"></td></tr>'

    if prefix_list_count != 0:
        # Logic of groupby_columns template tag
        rows = (prefix_list_count // col) + 1
        table = [prefix_list[i::rows] for i in range(rows)]
        n = len(table[0])
        new_prefix_list = [row + [None for x in range(n - len(row))] for row in table]

        for obj_list in new_prefix_list:
            html_table += '<tr>'
            for obj in obj_list:
                if obj:
                    if default_name == 'blacklist':
                        obj_string = '<input type="checkbox" name="select_blacklist" class="checkbox" value="' + str(obj.id) + '" />&nbsp;'
                    if default_name == 'whitelist':
                        obj_string = '<input type="checkbox" name="select_whitelist" class="checkbox" value="' + str(obj.id) + '" />&nbsp;'

                    obj_string += str(obj.phonenumber_prefix) + ' | ' + str(obj.country.countryname)
                    html_table += '<td>' + str(obj_string) + '</td>'
                else:
                    html_table += '<td>&nbsp;</td>'
            html_table += '</tr>'
        html_table += '</table>'
    else:
        html_table = ''

    return html_table


@login_required
@dajaxice_register
def add_blacklist_country(request, country_id):
    dajax = Dajax()
    try:
        country = Country.objects.get(id=int(country_id))
        country_id = country.id
        prefix_list =\
            Prefix.objects.values_list('prefix', flat=True).filter(country_id=country_id)

        add_flag = False
        for prefix in prefix_list:
            rec_count = Blacklist.objects.filter(user=request.user,
                                                 phonenumber_prefix=int(prefix),
                                                 country_id=country_id).count()
            # No duplicate record found, so insert
            if rec_count == 0:
                Blacklist.objects.create(
                    user=request.user,
                    phonenumber_prefix=int(prefix),
                    country_id=country_id,
                )
                add_flag = True
        if add_flag:
            message = blacklist_success % (country.countryname)
        else:
            message = blacklist_info % (country.countryname)

        html_table = get_html_table(request, 'blacklist')
        dajax.assign('#id_blacklist_table', 'innerHTML', str(html_table))
    except:
        message = blacklist_error % (country.countryname)
    dajax.assign('#id_alert_message', 'innerHTML', str(message))
    return dajax.json()


@login_required
@dajaxice_register
def add_blacklist_prefix(request, prefix):
    dajax = Dajax()
    try:
        prfix_obj = Prefix.objects.get(prefix=int(prefix))
        country_id = prfix_obj.country_id.id
        rec_count = Blacklist.objects.filter(user=request.user,
                                             phonenumber_prefix=int(prefix),
                                             country_id=country_id).count()
        add_flag = False
        # No duplicate record found, so insert
        if rec_count == 0:
            Blacklist.objects.create(
                user=request.user,
                phonenumber_prefix=int(prefix),
                country_id=country_id,
            )
            add_flag = True

        if add_flag:
            message = blacklist_success % (str(prefix))
        else:
            message = blacklist_info % (str(prefix))
        html_table = get_html_table(request, 'blacklist')
        dajax.assign('#id_blacklist_table', 'innerHTML', str(html_table))
    except:
        message = blacklist_error % (prefix)
    dajax.assign('#id_alert_message', 'innerHTML', str(message))
    return dajax.json()


@login_required
@dajaxice_register
def delete_blacklist(request, id_list):
    dajax = Dajax()
    try:
        # delete selected
        if str(id_list) != '0':
            id_list = map(int, id_list)
            objs = Blacklist.objects.filter(id__in=id_list)
            del_dialcodes = ''
            for i in objs:
                del_dialcodes += str(i.phonenumber_prefix) + ', '
            objs.delete()
            message = blacklist_delete_success % (str(del_dialcodes[:-1]))
        else:
            # delete all
            objs = Blacklist.objects.filter(user=request.user)
            objs.delete()
            message = blacklist_delete_all_success

        html_table = get_html_table(request, 'blacklist')
        dajax.assign('#id_blacklist_table', 'innerHTML', str(html_table))
    except:
        message = blacklist_delete_error % (str(id_list))
    dajax.assign('#id_alert_message', 'innerHTML', str(message))
    return dajax.json()


@login_required
@dajaxice_register
def add_whitelist_country(request, country_id):
    dajax = Dajax()
    try:
        country = Country.objects.get(id=int(country_id))
        country_id = country.id
        prefix_list =\
            Prefix.objects.values_list('prefix', flat=True).filter(country_id=country_id)

        add_flag = False
        for prefix in prefix_list:
            rec_count = Whitelist.objects.filter(user=request.user,
                                                 phonenumber_prefix=int(prefix),
                                                 country_id=country_id).count()
            # No duplicate record found, so insert
            if rec_count == 0:
                Whitelist.objects.create(
                    user=request.user,
                    phonenumber_prefix=int(prefix),
                    country_id=country_id,
                )
                add_flag = True
        if add_flag:
            message = whitelist_success % (country.countryname)
        else:
            message = whitelist_info % (country.countryname)

        html_table = get_html_table(request, 'whitelist')
        dajax.assign('#id_whitelist_table', 'innerHTML', str(html_table))
    except:
        message = whitelist_error % (str(prefix))
    dajax.assign('#id_alert_message', 'innerHTML', str(message))
    return dajax.json()


@login_required
@dajaxice_register
def add_whitelist_prefix(request, prefix):
    dajax = Dajax()

    try:
        prfix_obj = Prefix.objects.get(prefix=int(prefix))
        country_id = prfix_obj.country_id.id

        rec_count = Whitelist.objects.filter(user=request.user,
                                             phonenumber_prefix=int(prefix),
                                             country_id=country_id).count()
        add_flag = False
        # No duplicate record, so insert
        if rec_count == 0:
            Whitelist.objects.create(
                user=request.user,
                phonenumber_prefix=int(prefix),
                country_id=country_id,
            )
            add_flag = True

        if add_flag:
            message = whitelist_success % (str(prefix))
        else:
            message = whitelist_info % (str(prefix))
        html_table = get_html_table(request, 'whitelist')
        dajax.assign('#id_whitelist_table', 'innerHTML', str(html_table))
    except:
        message = whitelist_error % (str(prefix))
    dajax.assign('#id_alert_message', 'innerHTML', str(message))
    return dajax.json()


@login_required
@dajaxice_register
def delete_whitelist(request, id_list):
    dajax = Dajax()
    try:
        # delete selected
        if str(id_list) != '0':
            id_list = map(int, id_list)
            objs = Whitelist.objects.filter(id__in=id_list)
            del_dialcodes = ''
            for i in objs:
                del_dialcodes += str(i.phonenumber_prefix) + ', '
            objs.delete()
            message = whitelist_delete_success % (str(del_dialcodes[:-1]))
        else:
            # delete all
            objs = Whitelist.objects.filter(user=request.user)
            objs.delete()
            message = whitelist_delete_all_success
        html_table = get_html_table(request, 'whitelist')
        dajax.assign('#id_whitelist_table', 'innerHTML', str(html_table))
    except:
        message = blacklist_delete_error % (str(id_list))
    dajax.assign('#id_alert_message', 'innerHTML', str(message))
    return dajax.json()
