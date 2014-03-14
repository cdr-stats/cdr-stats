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
from django.contrib.auth.decorators import login_required, permission_required
from django.core.cache import cache
from dajaxice.decorators import dajaxice_register
from cdr.models import Switch
from cdr.decorators import check_user_detail
from datetime import datetime
import json
import logging


@permission_required('user_profile.real_time_calls', login_url='/')
@check_user_detail('accountcode')
@login_required
@dajaxice_register
def get_realtime_json(request, key_uuid):
    """
    Get realtime data
    """
    try:
        switch = Switch.objects.get(key_uuid=key_uuid)
    except:
        return False

    switch_id = switch.id
    now = datetime.today()
    key_date = "%d-%d-%d-%d-%d" % (now.year, now.month, now.day, now.hour, now.minute)

    if not request.user.is_superuser:
        accountcode = str(request.user.userprofile.accountcode)
    elif (hasattr(request.user, 'userprofile') and request.user.userprofile.accountcode and request.user.is_superuser):
        accountcode = str(request.user.userprofile.accountcode)
    elif request.user.is_superuser:
        accountcode = 'root'

    key = "%s-%d-%s" % (key_date, switch_id, str(accountcode))
    numbercall = cache.get(key)
    logging.debug("key:%s, accountcode:%s, numbercall:%s" % (key, accountcode, str(numbercall)))

    if not numbercall:
        numbercall = 0

    # import random
    # numbercall = random.randint(1, 300)
    # logging.debug('numbercall :::> %d' % numbercall)
    return json.dumps({'numbercall': numbercall})
