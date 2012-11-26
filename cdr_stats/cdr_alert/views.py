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
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required,\
    permission_required
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.utils.translation import gettext as _
from django.conf import settings
from cdr_alert.models import Alarm
from cdr_alert.constants import ALARM_COLUMN_NAME
from common_notification.views import notice_count
from common.common_functions import current_view, get_pagination_vars,\
    variable_value, ceil_strdate


@permission_required('cdr_alert.view_alarm', login_url='/')
@login_required
def alert_list(request):
    """Alarm list for the logged in user

    **Attributes**:

        * ``template`` - frontend/cdr_alert/alert_list.html

    **Logic Description**:

        * List all alarms which belong to the logged in user.
    """
    sort_col_field_list = ['id', 'name', 'period', 'type','updated_date']
    default_sort_field = 'id'
    pagination_data =\
        get_pagination_vars(request, sort_col_field_list, default_sort_field)

    PAGE_SIZE = pagination_data['PAGE_SIZE']
    sort_order = pagination_data['sort_order']

    alarm_list = Alarm.objects\
        .filter(user=request.user).order_by(sort_order)

    template_name = 'frontend/cdr_alert/alert_list.html'

    PAGE_SIZE = settings.PAGE_SIZE
    template_data = {
        'module': current_view(request),
        'rows': alarm_list,
        'total_count': alarm_list.count(),
        'PAGE_SIZE': PAGE_SIZE,
        'ALARM_COLUMN_NAME': ALARM_COLUMN_NAME,
        'col_name_with_order': pagination_data['col_name_with_order'],
        'notice_count': notice_count(request),
    }

    return render_to_response(template_name, template_data,
        context_instance=RequestContext(request))