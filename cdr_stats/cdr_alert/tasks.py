# -*- coding: utf-8 -*-

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
from __future__ import division
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.mail import send_mail, mail_admins
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from celery.task import PeriodicTask, task
from notification import models as notification
from django_lets_go.only_one_task import only_one
from cdr_alert.constants import PERIOD, ALARM_TYPE, ALERT_CONDITION, ALERT_CONDITION_ADD_ON,\
    ALARM_REPROT_STATUS
from aggregator.pandas_cdr import get_report_cdr_per_switch
from aggregator.aggregate_cdr import custom_sql_aggr_top_hangup
from cdr_alert.models import Alarm, AlarmReport
from cdr.functions_def import get_hangupcause_id
from cdr.views import get_cdr_mail_report
from user_profile.models import UserProfile
from user_profile.constants import NOTICE_TYPE
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import math

# Lock expires in 30 minutes
LOCK_EXPIRE = 60 * 30


def get_start_end_date(alert_condition_add_on):
    """Get start and end date according to alert_condition

    return a list with
        * p_start_date
        * p_end_date
        * c_start_date
        * c_end_date
    """
    date_dict = {}
    # yesterday's date
    end_date = datetime.today() + relativedelta(days=-1)
    if alert_condition_add_on == ALERT_CONDITION_ADD_ON.SAME_DAY:  # Same day
        compare_days = 1
    if alert_condition_add_on == ALERT_CONDITION_ADD_ON.SAME_DAY_IN_PRE_WEEK:  # Same day in the previous week
        compare_days = 7

    start_date = end_date + relativedelta(days=-int(compare_days))
    # get Previous dates and Current dates
    date_dict['p_start_date'] = datetime(start_date.year, start_date.month,
                                       start_date.day, 0, 0, 0, 0)
    date_dict['p_end_date'] = datetime(start_date.year, start_date.month,
                                     start_date.day, 23, 59, 59, 999999)
    date_dict['c_start_date'] = datetime(end_date.year, end_date.month,
                                       end_date.day, 0, 0, 0, 0)
    date_dict['c_end_date'] = datetime(end_date.year, end_date.month,
                                     end_date.day, 23, 59, 59, 999999)

    return date_dict


def notify_admin_with_mail(notice_id, email_id):
    """Send notification to all admin as well as mail to recipient of alarm

    >>> notify_admin_with_mail(1, 'xyz@localhost.com')
    True
    """
    # Get all the admin users - admin superuser
    for user in User.objects.filter(is_superuser=True):
        recipient = user

        # send notification
        if notification:
            note_label = notification.NoticeType.objects.get(default=notice_id).label
            notification.send([recipient], note_label,
                              {'from_user': user}, sender=user)
        # Send mail to ADMINS
        subject = _('Alert')
        message = _('Alert Message "%(user)s" - "%(user_id)s"') % {'user': user, 'user_id': user.id}

        try:
            send_mail(subject, message, settings.SERVER_EMAIL, email_id)
        except:
            # send an email to the site admins as defined in the ADMINS setting
            mail_admins(subject, message)  # html_message='text/html'

    return True


def create_alarm_report_object(alarm_obj, status):
    # create alarm report
    # status - 1 - No alarm sent
    # status - 2 - Alarm sent
    try:
        AlarmReport.objects.create(alarm=alarm_obj,
                                   calculatedvalue=alarm_obj.alert_value,
                                   status=status)
        return True
    except:
        return False


