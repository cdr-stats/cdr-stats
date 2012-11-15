#
# Newfies-Dialer License
# http://www.newfies-dialer.org
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


#IMPORT SETTINGS
#===============
from settings import *

SOUTH_TESTS_MIGRATE = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

#Celery test
BROKER_BACKEND = "memory"
CELERY_ALWAYS_EAGER = True


#LOGGING
#=======
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
}

INSTALLED_APPS += ('django_nose', )
TEST_RUNNER = 'django_nose.run_tests'
