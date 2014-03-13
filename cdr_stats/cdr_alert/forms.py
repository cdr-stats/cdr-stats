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
#from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from cdr_alert.models import Alarm
from cdr.functions_def import get_country_list
from mod_utils.forms import common_submit_buttons, SaveUserModelForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, HTML


class BWCountryForm(forms.Form):
    """Blacklist/Whitelist by country form"""
    country = forms.ChoiceField(label=_('country'), required=True,
                                choices=get_country_list())

    def __init__(self, form_type, *args, **kwargs):
        super(BWCountryForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        if form_type == 'blacklist':
            self.helper.form_id = 'id_bl_country_from'
            form_button = HTML("""<input id="add_bl_country" type="button" class="btn btn-info" value="%s" />""" %
                               _("blacklist this country").capitalize())
        else:
            self.helper.form_id = 'id_wl_country_from'
            form_button = HTML("""<input id="add_wl_country" type="button" class="btn btn-info" value="%s" />""" %
                               _("whitelist this country").capitalize())

        self.helper.form_show_labels = False
        css_class = 'col-md-3 col-xs-6'
        self.helper.layout = Layout(
            Div(
                Div('country', css_class=css_class),
                Div(form_button, css_class=css_class),
                css_class='row',
            ),
        )


class BWPrefixForm(forms.Form):
    """Blacklist/Whitelist by prefix form"""
    prefix = forms.CharField(label=_('prefix'), required=False)

    def __init__(self, form_type, *args, **kwargs):
        super(BWPrefixForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        if form_type == 'blacklist':
            self.helper.form_id = 'id_bl_prefix_from'
            prefix_field_id = 'id_bl_prefix'
            form_button = HTML("""<input id="add_bl_prefix" type="button" class="btn btn-info" value="%s" />""" %
                               _("blacklist this dialcode").capitalize())
        else:
            self.helper.form_id = 'id_wl_prefix_from'
            prefix_field_id = 'id_wl_prefix'
            form_button = HTML("""<input id="add_wl_prefix" type="button" class="btn btn-info" value="%s" />""" %
                               _("whitelist this dialcode").capitalize())

        self.helper.form_show_labels = False
        css_class = 'col-md-3 col-xs-6'
        self.helper.layout = Layout(
            Div(
                Div('prefix', css_class=css_class),
                Div(form_button, css_class=css_class),
                css_class='row',
            ),
        )
        self.fields['prefix'].widget.attrs.update({'id': prefix_field_id})
        self.fields['prefix'].widget.attrs['autocomplete'] = 'off'


class AlarmForm(SaveUserModelForm):
    """Alarm ModelForm"""

    class Meta:
        model = Alarm
        #fields = ['name', 'period', 'type', 'alert_condition',
        #          'alert_value', 'alert_condition_add_on', 'status',
        #          'email_to_send_alarm']
        exclude = ('user',)

    def __init__(self, *args, **kwargs):
        super(AlarmForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'well'
        css_class = 'col-md-6'
        self.helper.layout = Layout(
            Div(
                Div('name', css_class=css_class),
                Div('period', css_class=css_class),
                css_class='row',
            ),
            Div(
                Div('type', css_class=css_class),
                Div('alert_condition', css_class=css_class),
                css_class='row',
            ),
            Div(
                Div('alert_value', css_class=css_class),
                Div('alert_condition_add_on', css_class=css_class),
                css_class='row',
            ),
            Div(
                Div('status', css_class=css_class),
                Div('email_to_send_alarm', css_class=css_class),
                css_class='row',
            ),
        )
        if self.instance.id:
            common_submit_buttons(self.helper.layout, 'update')
        else:
            common_submit_buttons(self.helper.layout)


class AlarmReportForm(forms.Form):
    """alarm list form"""
    alarm_id = forms.ChoiceField(label=_("alert").title(), required=False)

    def __init__(self, user, *args, **kwargs):
        super(AlarmReportForm, self).__init__(*args, **kwargs)
        alarm_list_user = []
        alarm_list_user.append((0, '---'))
        alarm_list = Alarm.objects.values_list('id', 'name').filter(user=user).order_by('id')
        for i in alarm_list:
            alarm_list_user.append((i[0], i[1]))

        self.fields['alarm_id'].choices = alarm_list_user
        self.helper = FormHelper()
        self.helper.form_action = '.'
        self.helper.form_class = 'well'
        css_class = 'col-md-4'
        self.helper.layout = Layout(
            Div(
                Div('alarm_id', css_class=css_class),
                css_class='row',
            ),
        )
        common_submit_buttons(self.helper.layout, 'search')
