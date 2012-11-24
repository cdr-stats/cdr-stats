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
from celery.task import PeriodicTask
from cdr.import_cdr_freeswitch_mongodb import import_cdr_freeswitch_mongodb
from cdr.import_cdr_asterisk import import_cdr_asterisk
from cdr.aggregate import set_concurrentcall_analytic
from django.core.cache import cache
from cdr.models import Switch
from common.only_one_task import only_one
from datetime import datetime, timedelta
import sqlite3
import asterisk.manager

#Note: if you import a lot of CDRs the first time you can have an issue here
#we need to make sure the user import their CDR before starting Celery
#for now we will increase the lock limit to 1 hours
LOCK_EXPIRE = 60 * 60 * 1  # Lock expires in 1 hours


class sync_cdr_pending(PeriodicTask):
    """
    A periodic task that checks for pending CDR to import
    """
    run_every = timedelta(seconds=10)  # every 10 secs

    @only_one(key="sync_cdr_pending", timeout=LOCK_EXPIRE)
    def run(self, **kwargs):
        logger = self.get_logger()
        logger.info('TASK :: sync_cdr_pending')

        if settings.CDR_BACKEND[settings.LOCAL_SWITCH_IP]['cdr_type'] == 'asterisk':
            # Import from Asterisk
            import_cdr_asterisk()

        elif settings.CDR_BACKEND[settings.LOCAL_SWITCH_IP]['cdr_type'] == 'freeswitch':
            # Import from Freeswitch Mongo
            import_cdr_freeswitch_mongodb()

        return True


