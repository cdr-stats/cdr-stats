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
# wget --no-check-certificate https://raw.github.com/Star2Billing/newfies-dialer/master/install/freeswitch/install-freeswitch.sh
#
#
#TODO: install memcache



# Identify Linux Distribution type
if [ -f /etc/debian_version ] ; then
    DIST='DEBIAN'
elif [ -f /etc/redhat-release ] ; then
    DIST='CENTOS'
else
    echo ""
    echo "This Installer should be run on a CentOS or a Debian based system"
    echo ""
    exit 1
fi


FS_CONF_PATH=https://raw.github.com/Star2Billing/newfies-dialer/master/install/freeswitch-conf
FS_INIT_PATH=https://raw.github.com/Star2Billing/newfies-dialer/master/install/freeswitch-init
FS_GIT_REPO=git://git.freeswitch.org/freeswitch.git
FS_INSTALLED_PATH=/usr/local/freeswitch
FS_CONFIG_PATH=/etc/freeswitch

#####################################################
FS_BASE_PATH=/usr/src/
#####################################################

CURRENT_PATH=$PWD

clear
echo ""
echo "FreeSWITCH will be installed in $FS_INSTALLED_PATH"
echo "Press Enter to continue or CTRL-C to exit"
echo ""
read INPUT

func_install_fs_source() {
    #install fs from source
   	echo "installing from source"
   	
   	#Add Freeswitch group and user
	grep -c "^freeswitch:" /etc/group &> /dev/null
	if [ $? = 1 ]; then
       /usr/sbin/groupadd -r -f freeswitch
	else
       echo "group freeswitch already present"
	fi

	grep -c "^freeswitch:" /etc/passwd &> /dev/null
	if [ $? = 1 ]; then
       echo "adding user freeswitch..."
       /usr/sbin/useradd -r -c "freeswitch" -g freeswitch freeswitch
	else
       echo "user freeswitch already present"
	fi

	    	
	# Install FreeSWITCH
	cd $FS_BASE_PATH
	git clone $FS_GIT_REPO
	cd $FS_BASE_PATH/freeswitch
	sh bootstrap.sh && ./configure --without-pgsql --prefix=/usr/local/freeswitch --sysconfdir=/etc/freeswitch/
	[ -f modules.conf ] && cp modules.conf modules.conf.bak
	sed -i -e \
	"s/#applications\/mod_curl/applications\/mod_curl/g" \
	-e "s/#asr_tts\/mod_flite/asr_tts\/mod_flite/g" \
	-e "s/#asr_tts\/mod_tts_commandline/asr_tts\/mod_tts_commandline/g" \
	-e "s/#formats\/mod_shout/formats\/mod_shout/g" \
	-e "s/#endpoints\/mod_dingaling/endpoints\/mod_dingaling/g" \
	-e "s/#formats\/mod_shell_stream/formats\/mod_shell_stream/g" \
	-e "s/#say\/mod_say_de/say\/mod_say_de/g" \
	-e "s/#say\/mod_say_es/say\/mod_say_es/g" \
	-e "s/#say\/mod_say_fr/say\/mod_say_fr/g" \
	-e "s/#say\/mod_say_it/say\/mod_say_it/g" \
	-e "s/#say\/mod_say_nl/say\/mod_say_nl/g" \
	-e "s/#say\/mod_say_ru/say\/mod_say_ru/g" \
	-e "s/#say\/mod_say_zh/say\/mod_say_zh/g" \
	-e "s/#say\/mod_say_hu/say\/mod_say_hu/g" \
	-e "s/#say\/mod_say_th/say\/mod_say_th/g" \
	-e "s/#xml_int\/mod_xml_cdr/xml_int\/mod_xml_cdr/g" \
	modules.conf
	make && make install && make sounds-install && make moh-install


	#Set permissions
	chown -R freeswitch:freeswitch /usr/local/freeswitch /etc/freeswitch
	
#installed fs from source 
}


