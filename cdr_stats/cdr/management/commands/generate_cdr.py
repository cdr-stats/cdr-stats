# -*- coding: utf-8 -*-

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
from django.conf import settings
from django.core.management.base import BaseCommand
from optparse import make_option
from random import choice
from uuid import uuid1
from pymongo.connection import Connection
from pymongo.errors import ConnectionFailure
import sys
import random
import datetime
import time

random.seed()

HANGUP_CAUSE = ['NORMAL_CLEARING', 'NORMAL_CLEARING', 'NORMAL_CLEARING',
                'NORMAL_CLEARING', 'USER_BUSY', 'NO_ANSWER', 'CALL_REJECTED',
                'INVALID_NUMBER_FORMAT']
HANGUP_CAUSE_Q850 = ['16', '17', '18', '19', '20', '21']

#list of exit code : http://www.howtocallabroad.com/codes.html
COUNTRY_PREFIX = ['0034', '011346', '+3465',  # Spain
                  '3912', '39', '+3928',  # Italy
                  '15', '17',  # US
                  '16', '1640',  # Canada
                  '44', '441', '00442',  # UK
                  '45', '451', '00452',  # Denmark
                  '32', '321', '0322',  # Belgium
                  '91', '919', '0911',  # India
                  '53', '531', '00532',  # Cuba
                  '55', '551', '552',  # Brazil
                  ]


def generate_cdr_data(day_delta_int):
    """
    TODO: Add function documentation
    """
    digit = '1234567890'

    delta_days = random.randint(0, day_delta_int)
    delta_minutes = random.randint(1, 1440)
    answer_stamp = datetime.datetime.now() \
        - datetime.timedelta(minutes=delta_minutes) \
        - datetime.timedelta(days=delta_days)

    # convert answer_stamp into milliseconds
    start_uepoch = int(time.mktime(answer_stamp.timetuple()))

    caller_id = ''.join([choice(digit) for i in range(8)])
    channel_name = 'sofia/internal/' + caller_id + '@127.0.0.1'
    destination_number = ''.join([choice(digit) for i in range(8)])

    if random.randint(1, 20) == 1:
        #Add local calls
        destination_number = ''.join([choice(digit) for i in range(5)])
    else:
        #International calls
        destination_number = choice(COUNTRY_PREFIX) + destination_number

    hangup_cause = choice(HANGUP_CAUSE)
    hangup_cause_q850 = choice(HANGUP_CAUSE_Q850)
    if hangup_cause == 'NORMAL_CLEARING':
        duration = random.randint(1, 200)
        billsec = random.randint(1, 200)
    else:
        duration = 0
        billsec = 0

    end_stamp = str(datetime.datetime.now()
                    - datetime.timedelta(minutes=delta_minutes)
                    - datetime.timedelta(days=delta_days)
                    + datetime.timedelta(seconds=duration))
    uuid = str(uuid1())

    return (
        answer_stamp,
        start_uepoch,
        caller_id,
        channel_name,
        destination_number,
        hangup_cause,
        hangup_cause_q850,
        duration,
        billsec,
        end_stamp,
        uuid,
    )


class Command(BaseCommand):
    args = ' no_of_record, delta_day '
    help = "Generate random CDRs\n"\
           "---------------------------------\n"\
           "python manage.py generate_cdr --number-cdr=100 --delta-day=0 [--duration=10]"

    option_list = BaseCommand.option_list + (
        make_option('--number-cdr',
                    default=None,
                    dest='number-cdr',
                    help=help),
        make_option('--delta-day',
                    default=None,
                    dest='delta-day',
                    help=help),
        make_option('--duration',
                    default=None,
                    dest='duration',
                    help=help),
    )

    def handle(self, *args, **options):
        """
        Note that subscriber created this way are only for devel purposes
        """
        no_of_record = 1  # default
        if options.get('number-cdr'):
            try:
                no_of_record = int(options.get('number-cdr'))
            except ValueError:
                no_of_record = 1

        day_delta_int = 30  # default
        if options.get('delta-day'):
            try:
                day_delta_int = int(options.get('delta-day'))
            except ValueError:
                day_delta_int = 30

        arg_duration = False  # default
        if options.get('duration'):
            try:
                arg_duration = options.get('duration')
                arg_duration = int(arg_duration)
            except ValueError:
                arg_duration = 0

        # Retrieve the field collection in the mongo_import list
        ipaddress = settings.CDR_BACKEND.items()[0][0]

        #Connect to Database
        db_name = settings.CDR_BACKEND[ipaddress]['db_name']
        table_name = settings.CDR_BACKEND[ipaddress]['table_name']
        db_engine = settings.CDR_BACKEND[ipaddress]['db_engine']
        cdr_type = settings.CDR_BACKEND[ipaddress]['cdr_type']
        user = settings.CDR_BACKEND[ipaddress]['user']
        password = settings.CDR_BACKEND[ipaddress]['password']
        host = settings.CDR_BACKEND[ipaddress]['host']
        port = settings.CDR_BACKEND[ipaddress]['port']

        if db_engine != 'mongodb' or cdr_type != 'freeswitch':
            sys.stderr.write('Generate CDRs is only working for mongoDB and freeswitch, please review your CDR_BACKEND settings')
            sys.exit(1)

        try:
            connection = Connection(host, port)
            DBCON = connection[db_name]
            DBCON.autentificate(user, password)
        except ConnectionFailure, e:
            sys.stderr.write('Could not connect to MongoDB: %s - %s' % (e,
                             ipaddress))
            sys.exit(1)

        for i in range(1, int(no_of_record) + 1):
            (
                answer_stamp,
                start_uepoch,
                caller_id,
                channel_name,
                destination_number,
                hangup_cause,
                hangup_cause_q850,
                duration,
                billsec,
                end_stamp,
                uuid,
            ) = generate_cdr_data(day_delta_int)

            if type(arg_duration) == int:
                duration = arg_duration

            if i % 100 == 0:
                print '%d CDRs created...' % i

            print "CDR => date:%s, uuid:%s, dur:%s, pn:%s, hg_cause:%s" % \
                (answer_stamp, uuid, duration, destination_number, hangup_cause)

            cdr_json = {
                'channel_data': {
                    'state': 'CS_REPORTING',
                    'direction': 'inbound'},
                'variables': {
                    'direction': 'inbound',
                    'uuid': uuid,
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
                    'call_uuid': uuid,
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
                        'caller_profile': {'caller_id_name': str(caller_id),
                        'ani': str(caller_id),
                        'caller_id_number': str(caller_id),
                        'network_addr': '192.168.1.21',
                        'destination_number': str(destination_number),
                        'uuid': uuid,
                        'chan_name': 'sofia/internal/1000@127.0.0.1'}
                    }
                ]
            }

            DBCON[table_name].insert(cdr_json)
