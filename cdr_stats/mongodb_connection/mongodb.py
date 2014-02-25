# -*- coding: utf-8 -*-
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
from pymongo.connection import Connection
from pymongo.errors import ConnectionFailure


try:
    connection = Connection(settings.MONGO_CDRSTATS['HOST'], settings.MONGO_CDRSTATS['PORT'])
    DBCON = connection[settings.MONGO_CDRSTATS['DB_NAME']]
    if settings.MONGO_CDRSTATS['USER'] and settings.MONGO_CDRSTATS['PASSWORD']:
        DBCON.autentificate(settings.MONGO_CDRSTATS['USER'], settings.MONGO_CDRSTATS['PASSWORD'])

    cdr_common = DBCON[settings.MONGO_CDRSTATS['CDR_COMMON']]
    daily_analytic = DBCON[settings.MONGO_CDRSTATS['DAILY_ANALYTIC']]
    monthly_analytic = DBCON[settings.MONGO_CDRSTATS['MONTHLY_ANALYTIC']]
    conc_call = DBCON[settings.MONGO_CDRSTATS['CONC_CALL']]
    conc_call_agg = DBCON[settings.MONGO_CDRSTATS['CONC_CALL_AGG']]
except ConnectionFailure, e:
    cdr_common = False
    daily_analytic = False
    monthly_analytic = False
    conc_call = False
    conc_call_agg = False
    DBCON = False
