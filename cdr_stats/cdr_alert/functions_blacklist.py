#
# CDR-Stats License
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
from django.conf import settings
from cdr.functions_def import remove_prefix, prefix_list_string, get_country_id_prefix
from cdr_alert.models import Blacklist, Whitelist
from cdr_alert.tasks import blacklist_whitelist_notification


def chk_prefix_in_whitelist(prefix_list):
    """Check destination no with allowed prefix

    >>> chk_prefix_in_whitelist([34, 345, 3456])
    False

    >>> chk_prefix_in_whitelist('')
    False
    """
    if not prefix_list:
        return False
    white_prefix_list = Whitelist.objects.all()
    flag = False
    if white_prefix_list:
        for j in eval(prefix_list):
            for i in white_prefix_list:
                # Allowed Prefix
                if i.phonenumber_prefix == j:
                    flag = True
                    break

            # if flag is true - allowed
            if flag:
                # notice_type = 4 whitelist
                blacklist_whitelist_notification.delay(4)
                return True

    # no whitelist define
    return False


def chk_prefix_in_blacklist(prefix_list):
    """Check destination no with ban prefix

    >>> chk_prefix_in_blacklist([34, 345, 3456])
    True

    >>> chk_prefix_in_blacklist([])
    True
    """
    if not prefix_list:
        return True
    banned_prefix_list = Blacklist.objects.all()
    flag = False
    if banned_prefix_list:
        for j in eval(prefix_list):
            for i in banned_prefix_list:
                # Banned Prefix
                if i.phonenumber_prefix == j:
                    flag = True
                    break

            # if flag is true - not allowed
            if flag:
                # notice_type = 3 blacklist
                blacklist_whitelist_notification.delay(3)
                return False

    # no blacklist is defined
    return True


def verify_auth_dest_number(destination_number):
    """
    >>> verify_auth_dest_number('1234567890')
    {
        'authorized': 0,
        'country_id': 0,
        'prefix_id': 0,
    }
    """
    # remove prefix
    sanitized_destination = remove_prefix(destination_number, settings.PREFIX_TO_IGNORE)

    prefix_list = prefix_list_string(sanitized_destination)

    authorized = 1  # default
    # check destion against whitelist
    authorized = chk_prefix_in_whitelist(prefix_list)
    if authorized:
        authorized = 1
    else:
        # check against blacklist
        authorized = chk_prefix_in_blacklist(prefix_list)
        if not authorized:
            # not allowed destination
            authorized = 0

    if (len(sanitized_destination) < settings.PN_MIN_DIGITS
            or sanitized_destination[:1].isalpha()):
        # It might be an extension
        country_id = 0
    elif (len(sanitized_destination) >= settings.PN_MIN_DIGITS
          and len(sanitized_destination) <= settings.PN_MAX_DIGITS):
        # It might be an local call
        # Need to add coma for get_country_id_prefix to eval correctly
        prefix_list = prefix_list_string(str(settings.LOCAL_DIALCODE) + sanitized_destination)
        (country_id, prefix_id) = get_country_id_prefix(prefix_list)
    else:
        # International call
        (country_id, prefix_id) = get_country_id_prefix(prefix_list)

    destination_data = {
        'authorized': authorized,
        'country_id': country_id,
        'prefix_id': prefix_id,
    }
    return destination_data