class get_channels_info(PeriodicTask):
    """
    A periodic task to retrieve channels info
    """
    run_every = timedelta(seconds=1)  # every minute - 60 seconds

    @only_one(key="get_channels_info", timeout=LOCK_EXPIRE)
    def run(self, **kwargs):

        logger = self.get_logger()
        logger.info('TASK :: get_channels_info')
        totalcall = 0

        # Get calldate
        now = datetime.today()
        date_now = datetime(now.year, now.month, now.day,
                            now.hour, now.minute, now.second, 0)
        #key_date / minute precision
        key_date = "%d-%d-%d-%d-%d" % (now.year, now.month, now.day, now.hour, now.minute)

        # Retrieve SwitchID
        try:
            switch = Switch.objects.get(ipaddress=settings.LOCAL_SWITCH_IP)
            switch_id = switch.id
        except:
            logger.error("Cannot retrieve Switch %s" % settings.LOCAL_SWITCH_IP)
            return False

        if settings.CDR_BACKEND[settings.LOCAL_SWITCH_IP]['cdr_type'] == 'freeswitch':
            con = False
            try:
                con = sqlite3.connect('/usr/local/freeswitch/db/core.db')
                cur = con.cursor()
                cur.execute('SELECT accountcode, count(*) FROM channels')
                rows = cur.fetchall()
                for row in rows:
                    if not row[0]:
                        accountcode = ''
                    else:
                        accountcode = row[0]
                    numbercall = row[1]
                    totalcall = totalcall + numbercall
                    logger.debug('%s (accountcode:%s, switch_id:%d) ==> %s'
                            % (date_now, accountcode, switch_id,
                               str(numbercall)))

                    call_json = {
                        'switch_id': switch_id,
                        'call_date': date_now,
                        'numbercall': numbercall,
                        'accountcode': accountcode,
                    }
                    settings.DBCON[settings.MONGO_CDRSTATS['CONC_CALL']].insert(call_json)

                    #Save to Redis cache
                    key = "%s-%d-%s" % (key_date, switch_id, str(accountcode))
                    cache.set(key, numbercall, 1800)  # 30 minutes
                    #Create collection for Analytics
                    set_concurrentcall_analytic(date_now, switch_id, accountcode, numbercall)

            except sqlite3.Error, e:
                logger.error('Error %s:' % e.args[0])
            finally:
                if con:
                    con.close()
        elif settings.CDR_BACKEND[settings.LOCAL_SWITCH_IP]['cdr_type'] == 'asterisk':
            manager = asterisk.manager.Manager()
            listaccount = {}
            try:
                # connect to the manager
                try:
                    manager.connect(settings.ASTERISK_MANAGER_HOST)
                    manager.login(settings.ASTERISK_MANAGER_USER, settings.ASTERISK_MANAGER_SECRET)

                    # get list of channels
                    response = manager.command('core show channels concise')
                    # response.data = "SIP/areski-00000006!a2billing-echotest!34902800102*!2!Ring!Echo!!34650784355!4267877355!!3!35!(None)!1352663344.6\n"
                    # response.data += "SIP/areski-00000006!a2billing-echotest!34902800102*!2!Ring!Echo!!34650784355!!!3!35!(None)!1352663344.6\n"
                    # response.data += "SIP/areski-00000006!a2billing-echotest!34902800102*!2!Ring!Echo!!34650784355!!!3!35!(None)!1352663344.6\n"
                    # response.data += "SIP/areski-00000006!a2billing-echotest!34902800102*!2!Ring!Echo!!34650784355!12346!!3!35!(None)!1352663344.6\n"
                    # response.data += "SIP/areski-00000006!a2billing-echotest!34902800102*!2!Ring!Echo!!34650784355!!!3!35!(None)!1352663344.6\n"

                    if response.data:
                        lines = response.data.split('\n')
                        for line in lines:
                            col = line.split('!')
                            if col and len(col) >= 8:
                                if col[8] in listaccount:
                                    listaccount[col[8]] = listaccount[col[8]] + 1
                                else:
                                    listaccount[col[8]] = 1
                    #manager.logoff()
                except asterisk.manager.ManagerSocketException, (errno, reason):
                    logger.error("Error connecting to the manager: %s" % reason)
                    return False
                except asterisk.manager.ManagerAuthException, reason:
                    logger.error("Error logging in to the manager: %s" % reason)
                    return False
                except asterisk.manager.ManagerException, reason:
                    logger.error("Error: %s" % reason)
                    return False
            finally:
                try:
                    manager.close()
                except:
                    logger.error("Manager didn't close")

            for accountcode in listaccount:
                numbercall = listaccount[accountcode]
                totalcall = totalcall + numbercall
                logger.debug('%s (accountcode:%s, switch_id:%d) ==> %s'
                            % (date_now, accountcode, switch_id,
                               str(numbercall)))
                call_json = {
                    'switch_id': switch_id,
                    'call_date': date_now,
                    'numbercall': numbercall,
                    'accountcode': accountcode,
                }
                settings.DBCON[settings.MONGO_CDRSTATS['CONC_CALL']].insert(call_json)
                #Save to Redis cache
                key = "%s-%d-%s" % (key_date, switch_id, str(accountcode))
                cache.set(key, numbercall, 1800)  # 30 minutes
                #Create collection for Analytics
                set_concurrentcall_analytic(date_now, switch_id, accountcode, numbercall)

        #For any switches

        #There is no calls
        if totalcall == 0:
            accountcode = ''
            numbercall = 0
            call_json = {
                'switch_id': switch_id,
                'call_date': date_now,
                'numbercall': numbercall,
                'accountcode': accountcode,
            }
            settings.DBCON[settings.MONGO_CDRSTATS['CONC_CALL']].insert(call_json)
            key = "%s-%d-%s" % (key_date, switch_id, str(accountcode))
            cache.set(key, numbercall, 1800)  # 30 minutes
            set_concurrentcall_analytic(date_now, switch_id, accountcode, numbercall)

        key = "%s-%d-root" % (key_date, switch_id)
        logger.info("key:%s, totalcall:%d" % (key, totalcall))
        cache.set(key, totalcall, 1800)  # 30 minutes

        return True
