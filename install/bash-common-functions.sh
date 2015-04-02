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

DATETIME=$(date +"%Y%m%d%H%M%S")
KERNELARCH=$(uname -p)
SCRIPT_NOTICE="This install script is only intended to run on Debian 7.X"


# Identify Linux Distribution type
func_identify_os() {
    if [ -f /etc/debian_version ] ; then
        DIST='DEBIAN'
        if [ "$(lsb_release -cs)" != "wheezy" ]; then
            echo $SCRIPT_NOTICE
            exit 255
        fi
    elif [ -f /etc/redhat-release ] ; then
        DIST='CENTOS'
        if [ "$(awk '{print $3}' /etc/redhat-release)" != "6.2" ] && [ "$(awk '{print $3}' /etc/redhat-release)" != "6.3" ] && [ "$(awk '{print $3}' /etc/redhat-release)" != "6.4" ] && [ "$(awk '{print $3}' /etc/redhat-release)" != "6.5" ]; then
            echo $SCRIPT_NOTICE
            exit 255
        fi
    else
        echo $SCRIPT_NOTICE
        exit 1
    fi
}



#Function mysql db setting
func_get_mysql_database_setting() {
    if mysql -u$MYSQLUSER -p$MYSQLPASSWORD -P$MYHOSTPORT -h$MYHOST $DATABASENAME -e ";" ; then
        #Database settings correct
        echo "Mysql settings correct!"
    else

        echo ""
        echo "Configure Mysql Settings..."
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
        echo "Enter Database name (default:cdrstats)"
        read DATABASENAME
        if [ -z "$DATABASENAME" ]; then
            DATABASENAME="cdrstats"
        fi
    fi
}


#Function mysql db setting
func_get_mysql_database_setting_asteriskcdrdb() {
    if mysql -u$MYSQLUSER -p$MYSQLPASSWORD -P$MYHOSTPORT -h$MYHOST $DATABASENAME -e ";" ; then
        #Database settings correct
        echo "Mysql settings correct!"
    else

        echo ""
        echo "Configure Mysql Settings to connect to the Asterisk CDR database..."
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
    fi
}


#Function accept license
func_accept_license() {
    echo ""
    echo ""
    echo "CDR-Stats License MPL V2.0 (branch:$BRANCH)"
    echo "Further information at http://www.cdr-stats.org/support/licensing/"
    echo ""
    echo "This Source Code Form is subject to the terms of the Mozilla Public"
    echo "License, v. 2.0. If a copy of the MPL was not distributed with this file,"
    echo "You can obtain one at http://mozilla.org/MPL/2.0/."
    echo ""
    echo "Copyright (C) 2011-2015 Star2Billing S.L."
    echo ""
}

