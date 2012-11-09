# -*- coding: utf-8 -*-

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
from django import forms
from django.conf import settings
from django.core.validators import validate_email
from django.utils.translation import ugettext_lazy as _
from common.common_functions import comp_day_range
from cdr.functions_def import get_switch_list, get_country_list, get_hc_list
from cdr.constants import STRING_SEARCH_TYPE_LIST
from user_profile.models import UserProfile

COMPARE_LIST = ((2, '>'),
                (3, '>='),
                (4, '<'),
                (5, '<='),
                (1, '='),)

PAGE_SIZE_LIST = ((10, '10'),
                  (25, '25'),
                  (50, '50'),
                  (100, '100'),
                  (250, '250'),
                  (500, '500'),
                  (1000, '1000'))

DATE_HELP_TEXT = _('Please use the following format') \
    + ': <em>YYYY-MM-DD</em>.'


def sw_list_with_all():
    """Switch list"""
    list_sw = []
    list_sw.append((0, _('All Switches')))
    sw_list = get_switch_list()
    for i in sw_list:
        list_sw.append((i[0], i[1]))
    return list_sw


def hc_list_with_all():
    """Hangup cause list"""
    list_hc = []
    list_hc.append((0, _('All')))
    hc_list = get_hc_list()
    for i in hc_list:
        list_hc.append((i[0], i[1]))
    return list_hc


def country_list_with_all():
    """Country list"""
    list_ct = []
    list_ct.append((0, _('All')))
    ct_list = get_country_list()
    for i in ct_list:
        list_ct.append((i[0], i[1]))
    return list_ct


class SearchForm(forms.Form):
    """
    Form used to search on general parameters in the Customer UI.
    """

    caller = forms.CharField(label=_('Caller ID'), required=False)
    caller_type = forms.ChoiceField(label='', required=False,
                                    choices=list(STRING_SEARCH_TYPE_LIST))
    caller_type.widget.attrs['class'] = 'input-small'

    destination = forms.CharField(label=_('Destination'),
                                  required=False)
    destination_type = forms.ChoiceField(label='',
                                         required=False,
                                         choices=list(STRING_SEARCH_TYPE_LIST))
    destination_type.widget.attrs['class'] = 'input-small'
    accountcode = forms.CharField(label=_('Account Code'),
                                  required=False)
    accountcode_type = forms.ChoiceField(label='',
                                         required=False,
                                         choices=list(STRING_SEARCH_TYPE_LIST))
    accountcode_type.widget.attrs['class'] = 'input-small'
    duration = forms.CharField(label=_('Duration'),
                               required=False)
    duration_type = forms.ChoiceField(label='',
                                      required=False,
                                      choices=COMPARE_LIST)
    duration_type.widget.attrs['class'] = 'input-small'
    hangup_cause = forms.ChoiceField(label=_('Hangup cause'),
                                     required=False,
                                     choices=hc_list_with_all())
    switch = forms.ChoiceField(label=_('Switch'),
                               required=False,
                               choices=get_switch_list())
    country_id = forms.MultipleChoiceField(label=_('Country'), required=False,
                                           choices=country_list_with_all())

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['switch'].choices = sw_list_with_all()

    def clean_caller(self):
        """Retrieve valid caller & it should be integer
        else will raise from validation error
        """
        caller = self.cleaned_data['caller']
        if caller:
            try:
                int(caller)
            except:
                raise forms.ValidationError('%s is not a valid caller.'
                        % caller)
        return caller

    def clean_duration(self):
        """Retrieve valid duration & it should be integer
        else will raise from validation error
        """
        duration = self.cleaned_data['duration']
        if duration:
            try:
                int(duration)
            except:
                raise forms.ValidationError('%s is not a valid duration.'
                        % duration)
        return duration

    def clean_accountcode(self):
        """Retrieve valid accountcode"""
        accountcode = self.cleaned_data['accountcode']
        return accountcode

    def clean_destination(self):
        """Retrieve valid destination & it should be integer
        else will raise from validation error"""
        destination = self.cleaned_data['destination']
        if destination:
            try:
                int(destination)
            except:
                raise forms.ValidationError('%s is not a valid destination.'
                        % destination)
        return destination


