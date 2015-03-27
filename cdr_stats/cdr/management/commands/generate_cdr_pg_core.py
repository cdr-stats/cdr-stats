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
from django.core.management.base import BaseCommand
from cdr.models import CDR, AccountCode
from optparse import make_option
from django.contrib.auth.models import User
from switch.models import Switch


class Command(BaseCommand):
    args = ' no_of_record, delta_day '
    help = "Generate random CDRs\n"\
           "---------------------------------\n"\
           "python manage.py generate_cdr --number-cdr=100 --delta-day=0 [--duration=10]"

    option_list = BaseCommand.option_list + (
        make_option('--number-cdr', default=None, dest='number-cdr', help=help),
        make_option('--delta-day', default=None, dest='delta-day', help=help),
        make_option('--duration', default=None, dest='duration', help=help),
    )

    def handle(self, *args, **options):

        no_of_record = 1  # default
        if options.get('number-cdr'):
            no_of_record = int(options.get('number-cdr', 1))

        day_delta_int = 30  # default
        if options.get('delta-day'):
            day_delta_int = int(options.get('delta-day', 30))

        arg_duration = False  # default
        if options.get('duration'):
            arg_duration = int(options.get('duration'), -1)

        list_user = User.objects.all()
        user = list_user[0]
        list_switch = Switch.objects.all()
        switch = list_switch[0]
        list_acc = AccountCode.objects.all()
        if list_acc:
            acc = list_acc[0]
        else:
            acc = None

        for i in range(1, int(no_of_record) + 1):
            (
                callid, answer_stamp, start_uepoch, caller_id,
                channel_name, destination_number, dialcode, hangup_cause,
                hangup_cause_q850, duration, billsec, end_stamp,
                cdr_source_type, authorized, country_id, direction,
                # accountcode, buy_rate, buy_cost, sell_rate, sell_cost
            ) = CDR.generate_fake_cdr(day_delta_int)

            if arg_duration and arg_duration >= 0:
                duration = arg_duration

            if i % 100 == 0:
                print '%d CDRs created...' % i

            print "CDR => date:%s, callid:%s, dur:%s, pn:%s, dc:%s, country:%s, hg_cause:%s" % \
                (answer_stamp, callid, duration, destination_number, dialcode, country_id, hangup_cause)

            cdr_json = {
                'channel_data': {
                    'state': 'CS_REPORTING',
                    'direction': 'inbound'},
                'variables': {
                    'direction': 'inbound',
                    'uuid': callid,
                    'session_id': '3',
                    'sip_network_ip': '192.168.1.21',
                    'sip_network_port': '60536',
                    'sip_authorized': 'true',
                    'sip_number_alias': '1000',
                    'sip_auth_username': '1000',
                    'sip_auth_realm': '127.0.0.1',
                    'user_name': '1000',
                    'accountcode': '1000',
                    'channel_name': str(channel_name),
                    'sip_via_host': '192.168.1.21',
                    'sip_via_port': '60536',
                    'presence_id': '1000@127.0.0.1',
                    'sip_use_codec_name': 'G722',
                    'sip_use_codec_rate': '8000',
                    'read_codec': 'G722',
                    'read_rate': '16000',
                    'write_codec': 'G722',
                    'write_rate': '16000',
                    'call_uuid': callid,
                    'remote_media_ip': '192.168.1.21',
                    'endpoint_disposition': 'ANSWER',
                    'current_application_data': '2000',
                    'current_application': 'delay_echo',
                    'sip_term_status': '200',
                    'proto_specific_hangup_cause': 'sip:200',
                    'sip_term_cause': '16',
                    'hangup_cause': str(hangup_cause),
                    'hangup_cause_q850': str(hangup_cause_q850),
                    'start_stamp': str(answer_stamp),
                    'profile_start_stamp': str(answer_stamp),
                    'answer_stamp': str(answer_stamp),
                    'end_stamp': str(end_stamp),
                    'start_epoch': '1327521953',
                    'start_uepoch': str(start_uepoch),
                    'answer_epoch': '1327521953',
                    'answer_uepoch': '1327521953952257',
                    'end_epoch': '1327521966',
                    'end_uepoch': '1327521966912241',
                    'last_app': 'delay_echo',
                    'last_arg': '2000',
                    'caller_id': str(caller_id),
                    'duration': str(duration),
                    'billsec': str(billsec),
                    'answersec': '0',
                    'waitsec': '0',
                    'mduration': '12960',
                    'billmsec': '12960',
                    'uduration': '12959984',
                    'billusec': '12959984',
                },
                'callflow': [
                    {
                        'dialplan': 'XML',
                        'caller_profile': {
                            'caller_id_name': str(caller_id),
                            'ani': str(caller_id),
                            'caller_id_number': str(caller_id),
                            'network_addr': '192.168.1.21',
                            'destination_number': str(destination_number),
                            'uuid': callid,
                            'chan_name': 'sofia/internal/1000@127.0.0.1'
                        }
                    }
                ]
            }
            cdr = CDR(user=user, switch=switch, cdr_source_type=cdr_source_type,
                      callid=callid, caller_id_number=caller_id, destination_number=destination_number,
                      dialcode_id=dialcode, starting_date=answer_stamp, duration=duration,
                      billsec=billsec, hangup_cause=hangup_cause, direction=direction,
                      country_id=country_id, authorized=authorized, accountcode=acc,
                      data=cdr_json)
            cdr.save()
