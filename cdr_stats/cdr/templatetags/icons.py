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

from django import template
from django.conf import settings

register = template.Library()


def icon(icon_name):
    """Tag is used to create icon link

    >>> icon('test')
    'class="icon" style="text-decoration:none;background-image:url(/static/cdr-stats/icons/test.png);"'
    """
    return 'class="icon" style="text-decoration:none;background-image:url(%scdr-stats/icons/%s.png);"'\
        % (settings.STATIC_URL, icon_name)
register.simple_tag(icon)


def listicon(icon_name):
    """Tag is used to pass icon style in link

    >>> listicon('eye')
    'style="text-decoration:none;list-style-image:url(/static/cdr-stats/icons/test.png);"'
    """
    return 'style="text-decoration:none;list-style-image:url(%scdr-stats/icons/%s.png);"'\
           % (settings.STATIC_URL, icon_name)
register.simple_tag(listicon)
