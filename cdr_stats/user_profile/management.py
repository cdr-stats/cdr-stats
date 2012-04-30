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

from django.conf import settings
from django.db.models import signals
from django.utils.translation import ugettext_noop as _


if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification

    def create_notice_types(app, created_models, verbosity, **kwargs):
        notification.create_notice_type("average_length_of_call",
                                        _("ALOC (Average Length of Call)"),
                                        _("Average Length of Call"),
                                        1)
        notification.create_notice_type("answer_seize_ratio",
                                        _("ASR (Answer Seize Ratio)"),
                                        _("Answer Seize Ratio"),
                                        2)
        notification.create_notice_type("blacklist_prefix",
                                        _("Blacklist Prefix"),
                                        _("Blacklist Prefix"),
                                        3)
        notification.create_notice_type("whitelist_prefix",
                                        _("Whitelist Prefix"),
                                        _("Whitelist Prefix"),
                                        4)
    signals.post_syncdb.connect(create_notice_types, sender=notification)
else:
    print "Skipping creation of NoticeTypes as notification app not found"