def chk_alert_value(alarm_obj, current_value, previous_value=None):
    """ compare values with following conditions against alarm alert value

        *   Is less than | Is greater than
        *   Decrease by more than | Increase by more than
        *   % decrease by more than | % Increase by more than
    """
    if alarm_obj.alert_condition == ALERT_CONDITION.IS_LESS_THAN:  # Is less than
        if alarm_obj.alert_value < current_value:
            notify_admin_with_mail(alarm_obj.type, alarm_obj.email_to_send_alarm)
            create_alarm_report_object(alarm_obj, status=ALARM_REPROT_STATUS.ALARM_SENT)
        else:
            create_alarm_report_object(alarm_obj, status=ALARM_REPROT_STATUS.NO_ALARM_SENT)

    if alarm_obj.alert_condition == ALERT_CONDITION.IS_GREATER_THAN:  # Is greater than
        if alarm_obj.alert_value > current_value:
            notify_admin_with_mail(alarm_obj.type, alarm_obj.email_to_send_alarm)
            create_alarm_report_object(alarm_obj, status=ALARM_REPROT_STATUS.ALARM_SENT)
        else:
            create_alarm_report_object(alarm_obj, status=ALARM_REPROT_STATUS.NO_ALARM_SENT)

    if alarm_obj.alert_condition == ALERT_CONDITION.DECREASE_BY_MORE_THAN:  # Decrease by more than
        diff = abs(current_value - previous_value)
        if diff < alarm_obj.alert_value:
            notify_admin_with_mail(alarm_obj.type, alarm_obj.email_to_send_alarm)
            create_alarm_report_object(alarm_obj, status=ALARM_REPROT_STATUS.ALARM_SENT)
        else:
            create_alarm_report_object(alarm_obj, status=ALARM_REPROT_STATUS.NO_ALARM_SENT)

    if alarm_obj.alert_condition == ALERT_CONDITION.INCREASE_BY_MORE_THAN:  # Increase by more than
        diff = abs(current_value - previous_value)
        if diff > alarm_obj.alert_value:
            notify_admin_with_mail(alarm_obj.type, alarm_obj.email_to_send_alarm)
            create_alarm_report_object(alarm_obj, status=ALARM_REPROT_STATUS.ALARM_SENT)
        else:
            create_alarm_report_object(alarm_obj, status=ALARM_REPROT_STATUS.NO_ALARM_SENT)

    # http://www.mathsisfun.com/percentage-difference.html
    if alarm_obj.alert_condition == ALERT_CONDITION.PERCENTAGE_DECREASE_BY_MORE_THAN:  # % decrease by more than
        diff = abs(current_value - previous_value)
        avg = (current_value + previous_value) / 2
        avg = avg if avg != 0 else 1
        percentage = diff / avg * 100
        if percentage < alarm_obj.alert_value:
            notify_admin_with_mail(alarm_obj.type, alarm_obj.email_to_send_alarm)
            create_alarm_report_object(alarm_obj, status=ALARM_REPROT_STATUS.ALARM_SENT)
        else:
            create_alarm_report_object(alarm_obj, status=ALARM_REPROT_STATUS.NO_ALARM_SENT)

    if alarm_obj.alert_condition == ALERT_CONDITION.PERCENTAGE_INCREASE_BY_MORE_THAN:  # % Increase by more than
        diff = abs(current_value - previous_value)
        avg = (current_value + previous_value) / 2
        avg = avg if avg != 0 else 1
        percentage = diff / avg * 100
        if percentage > alarm_obj.alert_value:
            notify_admin_with_mail(alarm_obj.type, alarm_obj.email_to_send_alarm)
            create_alarm_report_object(alarm_obj, status=ALARM_REPROT_STATUS.ALARM_SENT)
        else:
            create_alarm_report_object(alarm_obj, status=ALARM_REPROT_STATUS.NO_ALARM_SENT)

    return True


