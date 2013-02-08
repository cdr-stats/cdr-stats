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
# cd /usr/src/ ; wget --no-check-certificate https://raw.github.com/Star2Billing/cdr-stats/master/install/install-all-cdr-stats-freeswitch.sh -O install-all-cdr-stats-freeswitch.sh; bash install-all-cdr-stats-freeswitch.sh
#

BRANCH='master'

#INSTALL TYPE (ASTERISK or FREESWITCH)
INSTALL_TYPE='FREESWITCH'

INSTALLMODE='FULL' # Set to FULL to update Selinux / Firewall / etc...
KERNELARCH=$(uname -p)

#Get Scripts dependencies
cd /usr/src/
wget --no-check-certificate https://raw.github.com/Star2Billing/cdr-stats/$BRANCH/install/bash-common-functions.sh -O bash-common-functions.sh
wget --no-check-certificate https://raw.github.com/Star2Billing/cdr-stats/$BRANCH/install/cdr-stats-functions.sh -O cdr-stats-functions.sh

#Include general functions
source bash-common-functions.sh

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
        if [ ! -f /etc/yum.repos.d/rpmforge.repo ];
       	then
			#Install RPMFORGE Repo
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
wget --no-check-certificate https://raw.github.com/Star2Billing/cdr-stats/$BRANCH/install/install-mongodb.sh -O install-mongodb.sh
bash install-mongodb.sh


#Install Freeswitch
cd /usr/src/
wget --no-check-certificate https://raw.github.com/Star2Billing/cdr-stats/$BRANCH/install/install-freeswitch.sh -O install-freeswitch.sh
bash install-freeswitch.sh
/etc/init.d/freeswitch start

#Install CDR-Stats
cd /usr/src/
wget --no-check-certificate https://raw.github.com/Star2Billing/cdr-stats/$BRANCH/install/bash-common-functions.sh -O bash-common-functions.sh
wget --no-check-certificate https://raw.github.com/Star2Billing/cdr-stats/$BRANCH/install/cdr-stats-functions.sh -O cdr-stats-functions.sh


#Include general functions
source bash-common-functions.sh
source cdr-stats-functions.sh


#Identify the OS
func_identify_os

#Request the user to accept the license
func_accept_license_mplv2

#Install Landing page
func_install_landing_page

#Run install menu
run_menu_cdr_stats_install
