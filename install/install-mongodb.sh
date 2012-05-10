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
# cd /usr/src/ ; rm install-mongodb.sh ; rm bash-common-functions.sh ; wget --no-check-certificate https://raw.github.com/Star2Billing/cdr-stats/master/install/bash-common-functions.sh ; wget --no-check-certificate https://raw.github.com/Star2Billing/cdr-stats/master/install/install-mongodb.sh ; chmod +x install-mongodb.sh ; ./install-mongodb.sh


#Include general functions
source bash-common-functions.sh


#function to install mongoDB
func_install_mongodb() {

    if which mongo >/dev/null; then
        echo ""
        echo "MongoDB is already installed!"
        echo ""
        echo ""
        
    else
        #Identify the OS
        func_identify_os

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
                apt-get -y install mongodb-10gen
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
                yum -y install mongo-10gen mongo-10gen-server
                chkconfig --add mongodb
                chkconfig --levels 235 mongodb on
            ;;
        esac
        
        sed -i "s/#port = 27017/port = 27017/g" /etc/mongodb.conf
        /etc/init.d/mongodb restart
        

        echo ""
        echo ""
        echo "**************************************************************"
        echo "Congratulations, MongoDB is now installed!"
        echo "**************************************************************"
        echo ""
        echo ""
    fi
}


#Install Mongo
func_install_mongodb


