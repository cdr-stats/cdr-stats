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
from common.only_one_task import only_one
from datetime import datetime, timedelta
import sqlite3


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

        if settings.LOCAL_SWITCH_TYPE == 'asterisk':
            # Import from Asterisk
            import_cdr_asterisk()

        elif settings.LOCAL_SWITCH_TYPE == 'freeswitch':
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

        if settings.LOCAL_SWITCH_TYPE == 'freeswitch':
            logger = self.get_logger()
            logger.info('TASK :: get_channels_info')

            # Get calldate
            now = datetime.today()
            date_now = datetime(
                now.year,
                now.month,
                now.day,
                now.hour,
                now.minute,
                now.second,
                0,
                )

            # Retrieve SwitchID
            switch_id = settings.LOCAL_SWITCH_ID
            if settings.LOCAL_SWITCH_TYPE == 'freeswitch':
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
                        number_call = row[1]
                        logger.debug('%s (accountcode:%s, switch_id:%d) ==> %s'
                                 % (date_now, accountcode, switch_id,
                                str(number_call)))

                        call_json = {
                            'switch_id': switch_id,
                            'call_date': date_now,
                            'numbercall': number_call,
                            'accountcode': accountcode,
                            }
                        settings.DBCON[settings.MG_CONC_CALL].insert(call_json)
                except sqlite3.Error, e:

                    logger.error('Error %s:' % e.args[0])
                finally:
                    if con:
                        con.close()
            elif settings.LOCAL_SWITCH_TYPE == 'asterisk':

                # TODO: Implement concurrent calls in Asterisk
                print 'Asterisk needs to be implemented'

            return True
