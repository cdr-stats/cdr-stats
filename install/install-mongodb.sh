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
#
# cd /usr/src/ ; rm install-mongodb.sh ; wget --no-check-certificate https://raw.github.com/Star2Billing/cdr-stats/master/install/install-mongodb.sh ; chmod +x install-mongodb.sh ; ./install-mongodb.sh


DATETIME=$(date +"%Y%m%d%H%M%S")
KERNELARCH=$(uname -p)



func_identify_os() {
    # Identify Linux Distribution type
    if [ -f /etc/debian_version ] ; then
        DIST='DEBIAN'
        if [ "$(lsb_release -cs)" != "lucid" ] || [ "$(lsb_release -cs)" != "precise" ]; then
		    echo "This script is only intended to run on Ubuntu LTS 10.04 / 12.04 or CentOS 6.2"
		    exit 255
	    fi
    elif [ -f /etc/redhat-release ] ; then
        DIST='CENTOS'
        if [ "$(awk '{print $3}' /etc/redhat-release)" != "6.2" ] ; then
        	echo "This script is only intended to run on Ubuntu LTS 10.04 or CentOS 6.2"
        	exit 255
        fi
    else
        echo ""
        echo "This script is only intended to run on Ubuntu LTS 10.04 or CentOS 6.2"
        echo ""
        exit 1
    fi
}


#function to install mongoDB
func_install_mongodb() {
    echo ""
    echo ""
    echo "We will now install MongoDB on your server"
	echo "============================================"
    echo ""
    case $DIST in
        'DEBIAN')
            #Install mongodb on Debian
            apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10
            echo '
#MongoDB
deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' >> /etc/apt/sources.list
            apt-get update 
            apt-get install mongodb-10gen
            cd /etc/init.d/
            update-rc.d -f mongodb defaults
        ;;
        'CENTOS')
            #Install mongodb on CentOS
            if [ $KERNELARCH = "x86_64" ]; then
	            echo '
[10gen]
name=10gen Repository
baseurl=http://downloads-distro.mongodb.org/repo/redhat/os/x86_64
gpgcheck=0' > /etc/yum.repos.d/10gen-mongodb.repo
        	else
	            echo '
[10gen]
name=10gen Repository
baseurl=http://downloads-distro.mongodb.org/repo/redhat/os/i686
gpgcheck=0' > /etc/yum.repos.d/10gen-mongodb.repo
        	fi
            yum install mongo-10gen mongo-10gen-server
            chkconfig --add mongodb
            chkconfig --levels 235 mongodb on
        ;;
    esac
    
    sed -i "s/#port = 27017/port = 27017/g" /etc/mongodb.conf
    /etc/init.d/mongodb restart
}


#Identify the OS
func_identify_os

func_install_mongodb



echo ""
echo ""
echo "**************************************************************"
echo "Congratulations, MongoDB is now installed!"
echo "**************************************************************"
echo ""
echo ""
