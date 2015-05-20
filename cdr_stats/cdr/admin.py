# CDR-Stats License
#
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2015 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#
from django.contrib import admin
from cdr.models import HangupCause, CDR


# HangupCause
class HangupCauseAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'enumeration', 'cause', 'description')
    search_fields = ('code', 'enumeration',)

admin.site.register(HangupCause, HangupCauseAdmin)


# CDR
class CDRAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'starting_date', 'switch', 'destination_number', 'dialcode', 'caller_id_number',
                    'duration', 'hangup_cause', 'direction', 'country', 'sell_cost',)
    search_fields = ('destination_number', 'caller_id_number',)

admin.site.register(CDR, CDRAdmin)
