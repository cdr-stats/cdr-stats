# -*- coding: utf-8 -*-
#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2014 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from django.conf import settings
from django.db.models import signals
from django.utils.translation import ugettext_noop as _
from user_profile.constants import NOTICE_TYPE


# Info about management.py
# http://stackoverflow.com/questions/4455533/what-is-management-py-in-django

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification

    def create_notice_types(app, created_models, verbosity, **kwargs):
        kwargs = {}
        kwargs['default'] = NOTICE_TYPE.average_length_of_call
        notification.create_notice_type("average_length_of_call",
                                        _("ALOC (average length of call)"),
                                        _("average length of call"), **kwargs)
        kwargs['default'] = NOTICE_TYPE.answer_seize_ratio
        notification.create_notice_type("answer_seize_ratio",
                                        _("ASR (answer seize ratio)"),
                                        _("answer seize ratio"), **kwargs)
        kwargs['default'] = NOTICE_TYPE.blacklist_prefix
        notification.create_notice_type("blacklist_prefix",
                                        _("Blacklist Prefix"),
                                        _("blacklist prefix"), **kwargs)
        kwargs['default'] = NOTICE_TYPE.whitelist_prefix
        notification.create_notice_type("whitelist_prefix",
                                        _("Whitelist Prefix"),
                                        _("whitelist prefix"), **kwargs)

    signals.post_syncdb.connect(create_notice_types, sender=notification)
else:
    print "Skipping creation of NoticeTypes as notification app not found"
