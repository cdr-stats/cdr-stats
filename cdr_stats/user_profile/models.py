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

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from voip_billing.models import VoIPPlan
from django_lets_go.language_field import LanguageField
from django_countries.fields import CountryField


class UserProfile(models.Model):

    """This defines extra features for the user

    **Attributes**:

        * ``accountcode`` - Account name.
        * ``address`` -
        * ``city`` -
        * ``state`` -
        * ``address`` -
        * ``country`` -
        * ``zip_code`` -
        * ``phone_no`` -
        * ``fax`` -
        * ``company_name`` -
        * ``company_website`` -
        * ``language`` -
        * ``note`` -

    **Relationships**:

        * ``user`` - Foreign key relationship to the User model.
        * ``userprofile_gateway`` - ManyToMany
        * ``userprofile_voipservergroup`` - ManyToMany
        * ``dialersetting`` - Foreign key relationship to the DialerSetting \
        model.

    **Name of DB table**: user_profile
    """
    user = models.OneToOneField(User)
    voipplan = models.ForeignKey(VoIPPlan, verbose_name=_('VoIP plan'),
                                 help_text=_("select VoIP Plan"))
    accountcode = models.CharField(max_length=50, verbose_name=_('account code'),
                                   unique=True)
    address = models.CharField(blank=True, null=True, max_length=200,
                               verbose_name=_('address'))
    city = models.CharField(max_length=120, blank=True, null=True,
                            verbose_name=_('city'))
    state = models.CharField(max_length=120, blank=True, null=True,
                             verbose_name=_('state'))
    country = CountryField(blank=True, null=True, verbose_name=_('country'))
    zip_code = models.CharField(max_length=120, blank=True, null=True,
                                verbose_name=_('zip code'))
    phone_no = models.CharField(max_length=90, blank=True, null=True,
                                verbose_name=_('phone number'))
    fax = models.CharField(max_length=90, blank=True, null=True,
                           verbose_name=_('fax Number'))
    company_name = models.CharField(max_length=90, blank=True, null=True,
                                    verbose_name=_('company name'))
    company_website = models.URLField(max_length=90, blank=True, null=True,
                                      verbose_name=_('company website'))
    language = LanguageField(blank=True, null=True, verbose_name=_('language'))
    note = models.CharField(max_length=250, blank=True, null=True,
                            verbose_name=_('note'))
    multiple_email = models.TextField(blank=True, null=True,
                                      verbose_name=_('report mail list'),
                                      help_text=_('enter a valid e-mail address separated by commas.'))

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = (
            ("view_api_explorer", _('can view API-Explorer')),
            ("dashboard", _('can view CDR dashboard')),
            ("search", _('can view CDR')),
            ("cdr_detail", _('can view CDR detail')),
            ("daily_comparison", _('can view CDR hourly report')),
            ("overview", _('can view CDR overview')),
            ("concurrent_calls", _('can view CDR concurrent calls')),
            ("real_time_calls", _('can view CDR realtime')),
            ("by_country", _('can view CDR country report')),
            ("world_map", _('can view CDR world map')),
            ("mail_report", _('can view CDR mail report')),
            ("diagnostic", _('can view diagnostic report')),
            ("daily_billing", _('can view daily billing report')),
            ("hourly_billing", _('can view hourly billing report')),
            ("simulator", _('can view voip call simulator')),
            ("call_rate", _('can view voip call rate')),
            ("export_call_rate", _('can export voip call rate')),
        )
        db_table = 'user_profile'
        verbose_name = _("user profile")
        verbose_name_plural = _("user profile")


class Customer(User):

    """
    Django user application allows you to store user accounts for customer without
    is_staff/is_superuser privilege status
    """

    class Meta:
        proxy = True
        app_label = 'auth'
        verbose_name = _('customer')
        verbose_name_plural = _('customers')


class Staff(User):

    """
    Django user application allows you to store user accounts for staff with
    is_staff/is_superuser privilege status
    """

    class Meta:
        proxy = True
        app_label = 'auth'
        verbose_name = _('admin')
        verbose_name_plural = _('admins')

    def save(self, **kwargs):
        if not self.pk:
            self.is_staff = 1
            self.is_superuser = 1
        super(Staff, self).save(**kwargs)
