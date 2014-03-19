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

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.conf import settings
from django.template.context import RequestContext
from django.utils.translation import ugettext as _
from pymongo.connection import Connection
from django_lets_go.common_functions import get_news
from frontend.forms import LoginForm
from cdr.import_cdr_freeswitch_mongodb import chk_ipaddress
from mongodb_connection import mongodb

news_url = settings.NEWS_URL


def index(request):
    """Index Page of CDR-Stats

    **Attributes**:

        * ``template`` - frontend/index.html
        * ``form`` - loginForm
    """
    errorlogin = ''
    loginform = LoginForm()

    if request.GET.get('db_error'):
        if request.GET['db_error'] == 'closed':
            errorlogin = _('mongodb database connection is closed!')
        if request.GET['db_error'] == 'locked':
            errorlogin = _('mongodb database is locked!')

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
    success_ip = []
    error_ip = []
    CDR_COUNT = 0
    backend_cdr_data = []
    #loop within the Mongo CDR Import List
    for ipaddress in settings.CDR_BACKEND:

        #Connect to Database
        db_name = settings.CDR_BACKEND[ipaddress]['db_name']
        table_name = settings.CDR_BACKEND[ipaddress]['table_name']
        db_engine = settings.CDR_BACKEND[ipaddress]['db_engine']
        #cdr_type = settings.CDR_BACKEND[ipaddress]['cdr_type']
        host = settings.CDR_BACKEND[ipaddress]['host']
        port = settings.CDR_BACKEND[ipaddress]['port']
        user = settings.CDR_BACKEND[ipaddress]['user']
        password = settings.CDR_BACKEND[ipaddress]['password']

        data = chk_ipaddress(ipaddress)
        ipaddress = data['ipaddress']
        collection_data = {}

        #Connect on MongoDB Database
        try:
            if db_engine == 'mysql':
                import MySQLdb as Database
                connection = Database.connect(user=user, passwd=password, db=db_name, host=host, port=port, connect_timeout=4)
                connection.autocommit(True)
                cursor = connection.cursor()
            elif db_engine == 'pgsql':
                import psycopg2 as Database
                connection = Database.connect(user=user, password=password, database=db_name, host=host, port=port)
                connection.autocommit(True)
                cursor = connection.cursor()
            elif db_engine == 'mongodb':
                connection = Connection(host, port)
                DBCON = connection[db_name]
                DBCON.authenticate(user, password)
                CDR = DBCON[table_name]
                CDR_COUNT = CDR.find().count()

            if db_engine == 'mysql' or db_engine == 'pgsql':
                cursor.execute("SELECT count(*) FROM %s" % (table_name))
                row = cursor.fetchone()
                CDR_COUNT = row[0]

            success_ip.append(ipaddress)
            if not mongodb.cdr_common:
                raise Http404

            collection_data = {
                'CDR_COMMON': mongodb.cdr_common.find().count(),
                'DAILY_ANALYTIC': mongodb.daily_analytic.find().count(),
                'MONTHLY_ANALYTIC': mongodb.monthly_analytic.find().count(),
                'CONC_CALL': mongodb.conc_call.find().count(),
                'CONC_CALL_AGG': mongodb.conc_call_agg.find().count()
            }
        except:
            CDR_COUNT = _('Error')
            error_ip.append(ipaddress)

        backend_cdr_data.append({
            'ip': ipaddress,
            'cdr_count': CDR_COUNT,
        })

    if success_ip:
        info_msg = _("CDR backend %s connected successfully." % (str(success_ip)))

    if error_ip:
        error_msg = _("please review the 'CDR_BACKEND' Settings in your file /usr/share/cdr-stats/settings_local.py make sure the settings, username, password are correct. Check also that the backend authorize a connection from your server")
        info_msg = _("after changes in your 'CDR_BACKEND' settings, you will need to restart celery: $ /etc/init.d/cdr-stats-celeryd restart")

    data = {
        'backend_cdr_data': backend_cdr_data,
        'collection_data': collection_data,
        'settings': settings,
        'info_msg': info_msg,
        'error_msg': error_msg,
        'success_ip': success_ip,
        'error_ip': error_ip,
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
