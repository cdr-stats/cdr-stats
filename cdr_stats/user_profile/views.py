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

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
# from django.http import HttpResponseRedirect
from django.template.context import RequestContext
from django.utils.translation import ugettext_lazy as _
from user_profile.models import UserProfile
from user_profile.forms import UserChangeDetailForm, UserChangeDetailExtendForm, UserPasswordChangeForm
from cdr.decorators import check_user_detail


@login_required
@check_user_detail('accountcode')
def customer_detail_change(request):
    """User Detail change on Customer UI

    **Attributes**:

        * ``form`` - UserChangeDetailForm, UserChangeDetailExtendForm, UserPasswordChangeForm
        * ``template`` - 'user_profile/user_detail_change.html'

    **Logic Description**:

        * User is able to change their details.
    """
    user_detail = get_object_or_404(User, username=request.user)

    try:
        user_detail_extened = UserProfile.objects.get(user=user_detail)
    except UserProfile.DoesNotExist:
        # create UserProfile
        user_detail_extened = UserProfile(user=user_detail)
        # DEMO / Disable
        if not settings.DEMO_MODE:
            user_detail_extened.save()

    user_detail_form = UserChangeDetailForm(request.user, instance=user_detail)
    user_detail_extened_form = UserChangeDetailExtendForm(request.user, instance=user_detail_extened)

    user_password_form = UserPasswordChangeForm(user=request.user)

    msg_detail = ''
    msg_pass = ''
    error_detail = ''
    error_pass = ''
    action = ''

    if 'action' in request.GET:
        action = request.GET['action']

    if request.method == 'POST':
        if request.POST['form-type'] == "change-detail":
            user_detail_form = UserChangeDetailForm(request.user, request.POST, instance=user_detail)
            user_detail_extened_form = UserChangeDetailExtendForm(request.user, request.POST, instance=user_detail_extened)
            action = 'tabs-1'
            if user_detail_form.is_valid() and user_detail_extened_form.is_valid():
                user_detail_form.save()
                user_detail_extened_form.save()
                msg_detail = _('detail has been changed.')
            else:
                error_detail = _('please correct the errors below.')
        else:
            # change-password
            user_password_form = UserPasswordChangeForm(user=request.user, data=request.POST)
            action = 'tabs-2'
            if user_password_form.is_valid():
                user_password_form.save()
                msg_pass = _('your password has been changed.')
            else:
                error_pass = _('please correct the errors below.')
    data = {
        'user_detail_form': user_detail_form,
        'user_detail_extened_form': user_detail_extened_form,
        'user_password_form': user_password_form,
        'msg_detail': msg_detail,
        'msg_pass': msg_pass,
        'error_detail': error_detail,
        'error_pass': error_pass,
        'action': action,
    }
    return render_to_response('user_profile/user_detail_change.html', data, context_instance=RequestContext(request))
