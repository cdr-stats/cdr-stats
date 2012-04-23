#!/bin/bash
#
# Newfies-Dialer License
# http://www.newfies-dialer.org
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
# cd /usr/src/ ; rm install-all.sh ; wget --no-check-certificate https://raw.github.com/Star2Billing/newfies-dialer/master/install/install-all.sh ; chmod +x install-all.sh ; ./install-all.sh
#


func_identify_os() {
    # Identify Linux Distribution type
    if [ -f /etc/debian_version ] ; then
        DIST='DEBIAN'
        if [ "$(lsb_release -cs)" != "lucid" ] ; then
		    echo "This script is only intended to run on Ubuntu LTS 10.04 or CentOS 6.2"
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
echo "It will install Freeswitch, Plivo & Newfies on your server"
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



#Install Freeswitch
cd /usr/src/
wget https://raw.github.com/Star2Billing/newfies-dialer/master/install/install-freeswitch.sh
bash install-freeswitch.sh
/etc/init.d/freeswitch start


#Install Plivo
cd /usr/src/
wget https://raw.github.com/plivo/plivo/master/scripts/plivo_install.sh
bash plivo_install.sh /usr/share/plivo

#UPDATE Plivo configuration
awk 'NR==12{print "EXTRA_FS_VARS = variable_user_context,Channel-Read-Codec-Bit-Rate,variable_plivo_answer_url,variable_plivo_app,variable_direction,variable_endpoint_disposition,variable_hangup_cause,variable_hangup_cause_q850,variable_duration,variable_billsec,variable_progresssec,variable_answersec,variable_waitsec,variable_mduration,variable_billmsec,variable_progressmsec,variable_answermsec,variable_waitmsec,variable_progress_mediamsec,variable_call_uuid,variable_origination_caller_id_number,variable_caller_id,variable_answer_epoch,variable_answer_uepoch"}1' /usr/share/plivo/etc/plivo/default.conf > /tmp/default.conf
mv /tmp/default.conf /usr/share/plivo/etc/plivo/default.conf

#Stop/Start Plivo & Cache Server
/etc/init.d/plivo stop
/etc/init.d/plivocache stop
/etc/init.d/plivo start
/etc/init.d/plivocache start



#Install Newfies
cd /usr/src/
wget https://raw.github.com/Star2Billing/newfies-dialer/master/install/install-newfies.sh
bash install-newfies.sh




