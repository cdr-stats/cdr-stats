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
from django.utils.translation import ugettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML
from crispy_forms.bootstrap import FormActions


class LoginForm(forms.Form):

    """Client Login Form"""
    user = forms.CharField(max_length=30, label=_('username'), required=True)
    user.widget.attrs['placeholder'] = 'Username'
    password = forms.CharField(max_length=30, label=_('password'), required=True,
                               widget=forms.PasswordInput())
    password.widget.attrs['placeholder'] = 'Password'

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = '/login/'
        self.helper.form_show_labels = False
        self.helper.form_class = 'form-inline well'
        self.helper.layout = Layout(
            Div(
                Div('user', css_class='col-xs-3'),
                Div('password', css_class='col-xs-3'),
            ),
            FormActions(
                Submit('submit', 'Login'),
                HTML('<a class="btn btn-warning" href="/password_reset/">%s?</a>' % _('forgot password').capitalize()),
            ),
        )
