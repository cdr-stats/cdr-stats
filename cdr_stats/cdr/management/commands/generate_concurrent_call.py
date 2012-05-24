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
from django.utils.safestring import mark_safe
from random import choice
from uuid import uuid1
from datetime import *
from datetime import datetime
import sys
import random
import datetime
import json, ast

random.seed()

HANGUP_CAUSE = ['NORMAL_CLEARING','NORMAL_CLEARING','NORMAL_CLEARING','NORMAL_CLEARING',
                'USER_BUSY', 'NO_ANSWER', 'CALL_REJECTED', 'INVALID_NUMBER_FORMAT']

def NumberLong(var):
    return var

class Command(BaseCommand):
    # Usage : generate_concurrent_call 1
    args = ' delta_day '
    help = "Generate random Concurrent calls \n---------------------------------\n "\
            "python manage.py generate_concurrent_call <DELTA_DAYS>"

    def handle(self, *args, **options):
        """Note that subscriber created this way are only for devel purposes"""
        
        if not args:
            print self.help
            #print >> sys.stderr
            raise SystemExit
        
        no_of_record = 86400 # second in one day
        day_delta = args[0]
        try:
            day_delta_int = int(day_delta)
        except ValueError:
            day_delta_int = 1
            
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        digit = "1234567890"

        accountcode  = ''.join([choice(digit) for i in range(4)])
        accountcode = '12345'
        now = datetime.datetime.today()
        date_now = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute, now.second, 0)

        today_delta = datetime.timedelta(hours=datetime.datetime.now().hour, minutes=datetime.datetime.now().minute, seconds=datetime.datetime.now().second)
        date_today = date_now - today_delta - datetime.timedelta(days=day_delta_int)
        
        number_call = 0
        
        for i in range(0, int(no_of_record)):
            delta_duration = i
            call_date = (date_today + datetime.timedelta(seconds=delta_duration))

            delta_call = random.randint(-1, 1)
            number_call = number_call + delta_call
            switch_id = 1
            
            if number_call < 0:
                number_call = 0
            print "%s (accountcode:%s, switch_id:%d) ==> %s" % (call_date, accountcode, switch_id, str(number_call))
            
            call_json = {
                        "switch_id" : switch_id,
                        "call_date": call_date,
                        "numbercall": number_call,
                        "accountcode": accountcode,
                      }
            
            settings.DB_CONNECTION[settings.CDR_MONGO_CONC_CALL].insert(call_json)

        #TODO : Add unique index with sorting
        settings.DB_CONNECTION[settings.CDR_MONGO_CONC_CALL].ensure_index([('call_date', -1),
                                                                           ('switch_id', 1),
                                                                           ('accountcode', 1)], unique=True)
        #TODO: Map-reduce collection
        map = mark_safe(u'''
              function(){
                 var year = this.call_date.getFullYear();
                 var month = this.call_date.getMonth();
                 var day = this.call_date.getDate();
                 var hours = this.call_date.getHours();
                 var minutes = this.call_date.getMinutes();
                 var d = new Date(year, month, day, hours, minutes);
                 emit( {
                        g_Millisec: d.getTime(),
                       },
                       {numbercall__max: this.numbercall, call_date: this.call_date,
                        switch_id: this.switch_id, accountcode: this.accountcode } )
              }''')


        reduce = mark_safe(u'''
                 function(key,vals) {
                     var ret = {numbercall__max: 0, call_date: '',
                                switch_id: 0, accountcode: ''};
                     max = vals[0].numbercall__max;

                     for (var i=0; i < vals.length; i++){

                        if(vals[i].numbercall__max > max){
                            max = parseInt(vals[i].numbercall__max);
                        };
                     }
                     ret.numbercall__max = max;
                     ret.call_date = vals[0].call_date;
                     ret.switch_id = vals[0].switch_id;
                     ret.accountcode = vals[0].accountcode;
                     return ret;
                 }
                 ''')

        cdr_conn_call = settings.DB_CONNECTION[settings.CDR_MONGO_CONC_CALL]

        cdr_conn_call.map_reduce(map, reduce, out=settings.CDR_MONGO_CONC_CALL_AGG)