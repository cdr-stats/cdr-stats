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
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from mongodb_connection import mongodb
from user_profile.models import UserProfile


def check_cdr_exists(function=None):
    """
    Decorator check if cdr exists if not go to error page
    """
    def _dec(run_func):
        """Decorator"""
        def _caller(request, *args, **kwargs):
            """Caller."""
            if not mongodb.cdr_common:
                raise Http404
            doc = mongodb.cdr_common.find_one()
            if not doc:
                return render_to_response('cdr/error_import.html', context_instance=RequestContext(request))
            else:
                return run_func(request, *args, **kwargs)
        return _caller
    return _dec(function) if function is not None else _dec


def check_user_accountcode(function=None):
    """
    Decorator check if account code exists for user
    if not go to error page
    """
    def _dec(run_func):
        """Decorator"""
        def _caller(request, *args, **kwargs):
            """Caller."""
            if not request.user.is_superuser:
                if not UserProfile.objects.get(user=request.user).accountcode:
                    return HttpResponseRedirect('/?acc_code_error=true')
                else:
                    return run_func(request, *args, **kwargs)
            else:
                return run_func(request, *args, **kwargs)
        return _caller
    return _dec(function) if function is not None else _dec


def check_user_voipplan(function=None):
    """
    Decorator check if voip plan exists for user
    if not go to error page
    """
    def _dec(run_func):
        """Decorator"""
        def _caller(request, *args, **kwargs):
            """Caller."""
            if not request.user.is_superuser:
                if not UserProfile.objects.get(user=request.user).voipplan_id:
                    return HttpResponseRedirect('/?voipplan_error=true')
                else:
                    return run_func(request, *args, **kwargs)
            else:
                return run_func(request, *args, **kwargs)
        return _caller
    return _dec(function) if function is not None else _dec