def run_alarm(alarm_obj, logger):
    """
    Perform Alarm Check
    """
    running_alarm_test_data = {
        'running_alarm_status': True,
        'current_value': None,
        'previous_value': None,
    }
    user = False
    switch_id = 0

    if alarm_obj.type == ALARM_TYPE.ALOC:
        # ALOC (average length of call)
        logger.debug('ALOC (Average Length Of Call)')

        # return start and end date of previous/current day
        date_dict = get_start_end_date(alarm_obj.alert_condition_add_on)

        # Previous date data
        start_date = date_dict['p_start_date']
        end_date = date_dict['p_end_date']

        daily_data = get_report_cdr_per_switch(user, 'day', start_date, end_date, switch_id)

        total_calls = daily_data["nbcalls"]["total"]
        total_duration = daily_data["duration"]["total"]
        ACD = math.floor(total_duration / total_calls)

        if alarm_obj.alert_condition == ALERT_CONDITION.IS_LESS_THAN or \
                alarm_obj.alert_condition == ALERT_CONDITION.IS_GREATER_THAN:
            running_alarm_test_data['previous_value'] = ACD
            chk_alert_value(alarm_obj, ACD)
        else:
            previous_date_duration = ACD

        # Current date data
        start_date = date_dict['c_start_date']
        end_date = date_dict['c_end_date']

        daily_data = get_report_cdr_per_switch(user, 'day', start_date, end_date, switch_id)

        total_calls = daily_data["nbcalls"]["total"]
        total_duration = daily_data["duration"]["total"]
        ACD = math.floor(total_duration / total_calls)

        if alarm_obj.alert_condition == ALERT_CONDITION.IS_LESS_THAN or \
                alarm_obj.alert_condition == ALERT_CONDITION.IS_GREATER_THAN:
            running_alarm_test_data['current_value'] = ACD
            chk_alert_value(alarm_obj, ACD)
        else:
            current_date_duration = ACD
            running_alarm_test_data['current_value'] = ACD
            running_alarm_test_data['previous_value'] = previous_date_duration
            chk_alert_value(alarm_obj, current_date_duration, previous_date_duration)

    elif alarm_obj.type == ALARM_TYPE.ASR:
        # ASR (Answer Seize Ratio)
        logger.debug('ASR (Answer Seize Ratio)')
        # return start and end date of previous/current day
        date_dict = get_start_end_date(alarm_obj.alert_condition_add_on)

        # hangup_cause_q850 - 16 - NORMAL_CLEARING
        hangup_cause_q850 = 16

        # Previous date data
        start_date = date_dict['p_start_date']
        end_date = date_dict['p_end_date']

        limit = 10
        hangup_cause_id = False
        # TODO: Regroup the 2 calls to custom_sql_aggr_top_hangup to get the hangup
        (hangup_cause_data, total_calls, total_duration, total_billsec, total_buy_cost, total_sell_cost) = \
            custom_sql_aggr_top_hangup(user, switch_id, hangup_cause_id, limit, start_date, end_date)

        pre_total_record = total_calls

        hangup_cause_id = get_hangupcause_id(hangup_cause_q850)
        (hangup_cause_data, total_calls, total_duration, total_billsec, total_buy_cost, total_sell_cost) = \
            custom_sql_aggr_top_hangup(user, switch_id, hangup_cause_id, limit, start_date, end_date)
        pre_total_answered_record = total_calls

        # pre_total_record should not be 0
        pre_total_record = 1 if pre_total_record == 0 else pre_total_record
        previous_asr = pre_total_answered_record / pre_total_record

        if alarm_obj.alert_condition == ALERT_CONDITION.IS_LESS_THAN or \
                alarm_obj.alert_condition == ALERT_CONDITION.IS_GREATER_THAN:
            running_alarm_test_data['previous_value'] = previous_asr
            chk_alert_value(alarm_obj, previous_asr)
        else:
            previous_asr = previous_asr

        # TODO: Regroup the 2 calls to custom_sql_aggr_top_hangup to get the hangup

        # Current date data
        start_date = date_dict['c_start_date']
        end_date = date_dict['c_end_date']

        limit = 10
        hangup_cause_id = False
        # TODO: Regroup the 2 calls to custom_sql_aggr_top_hangup to get the hangup
        (hangup_cause_data, total_calls, total_duration, total_billsec, total_buy_cost, total_sell_cost) = \
            custom_sql_aggr_top_hangup(user, switch_id, hangup_cause_id, limit, start_date, end_date)

        cur_total_record = total_calls

        hangup_cause_id = get_hangupcause_id(hangup_cause_q850)
        (hangup_cause_data, total_calls, total_duration, total_billsec, total_buy_cost, total_sell_cost) = \
            custom_sql_aggr_top_hangup(user, switch_id, hangup_cause_id, limit, start_date, end_date)
        cur_total_answered_record = total_calls

        # cur_total_record should not be 0
        cur_total_record = 1 if cur_total_record == 0 else cur_total_record
        current_asr = cur_total_answered_record / cur_total_record

        if alarm_obj.alert_condition == ALERT_CONDITION.IS_LESS_THAN or \
                alarm_obj.alert_condition == ALERT_CONDITION.IS_GREATER_THAN:
            running_alarm_test_data['current_value'] = current_asr
            chk_alert_value(alarm_obj, current_asr)
        else:
            running_alarm_test_data['current_value'] = current_asr
            running_alarm_test_data['previous_value'] = previous_asr
            chk_alert_value(alarm_obj, current_asr, previous_asr)

    return running_alarm_test_data


