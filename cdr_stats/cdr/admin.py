# CDR-Stats License
#
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
from django.contrib import admin
from django.utils.translation import ugettext as _
from cdr.models import HangupCause, CDR


#from django_lets_go.app_label_renamer import AppLabelRenamer
APP_LABEL = _('CDR')
#AppLabelRenamer(native_app_label='cdr', app_label=APP_LABEL).main()


def get_value_from_uni(j, row, field_name):
    """Get value from unique dict list

    >>> j = ['abc', 2, 3]

    >>> field_name = 'abc'

    >>> row = [1, 2, 3]

    >>> get_value_from_uni(j, row, field_name)
    '2'
    """
    return row[j[1] - 1] if j[0] == field_name else ''


"""
Asterisk cdr col

accountcode - 1
caller_id_number - 2
destination_number - 3
duration - 13
billsec - 14
hangup_cause_id - 15
uuid - 4
start_uepoch - 17
"""


# HangupCause
class HangupCauseAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'enumeration', 'cause', 'description')
    search_fields = ('code', 'enumeration',)

admin.site.register(HangupCause, HangupCauseAdmin)


# CDR
class CDRAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'switch', 'destination_number', 'dialcode', 'caller_id_number',
                    'duration', 'hangup_cause', 'direction', 'country', 'sell_cost')
    search_fields = ('destination_number', 'caller_id_number',)

admin.site.register(CDR, CDRAdmin)
