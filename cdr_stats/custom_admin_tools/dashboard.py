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

from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.conf import settings

from admin_tools.dashboard import modules, Dashboard, AppIndexDashboard
from admin_tools.utils import get_admin_site_name


class HistoryDashboardModule(modules.LinkList):
    title = 'History'

    def init_with_context(self, context):
        request = context['request']
        # we use sessions to store the visited pages stack
        history = request.session.get('history', [])

        for item in history:
            self.children.append(item)

        # add the current page to the history
        history.insert(0, {
            'title': context['title'],
            'url': request.META['PATH_INFO']
        })
        if len(history) > 10:
            history = history[:10]
        request.session['history'] = history


class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard
    """

    def init_with_context(self, context):
        # we want a 3 columns layout
        self.columns = 3
        site_name = get_admin_site_name(context)

        #self.children.append(
        #            HistoryDashboardModule()
        #)

        self.children.append(modules.Group(
            title="General",
            display="tabs",
            children=[
                modules.AppList(
                    title=_('user').capitalize(),
                    models=('django.contrib.*', 'user_profile.*'),
                ),
                modules.AppList(
                    _('task manager').title(),
                    models=('djcelery.*', ),
                ),
                modules.AppList(
                    _('dashboard stats').title(),
                    models=('admin_tools_stats.*', ),
                ),
                modules.RecentActions(_('Recent Actions'), 5),
            ]
        ))

        self.children.append(modules.AppList(
            _('CDR Voip'),
            models=('cdr.*',),
        ))

        self.children.append(modules.AppList(
            _('alert').title(),
            models=('cdr_alert.*', ),
        ))

        self.children.append(modules.AppList(
            _('country dialcode').title(),
            models=('country_dialcode.*', ),
        ))

        self.children.append(modules.AppList(
            _('Voip gateway').title(),
            models=('voip_gateway.*', ),
        ))

        self.children.append(modules.AppList(
            _('Voip billing').title(),
            models=('voip_billing.*', ),
        ))

        # append a link list module for "quick links"
        self.children.append(modules.LinkList(
            _('quick links').capitalize(),
            layout='inline',
            draggable=True,
            deletable=True,
            collapsible=True,
            children=[
                [_('Go to CDR-Stats.org'), 'http://www.cdr-stats.org/'],
                [_('change password').capitalize(),
                 reverse('%s:password_change' % site_name)],
                [_('log out').capitalize(), reverse('%s:logout' % site_name)],
            ]
        ))

        if not settings.DEBUG:
            # append a feed module
            self.children.append(modules.Feed(
                _('Latest CDR-Stats News'),
                feed_url='http://www.cdr-stats.org/category/blog/feed/',
                limit=5
            ))


class CustomAppIndexDashboard(AppIndexDashboard):
    """
    Custom app index dashboard for admin.
    """
    # we disable title because its redundant with the model list module
    title = ''

    def __init__(self, *args, **kwargs):
        AppIndexDashboard.__init__(self, *args, **kwargs)

        #TODO: Find out better way
        if str(self.app_title) == 'Voip_Gateway':
            app_title = _('voip gateway')
            models = ['voip_gateway.*']
        elif str(self.app_title) == 'Voip_Billing':
            app_title = _('Voip Billing')
            models = ['voip_billing.*']
        elif str(self.app_title) == 'Cdr_Alert':
            app_title = _('CDR Alert')
            models = ['cdr_alert.*']
        else:
            app_title = self.app_title
            models = self.models

        # append a model list module and a recent actions module
        self.children += [
            #modules.ModelList(self.app_title, self.models),
            modules.ModelList(app_title, models),
            modules.RecentActions(
                _('recent actions').title(),
                include_list=self.get_app_content_types(),
                limit=5
            )
        ]

    def init_with_context(self, context):
        """
        Use this method if you need to access the request context.
        """
        return super(CustomAppIndexDashboard, self).init_with_context(context)
