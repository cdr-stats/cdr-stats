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
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_lazy as _
from random import choice
from uuid import uuid1
from pymongo.connection import Connection
from pymongo.errors import ConnectionFailure
import sys

import random
import datetime
import time
import json, ast

random.seed()

HANGUP_CAUSE = ['NORMAL_CLEARING', 'NORMAL_CLEARING', 'NORMAL_CLEARING', 
                'NORMAL_CLEARING', 'USER_BUSY', 'NO_ANSWER', 'CALL_REJECTED', 
                'INVALID_NUMBER_FORMAT']
HANGUP_CAUSE_Q850 = ['16', '17', '18', '19', '20', '21']

#list of exit code : http://www.howtocallabroad.com/codes.html
COUNTRY_PREFIX = ['0034', '011346', '+3465', #Spain
                  '3912', '39',  '+3928', #Italy
                  '15', '17', #US
                  '16', '1640', #Canada
                  '44', '441', '00442', #UK
                  '45', '451', '00452', #Denmark
                  '32', '321', '0322', #Belgium
                  '91', '919', '0911', #India
                  '53', '531', '00532', #Cuba
                  '55', '551', '552', #Brazil
                  ]

def NumberLong(var):
    return var

def generate_cdr_data (day_delta_int):

    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    digit = "1234567890"

    delta_days = random.randint(0, day_delta_int)
    delta_minutes = random.randint(1, 1440)
    answer_stamp = (datetime.datetime.now() - \
                    datetime.timedelta(minutes=delta_minutes) - \
                    datetime.timedelta(days=delta_days))
    
    # convert answer_stamp into milliseconds
    start_uepoch = int(time.mktime(answer_stamp.timetuple()))

    caller_id = '' . join([choice(digit) for i in range(8)])
    channel_name = 'sofia/internal/' + caller_id +'@127.0.0.1'
    destination_number  = '' . join([choice(digit) for i in range(8)])

    destination_number  = choice(COUNTRY_PREFIX) + destination_number
    
    hangup_cause = choice(HANGUP_CAUSE)
    hangup_cause_q850 = choice(HANGUP_CAUSE_Q850)
    if hangup_cause == 'NORMAL_CLEARING':
        duration = random.randint(1, 200)
        billsec = random.randint(1, 200)
    else:
        duration = 0
        billsec = 0
        
    end_stamp = str(datetime.datetime.now() - \
                    datetime.timedelta(minutes=delta_minutes) - \
                    datetime.timedelta(days=delta_days) + \
                    datetime.timedelta(seconds=duration))
    uuid = str(uuid1())

    return (answer_stamp, start_uepoch, caller_id, channel_name, \
                destination_number, hangup_cause, hangup_cause_q850, duration, \
                billsec, end_stamp, uuid)


