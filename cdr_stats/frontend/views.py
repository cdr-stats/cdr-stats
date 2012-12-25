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

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import password_reset, password_reset_done,\
    password_reset_confirm, password_reset_complete
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.conf import settings
from django.template.context import RequestContext
from django.utils.translation import ugettext as _
from pymongo.connection import Connection
from pymongo.errors import ConnectionFailure
from common.common_functions import current_view, get_news
from frontend.forms import LoginForm
from cdr.import_cdr_freeswitch_mongodb import chk_ipaddress


news_url = settings.NEWS_URL


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
                connection = Database.connect(user=user, passwd=password,
                    db=db_name, host=host, port=port, connect_timeout=4)
                connection.autocommit(True)
                cursor = connection.cursor()
            elif db_engine == 'pgsql':
                import psycopg2 as Database
                connection = Database.connect(user=user, passwd=password,
                    db=db_name, host=host, port=port)
                connection.autocommit(True)
                cursor = connection.cursor()
            elif db_engine == 'mongodb':
                connection = Connection(host, port)
                DBCON = connection[db_name]
                CDR = DBCON[table_name]
                CDR_COUNT = CDR.find().count()

            if db_engine == 'mysql' or db_engine == 'pgsql':
                cursor.execute("SELECT count(*) FROM %s" % (table_name))
                row = cursor.fetchone()
                #TODO: This should be an array, we might have more than 1 mysql / pgsql backend
                #image situation where we have 5 Mysql backend, we need to count cdr for each of them
                CDR_COUNT = row[0]

            success_ip.append(ipaddress)

            CDR_COMMON = settings.DBCON[settings.MONGO_CDRSTATS['CDR_COMMON']]
            DAILY_ANALYTIC = settings.DBCON[settings.MONGO_CDRSTATS['DAILY_ANALYTIC']]
            MONTHLY_ANALYTIC = settings.DBCON[settings.MONGO_CDRSTATS['MONTHLY_ANALYTIC']]
            CONC_CALL = settings.DBCON[settings.MONGO_CDRSTATS['CONC_CALL']]
            CONC_CALL_AGG = settings.DBCON[settings.MONGO_CDRSTATS['CONC_CALL_AGG']]

            collection_data = {
                'CDR_COMMON': CDR_COMMON.find().count(),
                'DAILY_ANALYTIC': DAILY_ANALYTIC.find().count(),
                'MONTHLY_ANALYTIC': MONTHLY_ANALYTIC.find().count(),
                'CONC_CALL': CONC_CALL.find().count(),
                'CONC_CALL_AGG': CONC_CALL_AGG.find().count()
            }
        except:
            error_ip.append(ipaddress)

        backend_cdr_data.append({
            'ip': ipaddress,
            'cdr_count': CDR_COUNT,
        })

    if success_ip:
        info_msg = _("CDR Backend %s connected successfully." % (str(success_ip)))

    if error_ip:
        error_msg = _("Please review the 'CDR_BACKEND' Settings in your file /usr/share/cdr-stats/settings_local.py make sure the settings, username, password are correct. Check also that the backend authorize a connection from your server")
        info_msg = _("After changes in your 'CDR_BACKEND' settings, you will need to restart celery: $ /etc/init.d/newfies-celeryd restart")

    data = {
        'backend_cdr_data': backend_cdr_data,
        'collection_data': collection_data,
        'settings': settings,
        'info_msg': info_msg,
        'error_msg': error_msg,
        'success_ip': success_ip,
        'error_ip': error_ip,
    }
    template = 'frontend/diagnostic.html'
    return render_to_response(template, data,
           context_instance=RequestContext(request))


def logout_view(request):
    """Log out from application"""
    try:
        del request.session['has_notified']
    except KeyError:
        pass

    logout(request)
    # set language cookie
    response = HttpResponseRedirect('/')
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME,
                        request.LANGUAGE_CODE)
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
    template = 'frontend/index.html'
    errorlogin = ''

    if request.method == 'POST':
        loginform = LoginForm(request.POST)
        if loginform.is_valid():
            cd = loginform.cleaned_data
            user = authenticate(username=cd['user'],
                                password=cd['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    request.session['has_notified'] = False
                    # Redirect to a success page (dashboard).
                    return HttpResponseRedirect('/dashboard/')
                else:
                    # Return a 'disabled account' error message
                    errorlogin = _('Disabled Account')
            else:
                # Return an 'invalid login' error message.
                errorlogin = _('Invalid Login.')
        else:
            # Return an 'Valid User Credentials' error message.
            errorlogin = _('Enter Valid User Credentials.')
    else:
        loginform = LoginForm()

    data = {
        'module': current_view(request),
        'loginform': loginform,
        'errorlogin': errorlogin,
        'news': get_news(news_url),
        'is_authenticated': request.user.is_authenticated(),
    }

    return render_to_response(template, data,
           context_instance=RequestContext(request))


def pleaselog(request):
    template = 'frontend/index.html'

    data = {
        'loginform': LoginForm(),
        'notlogged': True,
    }
    return render_to_response(template, data,
           context_instance=RequestContext(request))


def cust_password_reset(request):
    """Use ``django.contrib.auth.views.password_reset`` view method for
    forgotten password on the Customer UI

    This method sends an e-mail to the user's email-id which is entered in
    ``password_reset_form``
    """
    if not request.user.is_authenticated():
        data = {'loginform': LoginForm()}
        return password_reset(
            request,
            template_name='frontend/registration/password_reset_form.html',
            email_template_name='frontend/registration/password_reset_email.html',
            post_reset_redirect='/password_reset/done/',
            from_email='cdr_stats_admin@localhost.com',
            extra_context=data
        )
    else:
        return HttpResponseRedirect("/")


def cust_password_reset_done(request):
    """Use ``django.contrib.auth.views.password_reset_done`` view method for
    forgotten password on the Customer UI

    This will show a message to the user who is seeking to reset their
    password.
    """
    if not request.user.is_authenticated():
        data = {'loginform': LoginForm()}
        return password_reset_done(
            request,
            template_name='frontend/registration/password_reset_done.html',
            extra_context=data
        )
    else:
        return HttpResponseRedirect("/")


def cust_password_reset_confirm(request, uidb36=None, token=None):
    """Use ``django.contrib.auth.views.password_reset_confirm`` view method for
    forgotten password on the Customer UI

    This will allow a user to reset their password.
    """
    if not request.user.is_authenticated():
        data = {'loginform': LoginForm()}
        return password_reset_confirm(
            request,
            uidb36=uidb36,
            token=token,
            template_name='frontend/registration/password_reset_confirm.html',
            post_reset_redirect='/reset/done/',
            extra_context=data)
    else:
        return HttpResponseRedirect("/")


def cust_password_reset_complete(request):
    """Use ``django.contrib.auth.views.password_reset_complete`` view method
    for forgotten password on the Customer UI

    This shows an acknowledgement to the user after successfully resetting
    their password for the system.
    """
    if not request.user.is_authenticated():
        data = {'loginform': LoginForm()}
        return password_reset_complete(
            request,
            template_name='frontend/registration/password_reset_complete.html',
            extra_context=data)
    else:
        return HttpResponseRedirect("/")
