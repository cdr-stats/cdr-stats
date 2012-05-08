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
# cd /usr/src/ ; rm install-all.sh ; wget --no-check-certificate https://raw.github.com/Star2Billing/cdr-stats/master/install/install-cdr-stats-freepbx.sh ; chmod +x install-all.sh ; ./install-all.sh
#

INSTALL_DIR='/usr/share/cdr_stats'
DATABASENAME=""
MYSQLUSER=""
MYSQLPASSWORD=""
MYHOST=""
MYHOSTPORT=""

func_identify_os() {
    # Identify Linux Distribution type
    if [ -f /etc/debian_version ] ; then
        DIST='DEBIAN'
        if [ "$(lsb_release -cs)" != "lucid" ] && [ "$(lsb_release -cs)" != "precise" ]; then
		    echo "This script is only intended to run on Ubuntu LTS 10.04 / 12.04 or CentOS 6.2"
		    exit 255
	    fi
    elif [ -f /etc/redhat-release ] ; then
        DIST='CENTOS'
        if [ "$(awk '{print $3}' /etc/redhat-release)" != "6.2" ] ; then
        	echo "This script is only intended to run on Ubuntu LTS 10.04 / 12.04 or CentOS 6.2"
        	exit 255
        fi
    else
        echo ""
        echo "This script is only intended to run on Ubuntu LTS 10.04 / 12.04 or CentOS 6.2"
        echo ""
        exit 1
    fi
}

#Function mysql db setting
func_mysql_database_setting() {
    echo ""
    echo "Provide the MySQL settings to access to current CDR Database..."
    echo ""
    
    echo "Enter Mysql hostname (default:localhost)"
    read MYHOST
    if [ -z "$MYHOST" ]; then
        MYHOST="localhost"
    fi
    echo "Enter Mysql port (default:3306)"
    read MYHOSTPORT
    if [ -z "$MYHOSTPORT" ]; then
        MYHOSTPORT="3306"
    fi
    echo "Enter Mysql Username (default:root)"
    read MYSQLUSER
    if [ -z "$MYSQLUSER" ]; then
        MYSQLUSER="root"
    fi
    echo "Enter Mysql Password (default:password)"
    read MYSQLPASSWORD
    if [ -z "$MYSQLPASSWORD" ]; then
        MYSQLPASSWORD="password"
    fi
    echo "Enter Database name (default:asteriskcdrdb)"
    read DATABASENAME
    if [ -z "$DATABASENAME" ]; then
        DATABASENAME="asteriskcdrdb"
    fi
}

#Identify the OS
func_identify_os

echo ""
echo ""
echo "> > > This is only to be installed on a fresh new installation of CentOS 6.2 or Ubuntu LTS 10.04 / 12.04! < < <"
echo ""
echo "It will install Freeswitch, CDR-Stats on your server"
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

mysql -uroot -ppassw0rd -P3306 -hlocalhost -e ";"

until mysql -u$MYSQLUSER -p$MYSQLPASSWORD -P$MYHOSTPORT -h$MYHOST $DATABASENAME -e ";" ; do 
	clear 
	echo "Enter correct database settings"
	func_mysql_database_setting
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


