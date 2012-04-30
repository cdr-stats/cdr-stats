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
# cd /usr/src/ ; rm install-all.sh ; wget --no-check-certificate https://raw.github.com/Star2Billing/cdr-stats/master/install/install-all.sh ; chmod +x install-all.sh ; ./install-all.sh
#


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

#Identify the OS
func_identify_os

echo ""
echo ""
echo "> > > This is only to be installed on a fresh new installation of CentOS 6.2 or Ubuntu LTS 10.04! < < <"
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
        if [ ! -f /etc/yum.repos.d/rpmforge.repo ];
       	then
			# Install RPMFORGE Repo
            #Check architecture
        	KERNELARCH=$(uname -p)
        	if [ $KERNELARCH = "x86_64" ]; then
				rpm -ivh http://pkgs.repoforge.org/rpmforge-release/rpmforge-release-0.5.2-2.el6.rf.x86_64.rpm
			else
				rpm -ivh http://pkgs.repoforge.org/rpmforge-release/rpmforge-release-0.5.2-2.el6.rf.i686.rpm
			fi
        fi
        yum -y update
        yum -y install mlocate vim git-core
        yum -y install policycoreutils-python
        yum -y --enablerepo=rpmforge install sox sox-devel ffmpeg ffmpeg-devel mpg123 mpg123-devel libmad libmad-devel libid3tag libid3tag-devel lame lame-devel flac-devel libvorbis-devel
        yum -y groupinstall 'Development Tools'
        cd /usr/src/
        wget http://switch.dl.sourceforge.net/project/sox/sox/14.3.2/sox-14.3.2.tar.gz
        tar zxfv sox*
        rm -rf sox*.tar.gz
        mv sox* sox
        cd /usr/src/sox
        make distclean
        make clean
        ./configure --bindir=/usr/bin/
        make -s
        make install
    ;;
esac


#Install MongoDB
cd /usr/src/
wget https://raw.github.com/Star2Billing/cdr-stats/master/install/install-mongodb.sh
bash install-mongodb.sh


#Install Freeswitch
cd /usr/src/
wget https://raw.github.com/Star2Billing/cdr-stats/master/install/install-freeswitch.sh
bash install-freeswitch.sh
/etc/init.d/freeswitch start


#Install CDR-Stats
cd /usr/src/
wget https://raw.github.com/Star2Billing/cdr-stats/master/install/install-cdr-stats.sh
bash install-cdr-stats.sh


