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
from voip_report.forms import voip_call_disposition_list


def get_disposition_id(name):
    """
    To get id from voip_call_disposition_list
    """
    for i in voip_call_disposition_list:        
        if i[1] == name:
            return i[0]        


def get_disposition_name(id):
    """
    To get name from voip_call_disposition_list
    """
    for i in voip_call_disposition_list:
        if i[0] == id:
            return i[1]