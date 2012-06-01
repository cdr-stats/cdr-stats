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

from django.core.cache import cache


def single_instance_task(key, timeout):
    """
    Decorator function to add a semafor on task
    it helps to ensure tasks aren't run more than once at the same time
    """

    def task_exc(func):

        def wrapper(*args, **kwargs):
            lock_id = 'celery-single-instance-' + key
            acquire_lock = lambda: cache.add(lock_id, 'true', timeout)
            release_lock = lambda: cache.delete(lock_id)
            if acquire_lock():
                try:
                    func(*args, **kwargs)
                finally:
                    release_lock()

        return wrapper

    return task_exc
