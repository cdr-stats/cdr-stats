# -*- coding: utf-8 -*-

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
from django import forms
from django.conf import settings
from django.core.validators import validate_email
from django.utils.translation import ugettext_lazy as _
from django_lets_go.common_functions import comp_day_range
from cdr.functions_def import get_switch_list, get_country_list
from cdr.constants import STRING_SEARCH_TYPE_LIST, CheckWith, CDR_FIELD_LIST, CDR_FIELD_LIST_NUM
from cdr.models import HangupCause
from user_profile.models import UserProfile
from bootstrap3_datetime.widgets import DateTimePicker
from mod_utils.forms import common_submit_buttons, HorizRadioRenderer
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, HTML  # Fieldset, Field


COMPARE_LIST = (
    (2, '>'),
    (3, '>='),
    (4, '<'),
    (5, '<='),
    (1, '=')
)

PAGE_SIZE_LIST = (
    (10, '10'),
    (25, '25'),
    (50, '50'),
    (100, '100'),
    (250, '250'),
    (500, '500'),
    (1000, '1000')
)


def sw_list_with_all():
    """Switch list"""
    list_sw = []
    list_sw.append((0, _('all switches').capitalize()))
    for i in get_switch_list():
        list_sw.append((i[0], i[1]))
    return list_sw


def hc_list_with_all():
    """Hangup cause list"""
    list_hc = []
    list_hc.append((0, _('all').capitalize()))
    for i in HangupCause.objects.get_all_hangupcause():
        list_hc.append((i[0], i[1]))
    return list_hc


def country_list_with_all():
    """Country list"""
    list_ct = []
    list_ct.append((0, _('all').capitalize()))
    list_ct.append((999, _('internal call').capitalize()))
    for i in get_country_list():
        list_ct.append((i[0], i[1]))
    return list_ct


class SearchForm(forms.Form):
    """
    Form used to search on general parameters in the Customer UI.
    """
    caller = forms.CharField(label=_('callerID number').capitalize(), required=False)
    caller_type = forms.ChoiceField(label=_('type').capitalize(), required=False,
                                    choices=list(STRING_SEARCH_TYPE_LIST))
    destination = forms.CharField(label=_('destination').capitalize(), required=False)
    destination_type = forms.ChoiceField(label=_('type').capitalize(), required=False,
                                         choices=list(STRING_SEARCH_TYPE_LIST))
    accountcode = forms.CharField(label=_('account code').capitalize(), required=False)
    accountcode_type = forms.ChoiceField(label=_('type').capitalize(), required=False,
                                         choices=list(STRING_SEARCH_TYPE_LIST))
    duration = forms.CharField(label=_('duration (secs)').capitalize(), required=False)
    duration_type = forms.ChoiceField(label=_('type').capitalize(), required=False,
                                      choices=COMPARE_LIST)
    hangup_cause_id = forms.ChoiceField(label=_('hangup cause').capitalize(), required=False)
    switch_id = forms.ChoiceField(label=_('switch').capitalize(), required=False)
    country_id = forms.MultipleChoiceField(label=_('country').capitalize(), required=False,
                                           choices=country_list_with_all())

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['hangup_cause_id'].choices = hc_list_with_all()
        self.fields['switch_id'].choices = sw_list_with_all()

    def clean_duration(self):
        """Retrieve valid duration & it should be integer
        else will raise from validation error
        """
        duration = self.cleaned_data['duration']
        if duration:
            try:
                int(duration)
            except:
                raise forms.ValidationError('%s is not a valid duration.' % duration)
        return duration

    def clean_accountcode(self):
        """Retrieve valid accountcode"""
        return self.cleaned_data['accountcode']


