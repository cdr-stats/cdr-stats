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
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import UUIDField
import caching.base

CDR_TYPE = {
    "freeswitch": 1,
    "asterisk": 2,
    "yate": 3,
    "opensips": 4,
    "kamailio": 5,
    "API": 6,
    "CSV_IMPORT": 7,
}

DISPOSITION = (
    (1, _('ANSWER')),
    (2, _('BUSY')),
    (3, _('NOANSWER')),
    (4, _('CANCEL')),
    (5, _('CONGESTION')),
    (6, _('CHANUNAVAIL')),
    (7, _('DONTCALL')),
    (8, _('TORTURE')),
    (9, _('INVALIDARGS')),
)

SWITCH_TYPE = (
    ('freeswitch', _('FreeSWITCH')),
    ('asterisk', _('Asterisk')),
)


class Switch(caching.base.CachingMixin, models.Model):
    """This defines the Switch

    **Attributes**:

        * ``name`` - Name of switch.
        * ``ipaddress`` - ipaddress

    **Name of DB table**: voip_switch
    """
    name = models.CharField(max_length=100, blank=False,
                            null=True, unique=True)
    ipaddress = models.CharField(max_length=100, blank=False,
                            null=False, unique=True)
    #switch_type = models.CharField(choices=SWITCH_TYPE,
    #                        default='freeswitch',
    #                        max_length=100, null=False)
    key_uuid = UUIDField(auto=True)

    objects = caching.base.CachingManager()

    def __unicode__(self):
        return '[%s] %s' % (self.id, self.ipaddress)

    class Meta:
        verbose_name = _("Switch")
        verbose_name_plural = _("Switches")
        db_table = "voip_switch"


class HangupCause(caching.base.CachingMixin, models.Model):
    """This defines the HangupCause

    **Attributes**:

        * ``code`` - ITU-T Q.850 Code.
        * ``enumeration`` - Enumeration
        * ``cause`` - cause
        * ``description`` - cause description

    **Name of DB table**: hangup_cause
    """
    code = models.PositiveIntegerField(unique=True, verbose_name=_('Code'),
                                       help_text=_("ITU-T Q.850 Code"))
    enumeration = models.CharField(max_length=100, null=True, blank=True,
                                   verbose_name=_('Enumeration'))
    cause = models.CharField(max_length=100, null=True, blank=True,
                             verbose_name=_('Cause'))
    description = models.TextField(null=True, blank=True,
                                   verbose_name=_('Description'))

    def __unicode__(self):
        return '[%s] %s' % (self.code, self.enumeration)

    class Meta:
        verbose_name = _("Hangupcause")
        verbose_name_plural = _("Hangupcauses")
        db_table = "hangup_cause"
