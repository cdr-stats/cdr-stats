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

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.conf import settings
from django.template.context import RequestContext
from django.utils.translation import ugettext as _
from django_lets_go.common_functions import get_news
from frontend.forms import LoginForm
from collections import OrderedDict
from cdr.cdr_importer import check_connection_sql, get_to_import_cdr_count

news_url = settings.NEWS_URL


def index(request):
    """Index Page of CDR-Stats

    **Attributes**:

        * ``template`` - frontend/index.html
        * ``form`` - loginForm
    """
    errorlogin = ''
    loginform = LoginForm()

    if request.GET.get('acc_code_error'):
        if request.GET['acc_code_error'] == 'true':
            errorlogin = _('account code is not assigned!')

    if request.GET.get('voip_plan_error'):
        if request.GET['voip_plan_error'] == 'true':
            errorlogin = _('voip plan is not attached to user!')

    data = {
        'loginform': loginform,
        'errorlogin': errorlogin,
        'news': get_news(settings.NEWS_URL),
    }
    return render_to_response('frontend/index.html', data, context_instance=RequestContext(request))


@permission_required('user_profile.diagnostic', login_url='/')
@login_required
def diagnostic(request):
    """
    To run diagnostic test

    **Attributes**:

        * ``template`` - frontend/diagnostic.html
    """
    error_msg = ''
    info_msg = ''

    engine = settings.DATABASES['import_cdr']['ENGINE']
    hostname = settings.DATABASES['import_cdr']['HOST']
    port = settings.DATABASES['import_cdr']['PORT']
    db_name = settings.DATABASES['import_cdr']['NAME']
    table_name = 'cdr_import'
    username = 'YYYYYYYYYYYY'
    # password = 'XXXXXXXXXXXX'

    conn_status = check_connection_sql()
    if conn_status:
        (total_cdr, not_imported_cdr) = get_to_import_cdr_count()
    else:
        (total_cdr, not_imported_cdr) = (0, 0)

    if not conn_status:
        error_msg = _("Please review the 'DATABASES' settings in the config file (/usr/share/cdrstats/cdr_stats/settings_local.py). Make sure that the Database `CDR-Pusher` is created.")
        info_msg = _("After changes in your 'settings_local.py' conf file, you will need to restart celery: $ /etc/init.d/cdr-stats-celeryd restart")

    conn_report = OrderedDict([
                              ('engine', engine),
                              ('hostname', hostname),
                              ('port', port),
                              ('database name', db_name),
                              ('username', username),
                              ('table name', table_name),
                              ('connection status', conn_status),
                              ('total CDR', total_cdr),
                              ('total not imported CDR', not_imported_cdr),
                              ])

    data = {
        'info_msg': info_msg,
        'error_msg': error_msg,
        'conn_report': conn_report,
    }
    return render_to_response('frontend/diagnostic.html', data, context_instance=RequestContext(request))


def logout_view(request):
    """Log out from application"""
    try:
        del request.session['has_notified']
    except KeyError:
        pass

    logout(request)
    # set language cookie
    response = HttpResponseRedirect('/')
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, request.LANGUAGE_CODE)
    return response


def login_view(request):
    """Check User credentials

    **Attributes**:

        * ``form`` - LoginForm
        * ``template`` - frontend/index.html

    **Logic Description**:

        * Submitted user credentials need to be checked. If it is not valid
          then the system will redirect to the login page.
        * If submitted user credentials are valid then system will redirect to
          the dashboard.
    """
    errorlogin = ''
    loginform = LoginForm(request.POST or None)
    if request.method == 'POST':
        if loginform.is_valid():
            cd = loginform.cleaned_data
            user = authenticate(username=cd['user'], password=cd['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    request.session['has_notified'] = False
                    # Redirect to a success page (dashboard).
                    return HttpResponseRedirect('/dashboard/')
                else:
                    # Return a 'disabled account' error message
                    errorlogin = _('disabled Account')
            else:
                # Return an 'invalid login' error message.
                errorlogin = _('invalid Login.')
        else:
            # Return an 'Valid User Credentials' error message.
            errorlogin = _('enter valid user credentials.')

    data = {
        'loginform': loginform,
        'errorlogin': errorlogin,
        'news': get_news(news_url),
        'is_authenticated': request.user.is_authenticated(),
    }
    return render_to_response('frontend/index.html', data, context_instance=RequestContext(request))


def pleaselog(request):
    data = {
        'loginform': LoginForm(),
        'notlogged': True,
    }
    return render_to_response('frontend/index.html', data, context_instance=RequestContext(request))