class CdrSearchForm(SearchForm):
    """
    Form used to search calls in the Customer UI.
    """
    from_date = forms.DateTimeField(label=_('from').capitalize(), required=True,
        widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm", "pickSeconds": False}))
    to_date = forms.DateTimeField(label=_('to').capitalize(), required=True,
        widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm", "pickSeconds": False}))
    direction = forms.TypedChoiceField(label=_('direction').capitalize(), required=False,
                                       choices=(('all', _('all')),
                                                ('inbound', _('inbound')),
                                                ('outbound', _('outbound')),
                                                ('unknown', _('unknown'))))
    result = forms.ChoiceField(label=_('result').capitalize(), required=False,
                               choices=((1, _('minutes')), (2, _('seconds'))),
                               widget=forms.RadioSelect(renderer=HorizRadioRenderer))
    records_per_page = forms.ChoiceField(label=_('CDR per page'), required=False,
                                         initial=settings.PAGE_SIZE, choices=PAGE_SIZE_LIST)

    def __init__(self, *args, **kwargs):
        super(CdrSearchForm, self).__init__(*args, **kwargs)
        self.fields['records_per_page'].widget.attrs['onchange'] = 'this.form.submit();'
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_class = 'well'
        css_class = 'col-md-4'
        self.fields['result'].initial = 1

        self.helper.layout = Layout(
            Div(
                Div('from_date', css_class=css_class),
                Div('to_date', css_class=css_class),
                Div('switch_id', css_class=css_class),
                css_class='row'
            ),
            Div(
                Div('destination', css_class='col-md-2'),
                Div('destination_type', css_class='col-md-2'),
                Div('accountcode', css_class='col-md-2'),
                Div('accountcode_type', css_class='col-md-2'),
                Div('caller', css_class='col-md-2'),
                Div('caller_type', css_class='col-md-2'),
                css_class='row'
            ),
            Div(
                Div('direction', css_class=css_class),
                Div('duration', css_class='col-md-3'),
                Div('duration_type', css_class='col-md-1'),
                Div(HTML("""
                    <b>Result : </b><br/>
                    <div class="btn-group" data-toggle="buttons">
                        {% for choice in form.result.field.choices %}
                        <label class="btn btn-default {% if choice.0 == form.result.value %}active{% endif %}">
                            <input name='{{ form.result.name }}' type='radio' value='{{ choice.0 }}'/> {{ choice.1 }}
                        </label>
                        {% endfor %}
                    </div>
                   """), css_class=css_class),
                css_class='row'
            ),
            Div(
                Div('country_id', css_class=css_class),
                css_class='row'
            ),
        )
        common_submit_buttons(self.helper.layout, 'search')
        self.fields['records_per_page'].widget.attrs['class'] = 'select form-control'


class CountryReportForm(CdrSearchForm):
    """
    Form used to get country vise calls report in the Customer UI.
    """
    from_date = forms.DateTimeField(label=_('from').capitalize(), required=False,
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False}))
    to_date = forms.DateTimeField(label=_('to').capitalize(), required=False,
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False}))

    def __init__(self, *args, **kwargs):
        super(CountryReportForm, self).__init__(*args, **kwargs)
        self.fields['duration_type'].label = _('type').title()
        self.helper = FormHelper()
        self.helper.form_class = 'well'
        css_class = 'col-md-4'
        self.helper.layout = Layout(
            Div(
                Div('from_date', css_class=css_class),
                Div('to_date', css_class=css_class),
                Div('switch_id', css_class=css_class),
                css_class='row'
            ),
            Div(
                Div('duration', css_class='col-md-3'),
                Div('duration_type', css_class='col-md-1'),
                Div('country_id', css_class=css_class),
                css_class='row'
            ),
        )
        common_submit_buttons(self.helper.layout, 'search')