class chk_alarm(PeriodicTask):

    """A periodic task to determine unusual call patterns.

       Sends an email if an alert condition is matched.

    **Usage**:

        chk_alarm.delay()
    """

    run_every = timedelta(seconds=86400)  # every day

    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info('TASK :: chk_alarm called')

        alarm_objs = Alarm.objects.filter(status=1)  # all active alarms
        alarm_status = {}
        alarm_status['running_alarm_status'] = True
        for alarm_obj in alarm_objs:
            try:
                alarm_report = AlarmReport.objects.filter(alarm=alarm_obj).latest('daterun')
                diff_run = (datetime.now() - alarm_report.daterun).days
                diff_run = 1
                if alarm_obj.period == PERIOD.DAY:  # Day
                    if diff_run == 1:  # every day
                        # Run alert task
                        logger.debug('Run alarm')
                        alarm_status = run_alarm(alarm_obj, logger)

                if alarm_obj.period == PERIOD.WEEK:  # Week
                    if diff_run == 7:  # every week
                        # Run alert task
                        logger.debug('Run alarm')
                        alarm_status = run_alarm(alarm_obj, logger)

                if alarm_obj.period == PERIOD.MONTH:  # Month
                    if diff_run == 30:  # every month
                        # Run alert task
                        logger.debug('Run alarm')
                        alarm_status = run_alarm(alarm_obj, logger)
            except:
                # create alarm report
                AlarmReport.objects.create(alarm=alarm_obj, calculatedvalue=alarm_obj.alert_value, status=1)

        logger.debug('TASK :: chk_alarm finished')
        return alarm_status['running_alarm_status']


def notify_admin_without_mail(notice_id, email_id):
    """Send notification to admin as well as mail to recipient of alarm"""
    # Get all the admin users - admin superuser
    all_admin_user = User.objects.filter(is_superuser=True)
    for user in all_admin_user:
        recipient = user

        # send notification
        if notification:
            note_label = notification.NoticeType.objects.get(default=notice_id).label
            notification.send([recipient], note_label, {'from_user': user}, sender=user)
    return True


@task
def blacklist_whitelist_notification(notice_type):
    """
    Send email notification whne destination number matched with
    blacklist or whitelist.

    **Usage**:

        blacklist_whitelist_notification.delay(notice_type)
    """
    if notice_type == NOTICE_TYPE.blacklist_prefix:
        notice_type_name = 'blacklist'
    if notice_type == NOTICE_TYPE.whitelist_prefix:
        notice_type_name = 'whitelist'

    logger = blacklist_whitelist_notification.get_logger()
    logger.info('TASK :: %s_notification called' % notice_type_name)
    notice_type_obj = notification.NoticeType.objects.get(default=notice_type)
    try:
        notice_obj = notification.Notice.objects.\
            filter(notice_type=notice_type_obj).\
            latest('added')
        # Get time difference between two time intervals
        prevtime = str(datetime.time(notice_obj.added.replace(microsecond=0)))
        curtime = str(datetime.time(datetime.now().replace(microsecond=0)))
        FMT = '%H:%M:%S'
        diff = datetime.strptime(curtime, FMT) - datetime.strptime(prevtime, FMT)
        # if difference is more than X min than notification resend
        if int(diff.seconds / 60) >= settings.DELAY_BETWEEN_MAIL_NOTIFICATION:
            # blacklist notification id - 3 | whitelist notification type - 4
            notify_admin_without_mail(notice_type, 'admin@localhost.com')
    except:
        # blacklist notification type - 3 | whitelist notification type - 4
        notify_admin_without_mail(notice_type, 'admin@localhost.com')
    logger.debug('TASK :: %s_notification finished' % notice_type_name)
    return True


# Email previous day's CDR Report

class send_cdr_report(PeriodicTask):

    """A periodic task to send previous day's CDR Report as mail

    **Usage**:

        send_cdr_report.delay()
    """

    run_every = timedelta(seconds=86400)  # every day

    @only_one(ikey="send_cdr_report", timeout=LOCK_EXPIRE)
    def run(self, **kwargs):
        logger = self.get_logger()
        logger.info('TASK :: send_cdr_report')

        for c_user in User.objects.filter(is_staff=True, is_active=True):
            from_email = c_user.email
            try:
                to = UserProfile.objects.get(user=c_user).multiple_email
            except UserProfile.DoesNotExist:
                to = ''
                logger.error('Error : UserProfile notfound (user_id:%d)' % c_user.id)

            mail_data = get_cdr_mail_report(c_user)

            subject = _('CDR Report')

            html_content = get_template('cdr/mail_report_template.html')\
                .render(Context({
                    'yesterday_date': mail_data['yesterday_date'],
                    'rows': mail_data['rows'],
                    'total_duration': mail_data['total_duration'],
                    'total_calls': mail_data['total_calls'],
                    'ACH': mail_data['metric_aggr']['ACH'],
                    'ACD': mail_data['metric_aggr']['ACD'],
                    'country_analytic_array': mail_data['country_analytic_array'],
                    'hangup_analytic_array': mail_data['hangup_analytic_array']
                }
                ))

            msg = EmailMultiAlternatives(subject, html_content, from_email, [to])
            logger.info('Email sent to %s' % to)
            msg.content_subtype = 'html'
            msg.send()

        logger.debug('TASK :: send_cdr_report finished')
        return True
