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
from __future__ import division
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.mail import send_mail, mail_admins
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from celery.task import Task, PeriodicTask
from celery.schedules import crontab
from celery.decorators import task, periodic_task
from notification import models as notification
from cdr.common_tasks import single_instance_task
from cdr_alert.models import AlertRemovePrefix, Alarm, AlarmReport, Blacklist, Whitelist
from cdr.mapreduce import mapreduce_task_cdr_alert
from cdr.functions_def import get_hangupcause_id
from cdr.views import get_cdr_mail_report
from user_profile.models import UserProfile

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


# Lock expires in 30 minutes
LOCK_EXPIRE = 60 * 30


cdr_data = settings.DB_CONNECTION[settings.MG_CDR_COMMON]
(map, reduce, finalize_fun, out) = mapreduce_task_cdr_alert()


def get_start_end_date(alert_condition_add_on):
    """Get start and end date according to alert_condition_add_on"""
    dt_list = {}
    # yesterday's date
    end_date = datetime.today() + relativedelta(days=-1)
    if alert_condition_add_on == 1:  # same day
        comp_days = 1
    if alert_condition_add_on == 2:  # Same day in the previous week
        comp_days = 7

    start_date= end_date + relativedelta(days=-int(comp_days))
    #get Previous dates and Current dates
    dt_list['p_start_date'] = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0, 0)
    dt_list['p_end_date'] = datetime(start_date.year, start_date.month, start_date.day, 23, 59, 59, 999999)
    dt_list['c_start_date'] = datetime(end_date.year, end_date.month, end_date.day, 0, 0, 0, 0)
    dt_list['c_end_date'] = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, 999999)

    return dt_list


def notify_admin_with_mail(notice_id, email_id):
    """Send notification to all admin as well as mail to recipient of alarm"""
    # Get all the admin users - admin staff
    all_admin_user = User.objects.filter(is_staff=True) # is_superuser=True
    for user in all_admin_user:
        recipient = user

        # send notification
        if notification:
            note_label = notification.NoticeType.objects.get(default=notice_id)
            notification.send([recipient],
                              note_label.label,
                              {"from_user": user},
                              sender=user)
        # Send mail to ADMINS
        subject = _('Alert')
        message = _('Alert Message "%(user)s" - "%(user_id)s"') \
                    % {'user': user, 'user_id': user.id}

        try:
            send_mail(subject, message, settings.SERVER_EMAIL, email_id)
        except:
            # mail_admins() is a shortcut for sending an email to the site admins,
            # as defined in the ADMINS setting
            mail_admins(subject, message)  # html_message='text/html'

    return True


def create_alarm_report_object(alarm_obj, status):
    # create alarm report
    # status - 1 - No alarm sent
    # status - 2 - Alarm sent
    AlarmReport.objects.create(alarm=alarm_obj,
                        calculatedvalue=alarm_obj.alert_value,
                        status=status)
    return True


def chk_alert_value(alarm_obj, current_value, previous_value=None):
    """ compare values with following conditions against alarm alert value

        *   Is less than | Is greater than
        *   Decrease by more than | Increase by more than
        *   % decrease by more than | % Increase by more than
    """
    if alarm_obj.alert_condition == 1:  # Is less than
        if alarm_obj.alert_value < current_value:
            notify_admin_with_mail(alarm_obj.type, alarm_obj.email_to_send_alarm)
            create_alarm_report_object(alarm_obj, status=2)
        else:
            create_alarm_report_object(alarm_obj, status=1)

    if alarm_obj.alert_condition == 2:  # Is greater than
        if alarm_obj.alert_value > current_value:
            notify_admin_with_mail(alarm_obj.type, alarm_obj.email_to_send_alarm)
            create_alarm_report_object(alarm_obj, status=2)
        else:
            create_alarm_report_object(alarm_obj, status=1)

    if alarm_obj.alert_condition == 3:  # Decrease by more than
        diff = abs(current_value - previous_value)
        if diff < alarm_obj.alert_value:
            notify_admin_with_mail(alarm_obj.type, alarm_obj.email_to_send_alarm)
            create_alarm_report_object(alarm_obj, status=2)
        else:
            create_alarm_report_object(alarm_obj, status=1)

    if alarm_obj.alert_condition == 4:  # Increase by more than
        diff = abs(current_value - previous_value)
        if diff > alarm_obj.alert_value:
            notify_admin_with_mail(alarm_obj.type, alarm_obj.email_to_send_alarm)
            create_alarm_report_object(alarm_obj, status=2)
        else:
            create_alarm_report_object(alarm_obj, status=1)

    # http://www.mathsisfun.com/percentage-difference.html
    if alarm_obj.alert_condition == 5:  # % decrease by more than
        diff = abs(current_value - previous_value)
        avg = (current_value + previous_value)/2
        percentage = (diff / avg) * 100
        if percentage < alarm_obj.alert_value:
            notify_admin_with_mail(alarm_obj.type, alarm_obj.email_to_send_alarm)
            create_alarm_report_object(alarm_obj, status=2)
        else:
            create_alarm_report_object(alarm_obj, status=1)

    if alarm_obj.alert_condition == 6:  # % Increase by more than
        diff = abs(current_value - previous_value)
        avg = (current_value + previous_value) / 2
        percentage = (diff / avg) * 100
        if percentage > alarm_obj.alert_value:
            notify_admin_with_mail(alarm_obj.type, alarm_obj.email_to_send_alarm)
            create_alarm_report_object(alarm_obj, status=2)
        else:
            create_alarm_report_object(alarm_obj, status=1)

    return True


