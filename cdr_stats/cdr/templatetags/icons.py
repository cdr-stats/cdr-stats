#
# Newfies-Dialer License
# http://www.newfies-dialer.org
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

from django import template
from django.conf import settings

register = template.Library()


def icon(icon_name):
    return 'class="icon" style="text-decoration:none;background-image:url(' \
           + settings.STATIC_URL + 'newfies/icons/' + icon_name + '.png);"'
register.simple_tag(icon)


def listicon(icon_name):
    return 'style="text-decoration:none;list-style-image:url(' \
           + settings.STATIC_URL + 'newfies/icons/' + icon_name + '.png);"'
register.simple_tag(listicon)
