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
from django.db import models
from django.utils.translation import ugettext_lazy as _
from common.intermediate_model_base_class import Model
from voip_gateway.constants import GATEWAY_STATUS


class Gateway(Model):
    """
    Gateway

    This defines the trunk to deliver the Voip Calls.
    Each Gateway are route that support different protocol and different
    set of rules to alter the dialed number
    """
    name = models.CharField(unique=True, max_length=255, verbose_name=_('Name'),
                            help_text=_("Enter Gateway Name"))
    description = models.TextField(verbose_name=_('Description'),
                               help_text=_("Short description about Provider"))
    addprefix = models.CharField(max_length=60, blank=True)
    removeprefix = models.CharField(max_length=60, blank=True)
    protocol = models.CharField(max_length=60)
    hostname = models.CharField(max_length=240)
    secondused = models.IntegerField(null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Date'))
    updated_date = models.DateTimeField(auto_now=True)

    failover = models.ForeignKey('self', null=True, blank=True,
                related_name="Failover", help_text=_("Select Gateway"))
    addparameter = models.CharField(max_length=360, blank=True)
    count_call = models.IntegerField(null=True, blank=True)
    count_using = models.IntegerField(null=True, blank=True)
    maximum_call = models.IntegerField(null=True, blank=True)
    status = models.IntegerField(choices=list(GATEWAY_STATUS),
        default=GATEWAY_STATUS.INACTIVE, verbose_name=_("Gateway Status"),
        blank=True, null=True)
    max_call_gateway = models.IntegerField(null=True, blank=True,
        verbose_name=_("Max Call Gateway"),
        help_text=_("Select Gateway to route the call if the maximum call is reached"))

    class Meta:
        db_table = u'voip_gateway'        
        verbose_name = _("Gateway")
        verbose_name_plural = _("Gateways")

    def __unicode__(self):
            return u"%s" % self.name


class Provider(Model):
    """
    Provider

    This defines the Voip Provider you want to use to deliver your calls.
    Each provider will be associated to a Gateway.
    """
    name = models.CharField(unique=True, max_length=255, verbose_name=_('Name'),
                            help_text=_("Enter Provider Name"))
    description = models.TextField(verbose_name=_('Description'),
                               help_text=_("Short description about Provider"))
    metric = models.IntegerField(default=10, verbose_name=_('Metric'),
                                 help_text=_("Enter metric in digit"))
    gateway = models.ForeignKey(Gateway, null=True, blank=True,
                                help_text=_("Select Gateway"))
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Date'))
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = u'voip_provider'        
        verbose_name = _("Provider")
        verbose_name_plural = _("Providers")

    def __unicode__(self):
            return u"%s" % self.name