class CdrSearchForm(SearchForm):
    """
    Form used to search calls in the Customer UI.
    """

    from_date = forms.CharField(label=_('From'),
                                required=True, max_length=10)
    to_date = forms.CharField(label=_('To'),
                                required=True, max_length=10)
    direction = forms.TypedChoiceField(label=_('Direction'),
                                required=False,
                                coerce=bool,
                                choices=(('all', _('All')),
                                    ('inbound', _('Inbound')),
                                    ('outbound', _('Outbound'))))
    result = forms.TypedChoiceField(label=_('Result'),
                                required=False,
                                coerce=bool,
                                choices=((1, _('Minutes')),
                                    (2, _('Seconds'))),
                                    widget=forms.RadioSelect)
    records_per_page = forms.ChoiceField(label=_('CDR per page'),
                                required=False,
                                initial=settings.PAGE_SIZE,
                                choices=PAGE_SIZE_LIST)
    records_per_page.widget.attrs['class'] = 'input-mini'

    def __init__(self, *args, **kwargs):
        super(CdrSearchForm, self).__init__(*args, **kwargs)
        self.fields['records_per_page'].widget.attrs['onchange'] = \
            'this.form.submit();'


class CountryReportForm(CdrSearchForm):
    """
    Form used to get country vise calls report in the Customer UI.
    """
    def __init__(self, *args, **kwargs):
        super(CountryReportForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['from_date', 'to_date', 'country_id',
                                'duration', 'duration_type', 'switch']


class CdrOverviewForm(CdrSearchForm):
    """
    Form used to get overview of calls in the Customer UI.
    """
    def __init__(self, *args, **kwargs):
        super(CdrOverviewForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['from_date', 'to_date', 'switch']


class CompareCallSearchForm(SearchForm):
    """
    Form used to search calls for comparison in the Customer UI.
    """
    from_date = forms.CharField(label=_('Select date'), required=True,
                                max_length=10)

    comp_days = forms.ChoiceField(label='', required=False,
                                  choices=comp_day_range(6))
    comp_days.widget.attrs['class'] = 'input-small'
    graph_view = forms.ChoiceField(label=_('Graph'), required=False,
                                   choices=((1, _('Calls per Hour')), (2,
                                   _('Minutes per Hour'))))
    check_days = forms.TypedChoiceField(label=_('Check with'), required=False,
            coerce=bool, choices=((1, _('Previous days')), (2,
            _('Same day of the week'))), widget=forms.RadioSelect)

    def __init__(self, *args, **kwargs):
        super(CompareCallSearchForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['from_date', 'comp_days', 'check_days',
                                'graph_view', 'switch']


class ConcurrentCallForm(CdrSearchForm):
    """
    Form used for concurrent calls in the Customer UI.
    """
    def __init__(self, *args, **kwargs):
        super(ConcurrentCallForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['from_date', 'result', 'switch']
        self.fields['from_date'].label = _('Select date')


class SwitchForm(SearchForm):
    """
    Form used to get the list of switches in the Customer UI.
    """
    def __init__(self, *args, **kwargs):
        super(SwitchForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['switch']
        self.fields['switch'].widget.attrs['onchange'] = 'this.form.submit();'


class WorldForm(CdrSearchForm):
    """
    Form used to get world overview of calls in the Customer UI.
    """
    def __init__(self, *args, **kwargs):
        super(WorldForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['from_date', 'to_date', 'switch']


class EmailReportForm(forms.ModelForm):
    """
    Form used to change the detail of a user in the Customer UI.
    """
    multiple_email = forms.CharField(max_length=300, required=False,
        label=_('Email to send the report'))
    multiple_email.widget.attrs['class'] = 'span6'

    class Meta:
        model = UserProfile
        fields = ('multiple_email', )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(EmailReportForm, self).__init__(*args, **kwargs)

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
                raise forms.ValidationError('%s is not a valid e-mail address.'
                         % email)

        # Always return the cleaned data.
        mail_list = ','.join(mail_list)
        return mail_list


class FileImport(forms.Form):
    """General Form : CSV file upload"""

    csv_file = forms.FileField(label=_('Upload CSV File '), required=True,
                               error_messages={'required': 'Please upload File'
                               }, help_text=_('Browse CSV file'))

    def clean_csv_file(self):
        """Form Validation :  File extension Check"""
        filename = self.cleaned_data['csv_file']
        file_exts = ('csv', 'txt')
        if not str(filename).split('.')[1].lower() in file_exts:
            raise forms.ValidationError(_(u'Document types accepted: %s'
                    % """ """.join(file_exts)))
        else:
            return filename


CDR_FIELD_LIST = (
    'caller_id_number',
    'caller_id_name',
    'destination_number',
    'duration',
    'billsec',
    'hangup_cause_id',
    'direction',
    'uuid',
    'remote_media_ip',
    'start_uepoch',
    'answer_uepoch',
    'end_uepoch',
    'mduration',
    'billmsec',
    'read_codec',
    'write_codec',
    'accountcode',
    )

CDR_FIELD_LIST_NUM = [(x, 'column-' + str(x)) for x in range(1,
                      len(CDR_FIELD_LIST) + 1)]
ACCOUNTCODE_FIELD_LIST_NUM = [(x, 'column-' + str(x)) for x in range(1,
                              len(CDR_FIELD_LIST) + 1)]
ACCOUNTCODE_FIELD_LIST_NUM.append((0, 'No import'))
ACCOUNTCODE_FIELD_LIST_NUM = sorted(ACCOUNTCODE_FIELD_LIST_NUM,
                                    key=lambda ACCOUNTCODE_FIELD_LIST_NUM: \
                                    ACCOUNTCODE_FIELD_LIST_NUM[0])


class CDR_FileImport(FileImport):

    """Admin Form : Import CSV file with phonebook CDR_FIELD_LIST"""

    switch = forms.ChoiceField(label=_('Switch'), choices=get_switch_list(),
                               required=True, help_text=_('Select switch'))
    accountcode_csv = forms.CharField(label=_('Account code'),
                                      required=False)
    caller_id_number = forms.ChoiceField(label=_('caller_id_number'),
                                         required=True,
                                         choices=CDR_FIELD_LIST_NUM)
    caller_id_name = forms.ChoiceField(label=_('caller_id_name'),
                                       required=True,
                                       choices=ACCOUNTCODE_FIELD_LIST_NUM)
    destination_number = forms.ChoiceField(label=_('destination_number'),
                                           required=True,
                                           choices=CDR_FIELD_LIST_NUM)
    duration = forms.ChoiceField(label=_('duration'), required=True,
                                 choices=CDR_FIELD_LIST_NUM)
    billsec = forms.ChoiceField(label=_('billsec'), required=True,
                                choices=CDR_FIELD_LIST_NUM)
    hangup_cause_id = forms.ChoiceField(label=_('hangup_cause_id'),
                                        required=True,
                                        choices=CDR_FIELD_LIST_NUM)
    direction = forms.ChoiceField(label=_('direction'), required=True,
                                  choices=ACCOUNTCODE_FIELD_LIST_NUM)
    uuid = forms.ChoiceField(label=_('uuid'), required=True,
                             choices=ACCOUNTCODE_FIELD_LIST_NUM)
    remote_media_ip = forms.ChoiceField(label=_('remote_media_ip'),
                                        required=True,
                                        choices=ACCOUNTCODE_FIELD_LIST_NUM)
    start_uepoch = forms.ChoiceField(label=_('start_uepoch'), required=True,
                                     choices=CDR_FIELD_LIST_NUM)
    answer_uepoch = forms.ChoiceField(label=_('answer_uepoch'), required=True,
                                      choices=ACCOUNTCODE_FIELD_LIST_NUM)
    end_uepoch = forms.ChoiceField(label=_('end_uepoch'), required=True,
                                   choices=ACCOUNTCODE_FIELD_LIST_NUM)
    mduration = forms.ChoiceField(label=_('mduration'), required=True,
                                  choices=ACCOUNTCODE_FIELD_LIST_NUM)
    billmsec = forms.ChoiceField(label=_('billmsec'), required=True,
                                 choices=ACCOUNTCODE_FIELD_LIST_NUM)
    read_codec = forms.ChoiceField(label=_('read_codec'), required=True,
                                   choices=ACCOUNTCODE_FIELD_LIST_NUM)
    write_codec = forms.ChoiceField(label=_('write_codec'), required=True,
                                    choices=ACCOUNTCODE_FIELD_LIST_NUM)
    accountcode = forms.ChoiceField(label=_('accountcode'), required=True,
                                    choices=ACCOUNTCODE_FIELD_LIST_NUM)

    def __init__(self, user, *args, **kwargs):
        super(CDR_FileImport, self).__init__(*args, **kwargs)

    def clean_accountcode_csv(self):
        accountcode_csv = self.cleaned_data['accountcode_csv']
        return accountcode_csv

    def clean_accountcode(self):
        accountcode = self.cleaned_data['accountcode']
        accountcode_csv = self.cleaned_data['accountcode_csv']
        if not accountcode_csv and accountcode == 0:
            raise forms.ValidationError(
                'select accountcode column no else enter accountcode')
        return accountcode
