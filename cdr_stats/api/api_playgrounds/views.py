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

from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.conf import settings
from cdr.views import notice_count
from common.common_functions import current_view
import os


@login_required
def api_list_view(request):
    """
    Get List of API names & their links
    """
    exclude_file = ['__init__.py', 'urls.py', 'views.py']
    list_of_api = []
    os.chdir(settings.APPLICATION_DIR + "/api/api_playgrounds/")
    for files in os.listdir("."):
        if files.endswith(".py") and files.endswith(".py"):
            if str(files) not in exclude_file:
                api_arr = str(files).split('_playground.py')
                api_link = '/api-explorer/' + api_arr[0].replace("_", "-")
                list_of_api.append({'api_name': api_arr[0],
                                    'api_link': api_link})

    template = 'frontend/api/api_list.html'
    data = {
        'list_of_api': list_of_api,
        'notice_count': notice_count(request),
        'module': current_view(request),
    }
    return render_to_response(template, data,
        context_instance=RequestContext(request))
