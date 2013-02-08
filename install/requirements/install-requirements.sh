#!/bin/bash
#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2013 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

echo "Install basic requirements..."
for line in $(cat install/requirements/basic-requirements.txt | grep -v \#)
do
    pip install $line --use-mirrors
done

echo "Install Django requirements..."
for line in $(cat install/requirements/django-requirements.txt | grep -v \#)
do
    pip install $line --use-mirrors
done

echo "Install Dev requirements..."
for line in $(cat install/requirements/dev-requirements.txt | grep -v \#)
do
    pip install $line
done

echo "Install test requirements..."
for line in $(cat install/requirements/test-requirements.txt | grep -v \#)
do
    pip install $line --use-mirrors
done