class CdrOverviewForm(CdrSearchForm):
    """
    Form used to get overview of calls in the Customer UI.
    """
    def __init__(self, *args, **kwargs):
        super(CdrOverviewForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'well'
        css_class = 'col-md-4'
        self.helper.layout = Layout(
            Div(
                Div('from_date', css_class=css_class),
                Div('to_date', css_class=css_class),
                Div('switch_id', css_class=css_class),
                css_class='row'
            ),
        )
        common_submit_buttons(self.helper.layout, 'search')


class CompareCallSearchForm(SearchForm):
    """
    Form used to search calls for comparison in the Customer UI.
    """
    from_date = forms.DateTimeField(label=_('select date').capitalize(), required=True,
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False}))
    comp_days = forms.ChoiceField(label=_('compare').capitalize(), required=False, choices=comp_day_range(6))
    check_days = forms.TypedChoiceField(label=_('check with').capitalize(),
                                        choices=list(CheckWith), widget=forms.RadioSelect(renderer=HorizRadioRenderer))

    def __init__(self, *args, **kwargs):
        super(CompareCallSearchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'well'
        css_class = 'col-md-4'
        self.helper.layout = Layout(
            Div(
                Div('from_date', css_class='col-md-3'),
                Div('comp_days', css_class='col-md-2'),
                Div('switch_id', css_class='col-md-3'),
                Div(HTML("""
                    <b>Check with* : </b><br/>
                    <div class="btn-group" data-toggle="buttons">
                        {% for choice in form.check_days.field.choices %}
                        <label class="btn btn-default">
                            <input name='{{ form.check_days.name }}' type='radio' value='{{ choice.0 }}'/>
                            {{ choice.1 }}
                        </label>
                        {% endfor %}
                    </div>
                   """), css_class=css_class),
                css_class='row'
            ),
        )
        common_submit_buttons(self.helper.layout, 'search')


class ConcurrentCallForm(CdrSearchForm):
    """
    Form used for concurrent calls in the Customer UI.
    """
    def __init__(self, *args, **kwargs):
        super(ConcurrentCallForm, self).__init__(*args, **kwargs)
        self.fields['from_date'].label = _('select date').capitalize()
        self.helper = FormHelper()
        self.helper.form_class = 'well'
        css_class = 'col-md-4'
        self.helper.layout = Layout(
            Div(
                Div('from_date', css_class=css_class),
                Div('switch_id', css_class=css_class),
                css_class='row'
            ),
        )
        common_submit_buttons(self.helper.layout, 'search')


class SwitchForm(SearchForm):
    """
    Form used to get the list of switches in the Customer UI.
    """
    def __init__(self, *args, **kwargs):
        super(SwitchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'well'
        css_class = 'col-md-3'
        self.helper.layout = Layout(
            Div(
                Div('switch_id', css_class=css_class),
                css_class='row'
            ),
        )
        self.fields['switch_id'].widget.attrs['onchange'] = 'this.form.submit();'


class WorldForm(CdrSearchForm):
    """
    Form used to get world overview of calls in the Customer UI.
    """
    from_date = forms.DateTimeField(label=_('from').capitalize(), required=True,
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False}))
    to_date = forms.DateTimeField(label=_('to').capitalize(), required=True,
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False}))

    def __init__(self, *args, **kwargs):
        super(WorldForm, self).__init__(*args, **kwargs)
        #self.fields.keyOrder = ['from_date', 'to_date', 'switch_id']
        self.helper = FormHelper()
        self.helper.form_class = 'well'
        css_class = 'col-md-4'
        self.helper.layout = Layout(
            Div(
                Div('from_date', css_class=css_class),
                Div('to_date', css_class=css_class),
                Div('switch_id', css_class=css_class),
                css_class='row'
            ),
        )
        common_submit_buttons(self.helper.layout, 'search')


