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

from django.core.cache import cache
from cdr.functions_def import prefix_list_string


def round_val(value):
    """
    Return rounded value to 2 decimal
    """
    return round(value, 2)


def rate_filter_range_field_chk(rate, rate_range, field_name):
    """
    Rate range fileds (e.g. >,>=,=,<=,<)
    are checked.
    """
    kwargs = {}
    if rate_range != '' and rate != '':
        if rate_range == 'gte':
            kwargs[field_name + '__gte'] = rate
        elif rate_range == 'gt':
            kwargs[field_name + '__gt'] = rate
        elif rate_range == 'eq':
            kwargs[field_name] = rate
        elif rate_range == 'lt':
            kwargs[field_name + '__lt'] = rate
        elif rate_range == 'lte':
            kwargs[field_name + '__lte'] = rate
    return kwargs


def rate_range():
    """
    Return list of filter for the rate symbol
    """
    choicelist = (('', 'All'),
                 ('gte', '>='),
                 ('gt', '>'),
                 ('eq', '='),
                 ('lt', '<'),
                 ('lte', '<='))
    return choicelist


def banned_prefix_qs(voipplan_id):
    """
    Banned Prefix queryset should be cached
    """
    from django.db import connection
    cursor = connection.cursor()
    sql_statement = (
        'SELECT voipbilling_ban_prefix.prefix_id FROM '
        'voipbilling_ban_prefix,voipbilling_banplan,voipbilling_voipplan_banplan '
        'WHERE voipbilling_ban_prefix.ban_plan_id = voipbilling_banplan.id '
        'AND voipbilling_banplan.id = voipbilling_voipplan_banplan.banplan_id '
        'AND voipbilling_voipplan_banplan.voipplan_id = %s')

    cursor.execute(sql_statement, [str(voipplan_id)])
    row = cursor.fetchall()
    result = []
    for record in row:
        modrecord = {}
        modrecord['prefix'] = record[0]
        result.append(modrecord)
    return result


def prefix_allowed_to_call(destination_number, voipplan_id):
    """
    Check destination number with ban prefix & voip_plan
    """
    destination_prefix_list = prefix_list_string(destination_number)
    # Cache the voipplan_id & banned_prefix query set
    cachekey = "banned_prefix_list_%s" % (str(voipplan_id))
    banned_prefix_list = cache.get(cachekey)
    if banned_prefix_list is None:
        banned_prefix_list = banned_prefix_qs(voipplan_id)
        cache.set(cachekey, banned_prefix_list, 60)

    flag = False
    for j in eval(destination_prefix_list):
        for i in banned_prefix_list:
            # Banned Prefix - VoIP call is not allowed
            if i['prefix'] == j:
                flag = True
                break
        # flag is false then calls are not allowed
        if flag:
            return False
    return True
