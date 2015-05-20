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

from cdr.functions_def import get_hangupcause_id


DICT_DISPOSITION = {
    'ANSWER': 1, 'ANSWERED': 1,
    'BUSY': 2,
    'NOANSWER': 3, 'NO ANSWER': 3,
    'CANCEL': 4,
    'CONGESTION': 5,
    'CHANUNAVAIL': 6,
    'DONTCALL': 7,
    'TORTURE': 8,
    'INVALIDARGS': 9,
    'FAIL': 10, 'FAILED': 10
}

# Try to match the Asterisk Dialstatus against Q.850
DISPOSITION_TRANSLATION = {
    0: 0,
    1: 16,      # ANSWER
    2: 17,      # BUSY
    3: 19,      # NOANSWER
    4: 21,      # CANCEL
    5: 34,      # CONGESTION
    6: 47,      # CHANUNAVAIL
    # DONTCALL: Privacy mode, callee rejected the call
    # Specific to Asterisk
    7: 21,       # DONTCALL
    # TORTURE: Privacy mode, callee chose to send caller to torture menu
    # Specific to Asterisk
    8: 21,       # TORTURE
    # INVALIDARGS: Error parsing Dial command arguments
    # Specific to Asterisk
    9: 47,       # INVALIDARGS
    10: 41,     # FAILED
}


def translate_disposition(disposition):
    """
    function to convert asterisk disposition to a internal hangup_cause_id
    """
    try:
        id_disposition = DICT_DISPOSITION.get(
            disposition.encode("utf-8"), 0)
        transdisposition = DISPOSITION_TRANSLATION[id_disposition]
    except:
        transdisposition = 0

    hangup_cause_id = get_hangupcause_id(transdisposition)

    return hangup_cause_id


def sanitize_cdr_field(field):
    """
    Sanitize CDR fields
    """
    try:
        field = field.decode('utf-8', 'ignore')
    except AttributeError:
        field = ''

    return field
