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
#from django.utils.safestring import mark_safe
from random import choice
from optparse import make_option
import random
import datetime


random.seed()

HANGUP_CAUSE = ['NORMAL_CLEARING', 'NORMAL_CLEARING', 'NORMAL_CLEARING',
                'NORMAL_CLEARING', 'USER_BUSY', 'NO_ANSWER', 'CALL_REJECTED',
                'INVALID_NUMBER_FORMAT']

CONC_CALL_AGG = settings.DBCON[settings.MONGO_CDRSTATS['CONC_CALL_AGG']]


def set_concurrentcall_analytic(call_date, switch_id, accountcode, numbercall):
    """Create Concurrent call Analytic"""
    date_minprec = datetime.datetime(
        call_date.year, call_date.month, call_date.day,
        call_date.hour, call_date.minute)

    #Get current value in CONC_CALL_AGG
    get_cc_obj = CONC_CALL_AGG.find_one(
        {
            "date": date_minprec,
            "switch_id": switch_id,
            "accountcode": accountcode
        })

    if not get_cc_obj:
        #If doesn't exist set numbercall
        #TODO: Add index to CONC_CALL_AGG
        CONC_CALL_AGG.insert(
            {
                "date": date_minprec,
                "switch_id": switch_id,
                "accountcode": accountcode,
                "numbercall": int(numbercall),
            })
    else:
        if int(get_cc_obj['numbercall']) < int(numbercall):
            #If numbercall is not max, update
            CONC_CALL_AGG.update(
                {
                    "date": date_minprec,
                    "switch_id": switch_id,
                    "accountcode": accountcode,
                },
                {
                    "$set": {
                        "numbercall": int(numbercall),
                    }
                })
    return True


class Command(BaseCommand):
    help = "Generate random Concurrent calls\n"\
           "---------------------------------\n"\
           "python manage.py generate_concurrent_call --delta-day=0\n"\
           "python manage.py generate_concurrent_call -d 0"

    option_list = BaseCommand.option_list + (
        make_option('--delta-day', '-d',
            default=None,
            dest='delta-day',
            help=help),
    )

    def handle(self, *args, **options):
        """Note that subscriber created this way are only for devel purposes"""

        no_of_record = 86400  # second in one day

        if options.get('delta-day'):
            try:
                day_delta_int = int(options.get('delta-day'))
            except ValueError:
                day_delta_int = 1
        else:
            day_delta_int = 1

        accountcode = ''.join([choice('1234567890') for i in range(4)])
        accountcode = '12345'
        now = datetime.datetime.today()
        date_now = datetime.datetime(now.year, now.month, now.day, now.hour,
                                     now.minute, now.second, 0)

        today_delta = datetime.timedelta(hours=datetime.datetime.now().hour,
                minutes=datetime.datetime.now().minute,
                seconds=datetime.datetime.now().second)
        date_today = date_now - today_delta \
            - datetime.timedelta(days=day_delta_int)

        numbercall = 10

        for i in range(0, int(no_of_record)):
            delta_duration = i
            call_date = date_today + datetime.timedelta(seconds=delta_duration)

            delta_call = random.randint(-2, 2)
            numbercall = numbercall + delta_call
            switch_id = 1

            if numbercall < 0:
                numbercall = 0
            print '%s (accountcode:%s, switch_id:%d) ==> %d' % (call_date,
                    accountcode, switch_id, numbercall)

            call_json = {'switch_id': switch_id, 'call_date': call_date,
                         'numbercall': numbercall, 'accountcode': accountcode}

            settings.DBCON[settings.MONGO_CDRSTATS['CONC_CALL']].insert(call_json)

            #Create collection for Analytics
            set_concurrentcall_analytic(call_date, switch_id, accountcode, numbercall)

        # Add unique index with sorting
        try:
            settings.DBCON[settings.MONGO_CDRSTATS['CONC_CALL']].ensure_index([('call_date', -1),
                ('switch_id', 1), ('accountcode', 1)], unique=True)
        except:
            print "Error: Adding unique index"

        # print "Create map reduce for concurrent call"
        # # Map-reduce collection
        # map = \
        #     mark_safe(u'''
        #     function(){
        #         var year = this.call_date.getFullYear();
        #         var month = this.call_date.getMonth();
        #         var day = this.call_date.getDate();
        #         var hours = this.call_date.getHours();
        #         var minutes = this.call_date.getMinutes();
        #         var d = new Date(year, month, day, hours, minutes);
        #         emit(
        #         {
        #             f_Switch: this.switch_id,
        #             g_Millisec: d.getTime()
        #         },
        #         {
        #         numbercall__max: this.numbercall, call_date: this.call_date,
        #         accountcode: this.accountcode
        #         } )
        #       }''')

        # reduce = \
        #     mark_safe(u'''
        #          function(key,vals) {
        #              var ret = {numbercall__max: 0, call_date: '',
        #                          accountcode: ''};
        #              max = vals[0].numbercall__max;

        #              for (var i=0; i < vals.length; i++){

        #                 if(vals[i].numbercall__max > max){
        #                     max = parseInt(vals[i].numbercall__max);
        #                 };
        #              }
        #              ret.numbercall__max = max;
        #              ret.call_date = vals[0].call_date;
        #              ret.accountcode = vals[0].accountcode;
        #              return ret;
        #          }
        #          ''')

        # cdr_conn_call = settings.DBCON[settings.MONGO_CDRSTATS['CONC_CALL']]

        # cdr_conn_call.map_reduce(map, reduce, out=settings.MONGO_CDRSTATS['CONC_CALL_AGG'])