echo "Setting up Prerequisites and Dependencies for FreeSWITCH"
case $DIST in
    'DEBIAN')
        apt-get -y update
        apt-get -y install autoconf automake autotools-dev binutils bison build-essential cpp curl flex g++ gcc git-core libaudiofile-dev libc6-dev libdb-dev libexpat1 libgdbm-dev libgnutls-dev libmcrypt-dev libncurses5-dev libnewt-dev libpcre3 libpopt-dev libsctp-dev libsqlite3-dev libtiff4 libtiff4-dev libtool libx11-dev libxml2 libxml2-dev lksctp-tools lynx m4 make mcrypt ncftp nmap openssl sox sqlite3 ssl-cert ssl-cert unixodbc-dev unzip zip zlib1g-dev zlib1g-dev
        apt-get -y install libssl-dev pkg-config
        apt-get -y install libvorbis0a libogg0 libogg-dev libvorbis-dev
        apt-get -y install flite flite1-dev
        #Install Freeswitch
        func_install_fs_source
        ;;
    'CENTOS')
    	echo ""
    	echo "Do you want to install Freeswitch via the yum repository instead of from source [y/n]" 
		read YUMSOURCE
        yum -y update
        yum -y install autoconf automake bzip2 cpio curl curl-devel curl-devel expat-devel fileutils gcc-c++ gettext-devel gnutls-devel libjpeg-devel libogg-devel libtiff-devel libtool libvorbis-devel make ncurses-devel nmap openssl openssl-devel openssl-devel perl patch unixODBC unixODBC-devel unzip wget zip zlib zlib-devel
        yum -y install flite

		#install the RPMFORGE Repository
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
        
        yum -y --enablerepo=rpmforge install git-core
        
		if [ "$YUMSOURCE" = "y" ] || [ "$YUMSOURCE" = "Y" ]; then
	    	echo "Installing via yum repository"
	    	
	    	# install the Freeswitch Repo
			rpm -Uvh http://files.freeswitch.org/yum/freeswitch-release-1-0.noarch.rpm

			# install the freeswitch files
			yum -y install freeswitch-config-vanilla freeswitch-codec-siren freeswitch-codec-passthru-amr freeswitch-application-conference freeswitch-application-db freeswitch-endpoint-dingaling freeswitch-application-enum freeswitch-application-esf freeswitch-application-expr freeswitch-application-fifo freeswitch-asrtts-flite freeswitch-application-fsv freeswitch-codec-passthru-g723_1 freeswitch-codec-passthru-g729 freeswitch-codec-h26x freeswitch-application-hash freeswitch-application-httapi freeswitch-codec-ilbc freeswitch-format-local-stream freeswitch-lua freeswitch-format-native-file freeswitch-lang-de freeswitch-lang-en freeswitch-lang-fr freeswitch-lang-ru freeswitch-format-mod-shout freeswitch-codec-speex freeswitch-spidermonkey freeswitch-format-tone-stream freeswitch-asrtts-tts-commandline freeswitch-application-valet_parking freeswitch-application-voicemail freeswitch-format-shell-stream
	    		    	
    	else
        	echo "installing from source"
        	func_install_fs_source
    	fi
     
    ;;
esac
    

# Enable FreeSWITCH modules
cd $FS_CONFIG_PATH/autoload_configs/
[ -f modules.conf.xml ] && cp modules.conf.xml modules.conf.xml.bak
sed -i -r \
-e "s/<\!--\s?<load module=\"mod_xml_curl\"\/>\s?-->/<load module=\"mod_xml_curl\"\/>/g" \
-e "s/<\!--\s?<load module=\"mod_xml_cdr\"\/>\s?-->/<load module=\"mod_xml_cdr\"\/>/g" \
-e "s/<\!--\s?<load module=\"mod_dingaling\"\/>\s?-->/<load module=\"mod_dingaling\"\/>/g" \
-e "s/<\!--\s?<load module=\"mod_shell_stream\"\/>\s?-->/<load module=\"mod_shell_stream\"\/>/g" \
-e "s/<\!-- \s?<load module=\"mod_shell_stream\"\/>\s? -->/<load module=\"mod_shell_stream\"\/>/g" \
-e "s/<\!--\s?<load module=\"mod_shout\"\/>\s?-->/<load module=\"mod_shout\"\/>/g" \
-e "s/<\!--\s?<load module=\"mod_tts_commandline\"\/>\s?-->/<load module=\"mod_tts_commandline\"\/>/g" \
-e "s/<\!--\s?<load module=\"mod_flite\"\/>\s?-->/<load module=\"mod_flite\"\/>/g" \
-e "s/<\!--\s?<load module=\"mod_say_ru\"\/>\s?-->/<load module=\"mod_say_ru\"\/>/g" \
-e "s/<\!--\s?<load module=\"mod_say_zh\"\/>\s?-->/<load module=\"mod_say_zh\"\/>/g" \
-e 's/mod_say_zh.*$/&\n    <load module="mod_say_de"\/>\n    <load module="mod_say_es"\/>\n    <load module="mod_say_fr"\/>\n    <load module="mod_say_it"\/>\n    <load module="mod_say_nl"\/>\n    <load module="mod_say_hu"\/>\n    <load module="mod_say_th"\/>/' \
modules.conf.xml


