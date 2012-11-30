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
from django.utils.encoding import smart_str, smart_unicode
from django.conf import settings
from django.db.models import Count
from cdr_alert.models import Alarm, Blacklist, Whitelist, AlarmReport
from cdr_alert.constants import ALARM_COLUMN_NAME, ALARM_REPORT_COLUMN_NAME
from cdr_alert.forms import AlarmForm, BWCountryForm, BWPrefixForm,\
    AlarmReportForm
from frontend_notification.views import notice_count
from common.common_functions import current_view, get_pagination_vars,\
    variable_value, ceil_strdate, validate_days
from country_dialcode.models import Country, Prefix
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import time


@permission_required('cdr_alert.view_alarm', login_url='/')
@login_required
def alarm_list(request):
    """Alarm list for the logged in user

    **Attributes**:

        * ``template`` - frontend/cdr_alert/alert_list.html

    **Logic Description**:

        * List all alarms which belong to the logged in user.
    """
    sort_col_field_list = ['id', 'name', 'period', 'type', 'alert_condition',
                           'alert_value', 'status', 'updated_date']
    default_sort_field = 'id'
    pagination_data =\
        get_pagination_vars(request, sort_col_field_list, default_sort_field)

    PAGE_SIZE = pagination_data['PAGE_SIZE']
    sort_order = pagination_data['sort_order']

    alarm_list = Alarm.objects\
        .filter(user=request.user).order_by(sort_order)

    template_name = 'frontend/cdr_alert/alarm/list.html'

    PAGE_SIZE = settings.PAGE_SIZE
    template_data = {
        'module': current_view(request),
        'msg': request.session.get('msg'),
        'rows': alarm_list,
        'total_count': alarm_list.count(),
        'PAGE_SIZE': PAGE_SIZE,
        'ALARM_COLUMN_NAME': ALARM_COLUMN_NAME,
        'col_name_with_order': pagination_data['col_name_with_order'],
        'notice_count': notice_count(request),
    }
    request.session['msg'] = ''
    request.session['error_msg'] = ''
    return render_to_response(template_name, template_data,
        context_instance=RequestContext(request))


@permission_required('cdr_alert.add_alarm', login_url='/')
@login_required
def alarm_add(request):
    """Add new Alarm for the logged in user

    **Attributes**:

        * ``form`` - AlarmForm
        * ``template`` - frontend/cdr_alert/alarm/change.html

    **Logic Description**:

        * Add a new Alarm which will belong to the logged in user
          via the AlarmForm & get redirected to the Alarm list
    """
    form = AlarmForm()
    if request.method == 'POST':
        form = AlarmForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = User.objects.get(username=request.user)
            obj.save()
            request.session["msg"] = _('"%(name)s" added.') %\
                                     {'name': request.POST['name']}
            return HttpResponseRedirect('/alert/')
    template = 'frontend/cdr_alert/alarm/change.html'
    data = {
        'module': current_view(request),
        'form': form,
        'action': 'add',
        'notice_count': notice_count(request),
    }
    return render_to_response(template, data,
        context_instance=RequestContext(request))



@permission_required('cdr_alert.delete_alarm', login_url='/')
@login_required
def alarm_del(request, object_id):
    """Delete a alarm for a logged in user

    **Attributes**:

        * ``object_id`` - Selected alarm object
        * ``object_list`` - Selected alarm objects

    **Logic Description**:

        * Delete selected the alarm from the alarm list
    """
    if int(object_id) != 0:
        # When object_id is not 0
        alarm = get_object_or_404(
            Alarm, pk=object_id, user=request.user)

        # 1) delete alarm
        request.session["msg"] = _('"%(name)s" is deleted.')\
                                 % {'name': alarm.name}
        alarm.delete()
    else:
        # When object_id is 0 (Multiple records delete)
        values = request.POST.getlist('select')
        values = ", ".join(["%s" % el for el in values])
        try:
            # 1) delete alarm
            alarm_list = Alarm.objects.filter(user=request.user)\
                .extra(where=['id IN (%s)' % values])
            if alarm_list:
                request.session["msg"] =\
                    _('%(count)s alarm(s) are deleted.')\
                        % {'count': alarm_list.count()}
                alarm_list.delete()
        except:
            raise Http404

    return HttpResponseRedirect('/alert/')


@permission_required('cdr_alert.change_alarm', login_url='/')
@login_required
def alarm_change(request, object_id):
    """Update/Delete Alarm for the logged in user

    **Attributes**:

        * ``object_id`` - Selected alarm object
        * ``form`` - AlarmForm
        * ``template`` - frontend/cdr_alert/alarm/change.html

    **Logic Description**:

        * Update/delete selected alarm from the alarm list
          via alarmForm & get redirected to alarm list
    """
    alarm = get_object_or_404(Alarm, pk=object_id, user=request.user)
    form = AlarmForm(instance=alarm)
    if request.method == 'POST':
        if request.POST.get('delete'):
            alarm_del(request, object_id)
            return HttpResponseRedirect('/alert/')
        else:
            form = AlarmForm(request.POST, instance=alarm)
            if form.is_valid():
                form.save()
                request.session["msg"] = _('"%(name)s" is updated.')\
                                         % {'name': request.POST['name']}
                return HttpResponseRedirect('/alert/')

    template = 'frontend/cdr_alert/alarm/change.html'
    data = {
        'module': current_view(request),
        'form': form,
        'action': 'update',
        'notice_count': notice_count(request),
    }
    return render_to_response(template, data,
        context_instance=RequestContext(request))


