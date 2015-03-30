#!/bin/bash
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

#
# To download and run the script on your server :
# cd /usr/src/ ; rm install-cdr-stats-asterisk.sh ; wget --no-check-certificate https://raw.github.com/Star2Billing/cdr-stats/master/install/install-cdr-stats-asterisk.sh -O install-cdr-stats-asterisk.sh; bash install-cdr-stats-asterisk.sh
#

USER=$(sed -rn 's/.*:([^/]+).*/\1/p' <<<$(git remote -v))
[ -z $USER ] && USER=Star2Billing
BRANCH='master'
INSTALL_DIR='/usr/share/cdr_stats'

#INSTALL TYPE (ASTERISK or FREESWITCH)
INSTALL_TYPE='ASTERISK'

INSTALLMODE='GENTLE' # Set to FULL to update Selinux, Firewall, etc if not Set to GENTLE

echo ""
echo "> > > This is only to be installed on a fresh new installation of CentOS 6.2 or Ubuntu LTS 10.04 / 12.04! < < <"
echo ""
echo "It will install CDR-Stats on your server"
echo "Press Enter to continue or CTRL-C to exit"
echo ""
read TEMP


#Get Scripts dependencies
cd /usr/src/
wget --no-check-certificate https://raw.github.com/$USER/cdr-stats/$BRANCH/install/bash-common-functions.sh -O bash-common-functions.sh
wget --no-check-certificate https://raw.github.com/$USER/cdr-stats/$BRANCH/install/cdr-stats-functions.sh -O cdr-stats-functions.sh

#Include general functions
source bash-common-functions.sh

source cdr-stats-functions.sh

#Identify the OS
func_identify_os

#Request the user to accept the license
func_accept_license_mplv2

#Install Stanalone backend
func_install_standalone_backend
