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
# cd /usr/src/ ; rm install-cdr-stats-freepbx.sh ; wget --no-check-certificate https://raw.github.com/Star2Billing/cdr-stats/master/install/install-cdr-stats-freepbx.sh ; chmod +x install-cdr-stats-freepbx.sh ; ./install-cdr-stats-freepbx.sh
#

INSTALL_DIR='/usr/share/cdr_stats'
DATABASENAME=""
MYSQLUSER=""
MYSQLPASSWORD=""
MYHOST=""
MYHOSTPORT=""

#Include general functions
source bash-common-functions.sh


#Identify the OS
func_identify_os


echo ""
echo ""
echo "> > > This is only to be installed on a fresh new installation of CentOS 6.2 or Ubuntu LTS 10.04 / 12.04! < < <"
echo ""
echo "It will install CDR-Stats on your server"
echo "Press Enter to continue or CTRL-C to exit"
echo ""
read TEMP


case $DIST in
    'DEBIAN') 
        apt-get -y update
        apt-get -y install vim git-core
    ;;
    'CENTOS')
        yum -y update
        yum -y install mlocate vim git-core
        yum -y install policycoreutils-python
    ;;
esac



until mysql -u$MYSQLUSER -p$MYSQLPASSWORD -P$MYHOSTPORT -h$MYHOST $DATABASENAME -e ";" ; do 
    clear 
    echo "Enter correct database settings"
    func_get_mysql_database_setting
done

#Update Mysql schema
echo "We will now add a Primary Key to your CDR database"
echo "We advice you to first backup your database prior continuing"
echo ""
echo "Press Enter to continue or CTRL-C to exit"
mysql -u$MYSQLUSER -p$MYSQLPASSWORD -P$MYHOSTPORT -h$MYHOST $DATABASENAME -e "ALTER TABLE  cdr ADD acctid BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST;;"


#Install CDR-Stats
cd /usr/src/
wget https://raw.github.com/Star2Billing/cdr-stats/master/install/install-cdr-stats.sh
bash install-cdr-stats.sh


#enable CDR-Stats for Asterisk
sed -i "s/freeswitch/asterisk/g"  $INSTALL_DIR/settings_local.py

#Restart Apache
case $DIST in
    'DEBIAN')
        service apache2 restart
    ;;
    'CENTOS')
        service httpd restart
    ;;
esac

#Restart backend services
/etc/init.d/cdr-stats-celeryd restart
/etc/init.d/cdr-stats-socketio restart