class Command(BaseCommand):
    # Usage : generate_cdr 500
    args = ' no_of_record, delta_day '
    help = "Generate random CDRs \n---------------------------------\n" + \
            "python manage.py generate_cdr <NUMBER_OF_CDR> <DELTA_DAYS>"

    def handle(self, *args, **options):
        """Note that subscriber created this way are only for devel purposes"""
        
        if not args or len(args)!=2:
            print self.help
            #print >> sys.stderr
            raise SystemExit
        
        no_of_record = args[0]
        day_delta = args[1]
        try:
            day_delta_int = int(day_delta)
        except ValueError:
            day_delta_int = 30
        
        #Retrieve the field collection in the mongo_import list
        ipaddress = settings.CDR_MONGO_IMPORT.items()[0][0]

        #Connect on MongoDB Database
        host = settings.CDR_MONGO_IMPORT[ipaddress]['host']
        port = settings.CDR_MONGO_IMPORT[ipaddress]['port']
        db_name = settings.CDR_MONGO_IMPORT[ipaddress]['db_name']
        try:
            connection = Connection(host, port)
            DB_CONNECTION = connection[db_name]
        except ConnectionFailure, e:
            sys.stderr.write("Could not connect to MongoDB: %s - %s" % \
                                                            (e, ipaddress))
            sys.exit(1)

        for i in range(1, int(no_of_record) + 1):
            
            (answer_stamp, start_uepoch, caller_id, channel_name, \
                destination_number, hangup_cause, hangup_cause_q850, duration, \
                billsec, end_stamp, uuid) = generate_cdr_data (day_delta_int)
            print "CDR => date:%s, uuid:%s, duration:%s, pn:%s, hangup_cause:%s" % \
                    (answer_stamp, uuid, duration, destination_number, hangup_cause)


            cdr_json = {
                      "channel_data":{
                        "state":"CS_REPORTING",
                        "direction":"inbound",
                        "state_number":11,
                        "flags":"0=1;1=1;35=1;36=1;38=1;41=1;51=1",
                        "caps":"1=1;2=1;3=1;4=1;5=1;6=1"
                      },
                      "variables":{
                        "direction":"inbound",
                        "uuid": uuid,
                        "session_id":"3",
                        "sip_local_network_addr":"192.168.1.21",
                        "sip_network_ip":"192.168.1.21",
                        "sip_network_port":"60536",
                        "sip_received_ip":"192.168.1.21",
                        "sip_received_port":"60536",
                        "sip_via_protocol":"udp",
                        "sip_authorized":"true",
                        "sip_number_alias":"1000",
                        "sip_auth_username":"1000",
                        "sip_auth_realm":"127.0.0.1",
                        "number_alias":"1000",
                        "user_name":"1000",
                        "domain_name":"0.0.0.0",
                        "record_stereo":"true",
                        "default_gateway":"example.com",
                        "default_areacode":"918",
                        "transfer_fallback_extension":"operator",
                        "toll_allow":"domestic,international,local",
                        "accountcode":"1000",
                        "user_context":"telechat",
                        "effective_caller_id_name":"Extension 1000",
                        "effective_caller_id_number":"1000",
                        "outbound_caller_id_name":"FreeSWITCH",
                        "outbound_caller_id_number":"0000000000",
                        "callgroup":"techsupport",
                        "sip_from_user":"1000",
                        "sip_from_uri":"1000@127.0.0.1",
                        "sip_from_host":"127.0.0.1",
                        "sip_from_user_stripped":"1000",
                        "sofia_profile_name":"internal",
                        "sip_req_user":"9995",
                        "sip_req_uri":"9995@127.0.0.1",
                        "sip_req_host":"127.0.0.1",
                        "sip_to_user":"9995",
                        "sip_to_uri":"9995@127.0.0.1",
                        "sip_to_host":"127.0.0.1",
                        "sip_contact_user":"nkdoehyp",
                        "sip_contact_port":"60536",
                        "sip_contact_uri":"nkdoehyp@192.168.1.21:60536",
                        "sip_contact_host":"192.168.1.21",
                        "channel_name":str(channel_name),
                        "sip_via_host":"192.168.1.21",
                        "sip_via_port":"60536",
                        "sip_via_rport":"60536",
                        "max_forwards":"70",
                        "presence_id":"1000@127.0.0.1",
                        "switch_r_sdp":"v=0\r\no=- 3536510753 \r\n",
                        "sip_remote_audio_rtcp_port":"50005",
                        "sip_audio_recv_pt":"9",
                        "sip_use_codec_name":"G722",
                        "sip_use_codec_rate":"8000",
                        "sip_use_codec_ptime":"20",
                        "read_codec":"G722",
                        "read_rate":"16000",
                        "write_codec":"G722",
                        "write_rate":"16000",
                        "call_uuid": uuid,
                        "sip_local_sdp_str":"v=0\no=FreeSWITCH 1327491731\n",
                        "local_media_ip":"192.168.1.21",
                        "local_media_port":"30222",
                        "advertised_media_ip":"192.168.1.21",
                        "sip_use_pt":"9",
                        "rtp_use_ssrc":"3375048911",
                        "sip_2833_send_payload":"101",
                        "sip_2833_recv_payload":"101",
                        "remote_media_ip":"192.168.1.21",
                        "remote_media_port":"50004",
                        "endpoint_disposition":"ANSWER",
                        "tts_engine":"flite",
                        "tts_voice":"kal",
                        "sip_to_tag":"Qjy1Bg20NZvjN",
                        "sip_from_tag":"cDrHnBstk5nfARzMY6G4rHKqbRBgZYjG",
                        "sip_cseq":"23146",
                        "sip_call_id":"QBez.ald9uHXShRNxPYTwmHt1rR7O1R6",
                        "sip_from_display":"1000",
                        "sip_full_from":"\"1000\" <sip:1000@127.0.0.1>;tag=cD",
                        "sip_full_to":"<sip:9995@127.0.0.1>;tag=Qjy1Bg20NZvjN",
                        "current_application_data":"2000",
                        "current_application":"delay_echo",
                        "sip_term_status":"200",
                        "proto_specific_hangup_cause":"sip:200",
                        "sip_term_cause":"16",
                        "sip_user_agent":"Blink 0.2.8 (Linux)",
                        "sip_hangup_disposition":"recv_bye",
                        "hangup_cause":str(hangup_cause),
                        "hangup_cause_q850":str(hangup_cause_q850),
                        "digits_dialed":"none",
                        "start_stamp":str(answer_stamp),
                        "profile_start_stamp":str(answer_stamp),
                        "answer_stamp":str(answer_stamp),
                        "end_stamp":str(end_stamp),
                        "start_epoch":"1327521953",
                        "start_uepoch":str(start_uepoch),
                        "profile_start_epoch":"1327521953",
                        "profile_start_uepoch":"1327521953952257",
                        "answer_epoch":"1327521953",
                        "answer_uepoch":"1327521953952257",
                        "bridge_epoch":"0",
                        "bridge_uepoch":"0",
                        "last_hold_epoch":"0",
                        "last_hold_uepoch":"0",
                        "hold_accum_seconds":"0",
                        "hold_accum_usec":"0",
                        "hold_accum_ms":"0",
                        "resurrect_epoch":"0",
                        "resurrect_uepoch":"0",
                        "progress_epoch":"0",
                        "progress_uepoch":"0",
                        "progress_media_epoch":"0",
                        "progress_media_uepoch":"0",
                        "end_epoch":"1327521966",
                        "end_uepoch":"1327521966912241",
                        "last_app":"delay_echo",
                        "last_arg":"2000",
                        "caller_id": str(caller_id),
                        "duration":str(duration),
                        "billsec":str(billsec),
                        "progresssec":"0",
                        "answersec":"0",
                        "waitsec":"0",
                        "progress_mediasec":"0",
                        "flow_billsec":"13",
                        "mduration":"12960",
                        "billmsec":"12960",
                        "progressmsec":"0",
                        "answermsec":"0",
                        "waitmsec":"0",
                        "progress_mediamsec":"0",
                        "flow_billmsec":"12960",
                        "uduration":"12959984",
                        "billusec":"12959984",
                        "progressusec":"0",
                        "answerusec":"0",
                        "waitusec":"0",
                        "progress_mediausec":"0",
                        "flow_billusec":"12959984",
                        "rtp_audio_rtcp_octet_count":"0"
                      },
                      "app_log":{
                        "application":{
                          "app_name":"answer",
                          "app_data":"",
                          "app_stamp":NumberLong("1327521953967984")
                        }
                      },
                      "callflow":{
                        "dialplan":"XML",
                        "profile_index":"1",
                        "extension":{
                          "name":"delay_echo",
                          "number":"9995",
                          "application":{
                            "app_name":"answer",
                            "app_data":""
                          }
                        },
                        "caller_profile":{
                          "username":"1000",
                          "dialplan":"XML",
                          "caller_id_name": str(caller_id),
                          "ani": str(caller_id),
                          "aniii":"",
                          "caller_id_number": str(caller_id),
                          "network_addr":"192.168.1.21",
                          "rdnis":"",
                          "destination_number":str(destination_number),
                          "uuid":uuid,
                          "source":"mod_sofia",
                          "context":"telechat",
                          "chan_name":"sofia/internal/1000@127.0.0.1"
                        },
                        "times":{
                          "created_time":NumberLong("1327521953952257"),
                          "profile_created_time":NumberLong("1327521953952257"),
                          "progress_time":NumberLong(0),
                          "progress_media_time":NumberLong(0),
                          "answered_time":NumberLong("1327521953952257"),
                          "bridged_time":NumberLong(0),
                          "last_hold_time":NumberLong(0),
                          "hold_accum_time":NumberLong(0),
                          "hangup_time":NumberLong("1327521966912241"),
                          "resurrect_time":NumberLong(0),
                          "transfer_time":NumberLong(0)
                        }
                      }
                    }
            
            DB_CONNECTION[settings.CDR_MONGO_IMPORT[ipaddress]['collection']].\
                insert(cdr_json)