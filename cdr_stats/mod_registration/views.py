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

from django.contrib.auth.views import password_reset, password_reset_done,\
    password_reset_confirm, password_reset_complete
from django.http import HttpResponseRedirect
from frontend.forms import LoginForm
from mod_registration.forms import ForgotForm, CustomSetPasswordForm
from django.conf import settings


def cust_password_reset(request):
    """Use ``django.contrib.auth.views.password_reset`` view method for
    forgotten password on the Customer UI

    This method sends an e-mail to the user's email-id which is entered in
    ``password_reset_form``
    """
    if not request.user.is_authenticated():
        data = {
            'loginform': LoginForm(),
            'forgotform': ForgotForm(request.POST or None),
        }
        return password_reset(
            request,
            template_name='mod_registration/password_reset_form.html',
            email_template_name='mod_registration/password_reset_email.html',
            post_reset_redirect='/password_reset/done/',
            from_email=settings.EMAIL_ADMIN,
            extra_context=data)
    else:
        return HttpResponseRedirect("/")


def cust_password_reset_done(request):
    """Use ``django.contrib.auth.views.password_reset_done`` view method for
    forgotten password on the Customer UI

    This will show a message to the user who is seeking to reset their
    password.
    """
    if not request.user.is_authenticated():
        data = {
            'loginform': LoginForm(),
            'forgotform': ForgotForm(),
        }
        return password_reset_done(request, template_name='mod_registration/password_reset_done.html', extra_context=data)
    else:
        return HttpResponseRedirect("/")


def cust_password_reset_confirm(request, uidb64=None, token=None):
    """Use ``django.contrib.auth.views.password_reset_confirm`` view method for
    forgotten password on the Customer UI

    This will allow a user to reset their password.
    """
    if not request.user.is_authenticated():
        data = {
            'loginform': LoginForm(),
            'custom_set_password_form': CustomSetPasswordForm(request.POST or None)
        }
        return password_reset_confirm(
            request, uidb64=uidb64, token=token,
            template_name='mod_registration/password_reset_confirm.html',
            post_reset_redirect='/reset/done/',
            extra_context=data)
    else:
        return HttpResponseRedirect("/")


def cust_password_reset_complete(request):
    """Use ``django.contrib.auth.views.password_reset_complete`` view method
    for forgotten password on theCustomer UI

    This shows an acknowledgement to the user after successfully resetting
    their password for the system.
    """
    if not request.user.is_authenticated():
        data = {'loginform': LoginForm()}
        return password_reset_complete(
            request, template_name='mod_registration/password_reset_complete.html',
            extra_context=data)
    else:
        return HttpResponseRedirect("/")