class EmailReportForm(forms.ModelForm):
    """
    Form used to change the detail of a user in the Customer UI.
    """
    multiple_email = forms.CharField(max_length=300, required=False, label=_('Email to send the report'))

    class Meta:
        model = UserProfile
        fields = ('multiple_email', )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(EmailReportForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'well'
        css_class = 'col-md-4'
        self.helper.layout = Layout(
            Div(
                Div('multiple_email', css_class=css_class),
                css_class='row'
            ),
        )
        common_submit_buttons(self.helper.layout, 'add')

    def clean_multiple_email(self):
        """Check that the field contains one or more comma-separated emails
        and normalizes the data to a list of the email strings.
        """
        emails = self.cleaned_data['multiple_email'].split(',')
        mail_list = []
        for email in emails:
            email = email.strip()
            try:
                validate_email(email)
                mail_list.append(str(email))
            except:
                raise forms.ValidationError('%s is not a valid e-mail address.' % email)

        # Always return the cleaned data.
        mail_list = ','.join(mail_list)
        return mail_list


class FileImport(forms.Form):
    """General Form : CSV file upload"""

    csv_file = forms.FileField(label=_('upload CSV File '), required=True,
                               error_messages={'required': 'please upload File'},
                               help_text=_('browse CSV file'))

    def clean_csv_file(self):
        """Form Validation :  File extension Check"""
        filename = self.cleaned_data['csv_file']
        file_exts = ('csv', 'txt')
        if not str(filename).split('.')[1].lower() in file_exts:
            raise forms.ValidationError(_(u'document types accepted: %s' % """ """.join(file_exts)))
        else:
            return filename

ACCOUNTCODE_FIELD_LIST_NUM = [(x, 'column-' + str(x)) for x in range(1, len(CDR_FIELD_LIST) + 1)]
ACCOUNTCODE_FIELD_LIST_NUM.append((0, 'No import'))
ACCOUNTCODE_FIELD_LIST_NUM = sorted(ACCOUNTCODE_FIELD_LIST_NUM,
    key=lambda ACCOUNTCODE_FIELD_LIST_NUM: ACCOUNTCODE_FIELD_LIST_NUM[0])


class CDR_FileImport(FileImport):
    """Admin Form : Import CSV file with phonebook CDR_FIELD_LIST"""
    switch_id = forms.ChoiceField(label=_('switch'), required=True, help_text=_('select switch'))
    accountcode_csv = forms.CharField(label=_('account code'), required=False)
    caller_id_number = forms.ChoiceField(label=_('caller_id_number'), required=True, choices=CDR_FIELD_LIST_NUM)
    caller_id_name = forms.ChoiceField(label=_('caller_id_name'), required=True, choices=ACCOUNTCODE_FIELD_LIST_NUM)
    destination_number = forms.ChoiceField(label=_('destination_number'), required=True, choices=CDR_FIELD_LIST_NUM)
    duration = forms.ChoiceField(label=_('duration'), required=True, choices=CDR_FIELD_LIST_NUM)
    billsec = forms.ChoiceField(label=_('billsec'), required=True, choices=CDR_FIELD_LIST_NUM)
    hangup_cause_id = forms.ChoiceField(label=_('hangup_cause_id'), required=True, choices=CDR_FIELD_LIST_NUM)
    direction = forms.ChoiceField(label=_('direction'), required=True, choices=ACCOUNTCODE_FIELD_LIST_NUM)
    uuid = forms.ChoiceField(label=_('uuid'), required=True, choices=ACCOUNTCODE_FIELD_LIST_NUM)
    remote_media_ip = forms.ChoiceField(label=_('remote_media_ip'), required=True, choices=ACCOUNTCODE_FIELD_LIST_NUM)
    start_uepoch = forms.ChoiceField(label=_('start_uepoch'), required=True, choices=CDR_FIELD_LIST_NUM)
    answer_uepoch = forms.ChoiceField(label=_('answer_uepoch'), required=True, choices=ACCOUNTCODE_FIELD_LIST_NUM)
    end_uepoch = forms.ChoiceField(label=_('end_uepoch'), required=True, choices=ACCOUNTCODE_FIELD_LIST_NUM)
    mduration = forms.ChoiceField(label=_('mduration'), required=True, choices=ACCOUNTCODE_FIELD_LIST_NUM)
    billmsec = forms.ChoiceField(label=_('billmsec'), required=True, choices=ACCOUNTCODE_FIELD_LIST_NUM)
    read_codec = forms.ChoiceField(label=_('read_codec'), required=True, choices=ACCOUNTCODE_FIELD_LIST_NUM)
    write_codec = forms.ChoiceField(label=_('write_codec'), required=True, choices=ACCOUNTCODE_FIELD_LIST_NUM)
    accountcode = forms.ChoiceField(label=_('accountcode'), required=True, choices=ACCOUNTCODE_FIELD_LIST_NUM)
    import_asterisk = forms.BooleanField(label=_('asterisk hangup format'), required=False,
        help_text=_('with this option on, the field hangup_cause_id will expect Asterisk Hangup Cause in the format : ANSWER, CANCEL, BUSY, CONGESTION, CHANUNAVAIL, etc..'))

    def __init__(self, user, *args, **kwargs):
        super(CDR_FileImport, self).__init__(*args, **kwargs)

        self.fields['switch_id'].choices = get_switch_list()
#