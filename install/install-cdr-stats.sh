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

#
# To download and run the script on your server :
#
# cd /usr/src/ ; wget --no-check-certificate https://raw.github.com/Star2Billing/cdr-stats/master/install/install-cdr-stats.sh -O install-cdr-stats.sh ; bash install-cdr-stats.sh
#
# Install develop branch
# cd /usr/src/ ; wget --no-check-certificate https://raw.github.com/Star2Billing/cdr-stats/develop/install/install-cdr-stats.sh -O install-cdr-stats.sh ; sed -i "s/cdr-stats\/master/cdr-stats\/develop/g" install-cdr-stats.sh ; bash install-cdr-stats.sh
#

BRANCH='master'
INSTALLMODE='FULL' # Set to FULL to update Selinux / Firewall / etc...


#Get Scripts dependencies
cd /usr/src/
wget --no-check-certificate https://raw.github.com/Star2Billing/cdr-stats/$BRANCH/install/bash-common-functions.sh -O bash-common-functions.sh
wget --no-check-certificate https://raw.github.com/Star2Billing/cdr-stats/$BRANCH/install/cdr-stats-functions.sh -O cdr-stats-functions.sh


#Menu Section for Script
show_menu_switch() {
    clear
    echo " > Do you want to install CDR-Stats for FreeSWITCH or Asterisk ?"
    echo "================================================================"
    echo "  1)  FreeSWITCH"
    echo "  2)  Asterisk"
    echo -n "(1-2) : "
    read OPTION < /dev/tty
}


ExitFinish=0
while [ $ExitFinish -eq 0 ]; do
    show_menu_switch
    case $OPTION in
    1)
        INSTALL_TYPE='FREESWITCH'
        echo "We will make some pre-configuration on CDR-Stats for FreeSWITCH..."
        ExitFinish=1
    ;;
    2)
        INSTALL_TYPE='ASTERISK'
        echo "We will make some pre-configuration on CDR-Stats for Asterisk..."
        ExitFinish=1
    ;;
    *)
    esac
done


#Include general functions
source bash-common-functions.sh

#Include cdr-stats install functions
source cdr-stats-functions.sh

#Identify the OS
func_identify_os

#Request the user to accept the license
func_accept_license

#run install menu
run_menu_cdr_stats_install




# Clean the system on MySQL
#==========================
# deactivate ; rm -rf /usr/share/cdr-stats ; rm -rf /var/log/cdr-stats ; rmvirtualenv cdr-stats ; rm -rf /etc/init.d/cdr-stats-celer* ; rm -rf /etc/default/cdr-stats-celeryd ; rm /etc/apache2/sites-enabled/cdr-stats.conf ; mysqladmin drop cdr-stats --password=password

# Create Database on MySQL
#=========================
# mysqladmin drop cdr-stats --password=password
# mysqladmin create cdr-stats --password=password