def last_seven_days_report(request, kwargs):
    comp_days = 7
    from_date = datetime.today()
    from_day = validate_days(from_date.year,
        from_date.month,
        from_date.day)
    from_year = from_date.year
    from_month = from_date.month
    end_date = datetime(from_year, from_month, from_day)
    start_date = end_date + relativedelta(days=-comp_days)
    start_date = datetime(start_date.year, start_date.month,
                          start_date.day, 0, 0, 0, 0)
    end_date = datetime(end_date.year, end_date.month,
                        end_date.day, 23, 59, 59, 999999)


    if start_date and end_date:
        kwargs['daterun__range'] = (start_date, end_date)

    select_data = {"daterun": "SUBSTR(CAST(daterun as CHAR(30)),1,10)"}


    alarm_data = AlarmReport.objects.extra(select=select_data)\
        .values('daterun')\
        .filter(**kwargs)\
        .annotate(Count('daterun'))\
        .order_by('-daterun')

    total_data = []
    total_alert = 0
    for doc in alarm_data:
        daterun = str(doc['daterun'])

        total_data.append(
            {
                'daterun': datetime(int(daterun[0:4]), int(daterun[5:7]), int(daterun[8:10])),
                'alert__count': int(int(doc['daterun__count'])),
            })
        total_alert += int(doc['daterun__count'])

    if alarm_data != 0:
        max_alert_count = max([int(x['alert__count']) for x in total_data])
    else:
        max_alert_count = 0

    data = {
        'start_date': start_date,
        'end_date': end_date,
        'total_data': total_data,
        'total_alert': total_alert,
        'max_alert_count': max_alert_count
    }
    return data


@permission_required('cdr_alert.view_alarm_report', login_url='/')
@login_required
def alert_report(request):
    """
    To get alarm report for logged in user

    **Attributes**:

        * ``form`` - AlarmReportForm
        * ``template`` - frontend/cdr_alert/alarm_report.html
    """
    form = AlarmReportForm(request.user, initial={'alarm': 0})
    sort_col_field_list = ['id', 'alarm', 'calculatedvalue', 'status','daterun']
    default_sort_field = 'id'
    pagination_data =\
        get_pagination_vars(request, sort_col_field_list, default_sort_field)

    PAGE_SIZE = pagination_data['PAGE_SIZE']
    sort_order = pagination_data['sort_order']
    search_tag = 1
    alert_id = ''
    action = 'tabs-1'

    if request.method == 'POST':
        form = AlarmReportForm(request.user, request.POST)
        if form.is_valid():
            request.session['session_alarm'] = ''

            if request.POST.get('alarm'):
                alert_id = request.POST.get('alarm')
                request.session['session_alarm'] = alert_id

    post_var_with_page = 0
    try:
        if request.GET.get('page') or request.GET.get('sort_by'):
            post_var_with_page = 1
            alert_id = request.session.get('session_alarm')
            form = AlarmReportForm(request.user, initial={'alarm': alert_id})
        else:
            post_var_with_page = 1
            if request.method == 'GET':
                post_var_with_page = 0
    except:
        pass

    if post_var_with_page == 0:
        # default
        # unset session var
        request.session['session_alarm'] = ''

    kwargs = {}
    if alert_id and alert_id != 0:
        kwargs['alarm_id'] = alert_id
    kwargs['alarm__user'] = request.user

    alarm_report_list = AlarmReport.objects.filter(**kwargs).order_by(sort_order)
    days_report = last_seven_days_report(request, kwargs)

    total_data = days_report['total_data']
    total_alert = days_report['total_alert']
    max_alert_count = days_report['max_alert_count']
    start_date = days_report['start_date']
    end_date = days_report['end_date']

    template = 'frontend/cdr_alert/alarm_report.html'
    data = {
        'module': current_view(request),
        'form': form,
        'action': action,
        'total_data': total_data,
        'max_alert_count': max_alert_count,
        'start_date': start_date,
        'end_date': end_date,
        'rows': alarm_report_list,
        'total_count': alarm_report_list.count(),
        'PAGE_SIZE': PAGE_SIZE,
        'ALARM_REPORT_COLUMN_NAME': ALARM_REPORT_COLUMN_NAME,
        'col_name_with_order': pagination_data['col_name_with_order'],
        'notice_count': notice_count(request),
    }
    return render_to_response(template, data,
        context_instance=RequestContext(request))


@permission_required('cdr_alert.view_whitelist', login_url='/')
@login_required
def trust_control(request):
    #Blacklist, Whitelist
    prefix_list = Prefix.objects.all().order_by('prefix')
    #for i in prefix_list:
    #    if i.country_id is not None:
    #        print str(i.prefix) + ' - ' +  smart_str(i.country_id.countryname)
    #prefix_list = (','.join('"' + item + '"' for item in prefix_list))
    #prefix_list = "[" + str(prefix_list) + "]"

    prefix_list = \
        map(str, Prefix.objects.values_list("prefix", flat=True).all().order_by('prefix'))
    prefix_list = (','.join('"' + item + '"' for item in prefix_list))
    prefix_list = "[" + str(prefix_list) + "]"


    blacklist = Blacklist.objects.filter(user=request.user).order_by('id')
    whitelist = Whitelist.objects.filter(user=request.user).order_by('id')

    # blacklist form
    bl_country_form = BWCountryForm()
    bl_prefix_form = BWPrefixForm()

    # whitelist form
    wl_country_form = BWCountryForm()
    wl_prefix_form = BWPrefixForm()

    template = 'frontend/cdr_alert/common_black_white_list.html'
    data = {
        'module': current_view(request),
        'prefix_list': prefix_list,
        'bl_country_form': bl_country_form,
        'bl_prefix_form': bl_prefix_form,
        'wl_country_form': wl_country_form,
        'wl_prefix_form': wl_prefix_form,
        'blacklist': blacklist,
        'whitelist': whitelist,
        'notice_count': notice_count(request),
    }
    return render_to_response(template, data,
        context_instance=RequestContext(request))
