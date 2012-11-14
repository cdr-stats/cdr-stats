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
    A periodic task that checks for pending calls to import
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

        # Get calldate
        now = datetime.today()
        date_now = datetime(now.year, now.month, now.day,
                            now.hour, now.minute, now.second, 0)

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
                    if response.data:
                        lines = response.data.split('\n')
                        for line in lines:
                            col = line.split('!')
                            if col and len(col) >= 8:
                                if col[8] in listaccount:
                                    listaccount[col[8]] = listaccount[col[8]] + 1
                                else:
                                    listaccount[col[8]] = 1
                    manager.logoff()
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

            for account in listaccount:
                numbercall = listaccount[account]
                logger.debug('%s (accountcode:%s, switch_id:%d) ==> %s'
                            % (date_now, account, switch_id,
                               str(numbercall)))
                call_json = {
                    'switch_id': switch_id,
                    'call_date': date_now,
                    'numbercall': numbercall,
                    'accountcode': account,
                }
                settings.DBCON[settings.MONGO_CDRSTATS['CONC_CALL']].insert(call_json)

                #Create collection for Analytics
                set_concurrentcall_analytic(date_now, switch_id, accountcode, numbercall)

        return True
