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
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from cdr_alert.models import Alarm
from cdr.functions_def import get_country_list


class BWCountryForm(forms.Form):
    """Blacklist/Whitelist by country form"""
    country = forms.ChoiceField(label=_('country'), required=True,
                                choices=get_country_list())

    def __init__(self, *args, **kwargs):
        super(BWCountryForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['country']


class BWPrefixForm(forms.Form):
    """Blacklist/Whitelist by prefix form"""
    prefix = forms.CharField(label=_('prefix'), required=False)

    def __init__(self, *args, **kwargs):
        super(BWPrefixForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['prefix']


class AlarmForm(ModelForm):
    """Alarm ModelForm"""

    class Meta:
        model = Alarm
        fields = ['name', 'period', 'type', 'alert_condition',
                  'alert_value', 'alert_condition_add_on', 'status',
                  'email_to_send_alarm']
        exclude = ('user',)


class AlarmReportForm(forms.Form):
    """alarm list form"""
    alarm = forms.ChoiceField(label=_("alert"), required=False)

    def __init__(self, user, *args, **kwargs):
        super(AlarmReportForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['alarm']

        alarm_list_user = []
        alarm_list_user.append((0, '---'))
        alarm_list = Alarm.objects.values_list('id', 'name')\
            .filter(user=user).order_by('id')
        for i in alarm_list:
            alarm_list_user.append((i[0], i[1]))

        self.fields['alarm'].choices = alarm_list_user