def run_alarm(alarm_obj):
    """Alarm object"""
    if alarm_obj.type == 1:  # ALOC (average length of call)
        logger.debug("ALOC (average length of call)")
        # return start and end date of previous/current day
        dt_list = get_start_end_date(alarm_obj.alert_condition_add_on)

        # Previous date data
        query_var = {}
        query_var['start_uepoch'] = {'$gte': dt_list['p_start_date'],
                                     '$lte': dt_list['p_end_date']}
        # previous date map_reduce
        pre_total_data = cdr_data.map_reduce(map, reduce, out,
                                             query=query_var,
                                             finalize=finalize_fun,)
        pre_total_data = pre_total_data.find().sort([('_id.a_Year', -1),
                                                     ('_id.b_Month', -1)])

        pre_day_data = {}
        for doc in pre_total_data:
            pre_date = dt_list['p_start_date']
            pre_day_data[pre_date.strftime('%Y-%m-%d')] = doc['value']['duration__avg']
            if alarm_obj.alert_condition == 1 or alarm_obj.alert_condition == 2:
                chk_alert_value(alarm_obj, doc['value']['duration__avg'])
            else:
                previous_date_duration = doc['value']['duration__avg']

        # Current date data
        query_var = {}
        query_var['start_uepoch'] = {'$gte': dt_list['c_start_date'],
                                     '$lte': dt_list['c_end_date']}
        # current date map_reduce
        cur_total_data = cdr_data.map_reduce(map, reduce, out,
                                             query=query_var,
                                             finalize=finalize_fun,)

        cur_total_data = cur_total_data.find().sort([('_id.a_Year', -1),
                                                     ('_id.b_Month', -1)])

        cur_day_data = {}
        for doc in cur_total_data:
            cur_date = dt_list['c_start_date']
            cur_day_data[cur_date.strftime('%Y-%m-%d')] = doc['value']['duration__avg']
            if alarm_obj.alert_condition == 1 or alarm_obj.alert_condition == 2:
                chk_alert_value(alarm_obj, doc['value']['duration__avg'])
            else:
                current_date_duration = doc['value']['duration__avg']
                chk_alert_value(alarm_obj, current_date_duration, previous_date_duration)

    if alarm_obj.type == 2:  # ASR (Answer Seize Ratio)
        logger.debug("ASR (Answer Seize Ratio)")
        # return start and end date of previous/current day
        dt_list = get_start_end_date(alarm_obj.alert_condition_add_on)

        # hangup_cause_q850 - 16 - NORMAL_CLEARING
        hangup_cause_q850 = 16

        # Previous date data
        query_var = {}
        query_var['start_uepoch'] = {'$gte': dt_list['p_start_date'],
                                     '$lte': dt_list['p_end_date']}

        pre_total_record = cdr_data.find(query_var).count()
        query_var['hangup_cause_id'] = get_hangupcause_id(hangup_cause_q850)
        pre_total_answered_record = cdr_data.find(query_var).count()
        previous_asr = pre_total_answered_record / pre_total_record

        if alarm_obj.alert_condition == 1 or alarm_obj.alert_condition == 2:
            chk_alert_value(alarm_obj, previous_asr)
        else:
            previous_asr = previous_asr

        # Current date data
        query_var = {}
        query_var['start_uepoch'] = {'$gte': dt_list['c_start_date'],
                                     '$lte': dt_list['c_end_date']}
        cur_total_record = cdr_data.find(query_var).count()

        query_var['hangup_cause_id'] = get_hangupcause_id(hangup_cause_q850)

        cur_total_answered_record = cdr_data.find(query_var).count()
        current_asr = cur_total_answered_record / cur_total_record

        if alarm_obj.alert_condition == 1 or alarm_obj.alert_condition == 2:
            chk_alert_value(alarm_obj, current_asr)
        else:
            chk_alert_value(alarm_obj, current_asr, previous_asr)

    return True


