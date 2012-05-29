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
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from user_profile.models import UserProfile, Customer, Staff


class UserChangeDetailForm(ModelForm):
    """A form used to change the detail of a user in the Customer UI."""
    email = forms.CharField(label=_('Email address'), required=True)
    class Meta:
        model = User
        fields = ["last_name", "first_name", "email"]

    def __init__(self, user, *args, **kwargs):
        self.user = user        
        super(UserChangeDetailForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        """Saves the detail."""
        self.user.last_name = self.cleaned_data["last_name"]
        self.user.first_name = self.cleaned_data["first_name"]
        self.user.email = self.cleaned_data["email"]
        if commit:
            self.user.save()
        return self.user


class UserChangeDetailExtendForm(ModelForm):
    """A form used to change the detail of a user in the Customer UI."""
    class Meta:
        model = UserProfile
        fields = ["address", "city", "state", "country", "zip_code", "phone_no",
                  "fax", "company_name", "company_website", "language", "note"]

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(UserChangeDetailExtendForm, self).__init__(*args, **kwargs)


class CheckPhoneNumberForm(forms.Form):
    """A form used to check the phone number in the Customer UI."""
    phone_number = forms.CharField(label=_('Phone Number'), required=True,
                                help_text=_("Check number is authorised to call"))


class UserProfileForm(ModelForm):

    class Meta:
        model = UserProfile
