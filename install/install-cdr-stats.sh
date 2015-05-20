#!/bin/bash
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

#
# To download and run the script on your server :
#
# cd /usr/src/ ; rm install-cdr-stats.sh ; wget --no-check-certificate https://raw.github.com/areski/cdr-stats/master/install/install-cdr-stats.sh -O install-cdr-stats.sh ; bash install-cdr-stats.sh
#
# Install develop branch
# cd /usr/src/ ; rm install-cdr-stats.sh ; wget --no-check-certificate https://raw.github.com/areski/cdr-stats/develop/install/install-cdr-stats.sh -O install-cdr-stats.sh ; bash install-cdr-stats.sh
#

BRANCH='master'

#Get Scripts dependencies
cd /usr/src/
rm cdr-stats-functions.sh
wget --no-check-certificate https://raw.github.com/areski/cdr-stats/$BRANCH/install/cdr-stats-functions.sh -O cdr-stats-functions.sh

#Include cdr-stats install functions
source cdr-stats-functions.sh


#Identify the OS
func_identify_os

#Request the user to accept the license
func_accept_license


echo "========================================================================="
echo ""
echo "CDR-Stats installation will start now!"
echo ""
echo "Press Enter to continue or CTRL-C to exit"
echo ""
read INPUT

func_install_frontend
func_install_landing_page
func_install_backend

clear
echo ""
echo "Congratulations, CDR-Stats is now installed!"
echo "--------------------------------------------"
echo ""
echo "Please log on to CDR-Stats at "
echo "http://$IPADDR:$HTTP_PORT"
echo "the username and password are the ones you entered during this installation."
echo ""
echo "Thank you for installing CDR-Stats"
echo "Yours,"
echo "The Star2Billing Team"
echo "http://www.star2billing.com and http://www.cdr-stats.org/"
echo ""
echo "========================================================================="
echo ""


# #Menu Section for Script
# show_menu_cdr_stats() {
#     clear
#     echo " > CDR-Stats Installation Menu"
#     echo "====================================="
#     echo "  1)  Install All"
#     echo "  2)  Install CDR-Stats Web Frontend"
#     echo "  3)  Install CDR-Stats Backend"
#     echo "  0)  Quit"
#     echo -n "(0-2) : "
#     read OPTION < /dev/tty
# }


# run_menu_cdr_stats_install() {
#     ExitFinish=0
#     while [ $ExitFinish -eq 0 ]; do
#         # Show menu with Installation items
#         show_menu_cdr_stats
#         case $OPTION in
#             1)
#                 func_install_frontend
#                 func_install_backend
#                 echo done
#             ;;
#             2)
#                 func_install_frontend
#             ;;
#             3)
#                 func_install_backend
#             ;;
#             0)
#                 ExitFinish=1
#             ;;
#             *)
#         esac
#     done
# }
#
# #run install menu
# run_menu_cdr_stats_install


# Clean the system on MySQL
#==========================
# deactivate ; rm -rf /usr/share/cdrstats ; rm -rf /var/log/cdr-stats ; rmvirtualenv cdr-stats ; rm -rf /etc/init.d/cdr-stats-celer* ; rm -rf /etc/default/cdr-stats-celeryd ; rm /etc/apache2/sites-enabled/cdr-stats.conf ; mysqladmin drop cdr-stats --password=password

# Create Database on MySQL
#=========================
# mysqladmin drop cdr-stats --password=password
# mysqladmin create cdr-stats --password=password
