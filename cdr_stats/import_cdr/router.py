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


"""
We implemented a router cause django-import-export doesn't have a mechanism
to specify the database with `using`
https://github.com/django-import-export/django-import-export
"""


class CDRImportRouter(object):
    """
    A router to control all database operations on models.
    """
    def db_for_read(self, model, **hints):
        """
        Attempts to read auth models go to import_cdr.
        """
        if model._meta.app_label == 'import_cdr':
            return 'import_cdr'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write auth models go to import_cdr.
        """
        if model._meta.app_label == 'import_cdr':
            return 'import_cdr'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the import_cdr app is involved.
        """
        if obj1._meta.app_label == 'import_cdr' or \
           obj2._meta.app_label == 'import_cdr':
            return True
        return None

    def allow_migrate(self, db, app_label, model=None, **hints):
        """
        Make sure the auth app only appears in the 'import_cdr'
        database.
        """
        if app_label == 'import_cdr':
            return db == 'import_cdr'
        return None