class chk_alarm(PeriodicTask):
    """A periodic task to determine strange behavior in CDR

       Which will get all alarm from system and checked with
       alert condition value & if it is matched, user will be notified
       via mail

    **Usage**:

        chk_alarm.delay()
    """
    run_every = timedelta(seconds=86400)  # every day
    #run_every = crontab(hours=12, minute=30) #"Execute every day at 12:30AM."

    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("TASK :: chk_alarm called")

        alarm_objs = Alarm.objects.filter(status=1)  # all active alarms
        for alarm_obj in alarm_objs:
            try:
                alarm_report = AlarmReport.objects.filter(alarm=alarm_obj).latest('daterun')
                diff_between_task_run = (datetime.now() - alarm_report.daterun).days

                if alarm_obj.period == 1:  # Day
                    if diff_between_task_run == 1:  # every day
                        # Run alert task
                        logger.debug("Run alarm")
                        run_alarm(alarm_obj)

                if alarm_obj.period == 2:  # Week
                    if diff_between_task_run == 7:  # every week
                        # Run alert task
                        logger.debug("Run alarm")
                        run_alarm(alarm_obj)

                if alarm_obj.period == 3:  # Month
                    if diff_between_task_run == 30:  # every month
                        # Run alert task
                        logger.debug("Run alarm")
                        run_alarm(alarm_obj)
            except:
                # create alarm report
                AlarmReport.objects.create(
                                alarm=alarm_obj,
                               calculatedvalue=alarm_obj.alert_value,
                               status=1)

        logger.debug("TASK :: chk_alarm finished")
        return True


def notify_admin_without_mail(notice_id, email_id):
    """Send notification to admin as well as mail to recipient of alarm"""
    # TODO : Get all the admin users
    user = User.objects.get(pk=1)
    recipient = user

    # send notification
    if notification:
        note_label = notification.NoticeType.objects.get(default=notice_id)
        notification.send([recipient],
                          note_label.label,
                          {"from_user": user},
                          sender=user)
    return True


@task
def blacklist_whitelist_notification(notice_type):
    """
    Send notification to user while destination number matched with
    blacklist or whitelist

    **Usage**:

        blacklist_whitelist_notification.delay(notice_type)
    """
    if notice_type == 3:
        notice_type_name = 'blacklist'
    if notice_type == 4:
        notice_type_name = 'whitelist'

    logger = blacklist_whitelist_notification.get_logger()
    logger.info("TASK :: %s_notification called" % notice_type_name)
    notice_type_obj = notification.NoticeType.objects.get(default=notice_type)
    try:
        notice_obj = notification.Notice.objects.filter(
                            notice_type=notice_type_obj
                            ).latest('added')

        # Get time difference between two time intervals
        previous_time = str(datetime.time(notice_obj.added.replace(microsecond=0)))
        current_time = str(datetime.time(datetime.now().replace(microsecond=0)))
        FMT = '%H:%M:%S'
        diff = datetime.strptime(current_time, FMT) - datetime.strptime(previous_time, FMT)
        # if difference is more than 30 min than notification resend
        if int(diff.seconds / 60) >= 30:
            # blacklist notification id - 3 | whitelist notification type - 4
            notify_admin_without_mail(notice_type, 'admin@localhost.com')
    except:
        # blacklist notification type - 3 | whitelist notification type - 4
        notify_admin_without_mail(notice_type, 'admin@localhost.com')
    logger.debug("TASK :: %s_notification finished" % notice_type_name)
    return True


# Send previous day's CDR Report as mail
class send_cdr_report(PeriodicTask):
    """A periodic task to send previous day's CDR Report as mail

    **Usage**:

        send_cdr_report.delay()
    """
    run_every = timedelta(seconds=86400)  # every day

    @single_instance_task(key="send_cdr_report", timeout=LOCK_EXPIRE)
    def run(self, **kwargs):
        logger = self.get_logger()
        logger.info("TASK :: send_cdr_report")

        list_users = User.objects.filter(is_staff=True, is_active=True)
        for c_user in list_users:
            from_email = c_user.email
            try:
                user_profile_obj = UserProfile.objects.get(user=c_user)
                to = user_profile_obj.multiple_email
            except UserProfile.DoesNotExist:
                logger.error("Error send_cdr_report : UserProfile don't exist for this user (user_id:%d)" % c_user.id)

            mail_data = get_cdr_mail_report()

            subject = _('CDR Report')

            html_content = get_template('cdr/mail_report_template.html').render(
                            Context({
                                'yesterday_date': mail_data['yesterday_date'],
                                'rows': mail_data['rows'],
                                'total_duration': mail_data['total_duration'],
                                'total_calls': mail_data['total_calls'],
                                'ACT': mail_data['ACT'],
                                'ACD': mail_data['ACD'],
                                'country_analytic_array': mail_data['country_analytic_array'],
                                'hangup_analytic_array': mail_data['hangup_analytic_array'],
                            })
                        )
            msg = EmailMultiAlternatives(subject, html_content, from_email, [to])
            logger.info("Email sent to %s" % to)
            msg.content_subtype = "html"
            msg.send()

        logger.debug("TASK :: send_cdr_report finished")
        return True
