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
from django import *
from django import forms
from django.forms import *
from django.contrib import *
from django.contrib.admin.widgets import *
from django.conf import settings
from django.core.validators import validate_email
from django.utils.translation import ugettext_lazy as _

from common.common_functions import comp_day_range
from cdr.models import *
from cdr.functions_def import *
from user_profile.models import UserProfile

STRING_SEARCH_TYPE_LIST = ((2, _('Begins with')),
                           (3, _('Contains')),
                           (4, _('Ends with')),
                           (1, _('Equals')),
                           )

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

DATE_HELP_TEXT = _("Please use the following format")+": <em>YYYY-MM-DD</em>."
COUNTRY_HELP_TEXT = _('Hold down "Ctrl", "Command" on Mac, to select more than one.')


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
    """Form used to search on general parameters in the Customer UI."""
    caller = forms.CharField(label=_('Caller ID'), required=False)
    caller_type = forms.ChoiceField(label='', required=False,
                                    choices=STRING_SEARCH_TYPE_LIST)
    caller_type.widget.attrs['class'] = 'input-small'

    destination = forms.CharField(label=_('Destination'), required=False)
    destination_type = forms.ChoiceField(label='', required=False,
                                         choices=STRING_SEARCH_TYPE_LIST)
    destination_type.widget.attrs['class'] = 'input-small'

    accountcode = forms.CharField(label=_('Account Code'), required=False)
    accountcode_type = forms.ChoiceField(label='', required=False,
                                         choices=STRING_SEARCH_TYPE_LIST)
    accountcode_type.widget.attrs['class'] = 'input-small'

    duration = forms.CharField(label=_('Duration'), required=False)
    duration_type = forms.ChoiceField(label='', required=False,
                                      choices=COMPARE_LIST)
    duration_type.widget.attrs['class'] = 'input-small'

    hangup_cause = forms.ChoiceField(label=_('Hangup cause'), required=False,
                                     choices=hc_list_with_all())

    switch = forms.ChoiceField(label=_('Switch'), required=False,
                               choices=get_switch_list())

    country_id = forms.MultipleChoiceField(label=_('Country'), required=False,
                                           choices=country_list_with_all(),
                                           help_text=COUNTRY_HELP_TEXT)

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['switch'].choices = sw_list_with_all()


class CdrSearchForm(SearchForm):
    """Form used to search calls in the Customer UI."""
    from_date = CharField(label=_('From'), required=True, max_length=10)
    to_date = CharField(label=_('To'), required=True, max_length=10)
    direction = forms.TypedChoiceField(label=_('Direction'), required=False, coerce=bool,
                choices=(('inbound', _('Inbound')), ('outbound', _('Outbound'))))
    result = forms.TypedChoiceField(label=_('Result'), required=False, coerce=bool,
                choices=((1, _('Minutes')), (2, _('Seconds'))),
                widget=forms.RadioSelect)
    records_per_page = forms.ChoiceField(label=_('CDR per page'),
                                         required=False, initial=settings.PAGE_SIZE,
                                         choices=PAGE_SIZE_LIST)
    records_per_page.widget.attrs['class'] = 'input-mini'

    def __init__(self, *args, **kwargs):
        super(CdrSearchForm, self).__init__(*args, **kwargs)
        self.fields['records_per_page'].widget.attrs['onchange'] = 'this.form.submit();'


class CountryReportForm(CdrSearchForm):
    """Form used to get country vise calls report in the Customer UI."""
    def __init__(self, *args, **kwargs):
        super(CountryReportForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['from_date', 'to_date', 'country_id', 'duration',
                                'duration_type', 'switch']


class CdrOverviewForm(CdrSearchForm):
    """Form used to get overview of calls in the Customer UI."""
    def __init__(self, *args, **kwargs):
        super(CdrOverviewForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['from_date', 'to_date', 'destination', 'destination_type',
                                'switch']


class CompareCallSearchForm(SearchForm):
    """Form used to search calls for comparison in the Customer UI."""
    from_date = forms.CharField(label=_('Select date'), required=True,
                                max_length=10)

    comp_days = forms.ChoiceField(label='', required=False, choices=comp_day_range())
    comp_days.widget.attrs['class'] = 'input-small'
    graph_view = forms.ChoiceField(label=_('Graph'), required=False,
                 choices=((1, _('Calls per Hour')), (2,_('Minutes per Hour'))))
    check_days = forms.TypedChoiceField(label=_('Check with'), required=False, coerce=bool,
                 choices=((1, _('Previous days')), (2, _('Same day of the week'))),
                 widget=forms.RadioSelect)

    def __init__(self, *args, **kwargs):
        super(CompareCallSearchForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['from_date','comp_days', 'check_days', 'destination',
                                'destination_type', 'graph_view', 'switch']


class ConcurrentCallForm(CdrSearchForm):
    """Form used for concurrent calls in the Customer UI."""
    def __init__(self, *args, **kwargs):
        super(ConcurrentCallForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['from_date', 'result', 'switch']
        self.fields['from_date'].label = _('Select date')


class SwitchForm(SearchForm):
    """Form used to get the list of switches in the Customer UI."""
    def __init__(self, *args, **kwargs):
        super(SwitchForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['switch']
        self.fields['switch'].widget.attrs['onchange'] = 'this.form.submit();'


class loginForm(forms.Form):
    """Form used to login of a user in the Customer UI."""
    user = forms.CharField(max_length=40, label=_('Login'), required=True)
    user.widget.attrs['class'] = 'input-small'
    user.widget.attrs['placeholder'] = 'Username'
    password = forms.CharField(max_length=40, label=_('Password'),
                               required=True, widget=forms.PasswordInput())
    password.widget.attrs['class'] = 'input-small'
    password.widget.attrs['placeholder'] = 'Password'

    
class EmailReportForm(ModelForm):
    """Form used to change the detail of a user in the Customer UI."""
    multiple_email = forms.CharField(max_length=300, required=False,
                           label=_("Enter e-mails to receive the mail report, if more than one separate by comma"))
    multiple_email.widget.attrs['class'] = 'span6'

    class Meta:
        model = UserProfile
        fields = ('multiple_email',)

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
                mail_list.append((str(email)))
            except:
                raise forms.ValidationError('%s is not a valid e-mail address.' % email)

        # Always return the cleaned data.
        mail_list = ','.join(mail_list)
        return mail_list


class FileImport(forms.Form):
    """General Form : CSV file upload"""
    csv_file = forms.FileField(label=_("Upload CSV File "), required=True,
        error_messages={'required': 'Please upload File'},
        help_text=_("Browse CSV file"))

    def clean_file(self):
        """Form Validation :  File extension Check"""
        filename = self.cleaned_data["csv_file"]
        file_exts = (".csv", )
        if not str(filename).split(".")[1].lower() in file_exts:
            raise forms.ValidationError(_(u'Document types accepted: %s' %\
                                          ' '.join(file_exts)))
        else:
            return filename


class CDR_FileImport(FileImport):
    """Admin Form : Import CSV file with phonebook CDR_FIELD_LIST"""
    switch = forms.ChoiceField(label=_("Switch"),
             choices=get_switch_list(), required=True, help_text=_("Select switch"))
    accountcode = forms.CharField(label=_('Account code'), required=True)

    def __init__(self, user, *args, **kwargs):
        super(CDR_FileImport, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['switch', 'accountcode', 'csv_file']