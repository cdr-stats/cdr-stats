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
from django.conf import settings


def cdr_stats_common_template_variable(request):
    """Return common_template_variable"""
    cdr_stats_page_size = settings.PAGE_SIZE if settings.PAGE_SIZE else 10
    return {'cdr_stats_page_size': cdr_stats_page_size}