#Configure Dialplan
cd $FS_CONFIG_PATH/conf/dialplan/

# Place Plivo Default Dialplan in FreeSWITCH
[ -f default.xml ] && mv default.xml default.xml.bak
wget --no-check-certificate $FS_CONF_PATH/default.xml -O default.xml

# Place Plivo Public Dialplan in FreeSWITCH
[ -f public.xml ] && mv public.xml public.xml.bak
wget --no-check-certificate $FS_CONF_PATH/public.xml -O public.xml


#Configure XML CDR
#cd $FS_INSTALLED_PATH/conf/autoload_configs/

#this is commented as we don't use xml_cdr anymore
## Place Newfies XML CDR conf in FreeSWITCH
#[ -f xml_cdr.conf.xml ] && mv xml_cdr.conf.xml xml_cdr.conf.xml.bak
#wget --no-check-certificate $FS_CONF_PATH/xml_cdr.conf.xml -O xml_cdr.conf.xml
#create dir to store send error of CDR
#mkdir /usr/local/freeswitch/log/err_xml_cdr/

#Return to current path
cd $CURRENT_PATH



case $DIST in
    'DEBIAN')
        #Install init.d script
        wget --no-check-certificate $FS_INIT_PATH/debian/freeswitch -O /etc/init.d/freeswitch
        chmod 0755 /etc/init.d/freeswitch
        cd /etc/init.d; update-rc.d freeswitch defaults 90
     ;;
    'CENTOS')
        #Install init.d script
        wget --no-check-certificate $FS_INIT_PATH/centos/freeswitch -O /etc/init.d/freeswitch
        chmod 0755 /etc/init.d/freeswitch
        chkconfig --add freeswitch
        chkconfig --level 345 freeswitch on
    ;;
esac


#replace with our own working init script as per http://jira.freeswitch.org/browse/FS-4042
if [ "$YUMSOURCE" = "y" ] || [ "$YUMSOURCE" = "Y" ]; then
    	echo "Installed via yum repository"
    	
		#replace with our own working init script as per http://jira.freeswitch.org/browse/FS-4042
    	rm -f /etc/init.d/freeswitch
    	#Install init.d script
       	wget --no-check-certificate $FS_INIT_PATH/centos/freeswitch -O /etc/init.d/freeswitch
       	chmod 0755 /etc/init.d/freeswitch
       	chkconfig --add freeswitch
       	chkconfig --level 345 freeswitch on
       	sed -i "s@/usr/local/freeswitch/bin@/usr/bin@g" /etc/init.d/freeswitch
		sed -i "s@/usr/local/freeswitch/run@/var/run/freeswitch@g" /etc/init.d/freeswitch
		/etc/init.d/freeswitch start
		#We will remove this when the bug is fixed.
		    	
else
       	echo "installing from source"
		#Add alias fs_cli
		chk=`grep "fs_cli" ~/.bashrc|wc -l`
		if [ $chk -lt 1 ] ; then
   			echo "alias fs_cli='/usr/local/freeswitch/bin/fs_cli'" >> ~/.bashrc
    	fi
fi




# Install Complete
#clear
echo ""
echo ""
echo ""
echo "**************************************************************"
echo "Congratulations, FreeSWITCH is now installed at '$FS_INSTALLED_PATH'"
echo "**************************************************************"
echo
echo "* To Start FreeSWITCH in foreground :"
echo "    '$FS_INSTALLED_PATH/bin/freeswitch'"
echo
echo "* To Start FreeSWITCH in background :"
echo "    '$FS_INSTALLED_PATH/bin/freeswitch -nc'"
echo
echo "**************************************************************"
echo ""
echo ""
