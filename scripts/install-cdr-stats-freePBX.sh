#!/bin/sh
#   Installation script for CDR-Stats with FreePBX pre-installed
#   Copyright (C) <2010>  <Star2Billing S.L> 
#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation; either version 2
#of the License, or (at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# To download this script direct to your server type
#wget --no-check-certificate https://github.com/Star2Billing/cdr-stats/raw/master/scripts/install-cdr-stats-freePBX.sh


#Variables
#comment out the appropriate line below to install the desired version
#CDRSTATSVERSION=master
CDRSTATSVERSION=v1.3.0
MYSQLROOTPASSWOOD=passw0rd
MYSQLUSER=asteriskuser
MYSQLPASSWORD=amp109
DATETIME=$(date +"%Y%m%d%H%M%S")
KERNELARCH=$(uname -p)


clear
echo "DO NOT RUN THIS SCRIPT ON INSTALLATIONS Except for FreePBX on CentOS"
echo ""
echo "Please note that if this is run on a system with no eth0, e.g. Proxmox"
echo "You will have to edit:-"
echo "/usr/src/cdr-stats/cdr_stats/settings.py"
echo "Line 59, MEDIA_URL = and put in your IP address manually"
echo "then restart apache with the command service httpd restart"
echo ""
echo ""
echo "Remeber to check the variables before running this script"
echo "By default the variables are"
echo "Mysql root password = passw0rd"
echo "MySQL User = asteriskuser (taken from /etc/amportal.conf)"
echo "asteriskuser password is amp109 (taken from /etc/amportal.conf)"
echo "If correct, press any key to continue or CTRL-C to exit"
read TEMP

# APACHE CONF
#APACHE_CONF_DIR="/etc/apache2/conf.d/"
APACHE_CONF_DIR="/etc/httpd/conf.d/"

IFCONFIG=`which ifconfig 2>/dev/null||echo /sbin/ifconfig`
IPADDR=`$IFCONFIG eth0|gawk '/inet addr/{print $2}'|gawk -F: '{print $2}'`


#python setup tools
echo "Install Dependencies and python modules..."
yum -y install python-setuptools python-tools python-devel mod_python


#Install PIP
rpm -ivh http://download.fedora.redhat.com/pub/epel/5/i386/epel-release-5-4.noarch.rpm 
# disable epel repository since by default it is enabled. It is not recommended to keep 
# non standard repositories activated. Use it just in case you need.
sed -i "s/enabled=1/enable=0/" /etc/yum.repos.d/epel.repo 
yum --enablerepo=epel install python-pip


#get CDR-Stats
echo "Install CDR-Stats..."
mkdir /usr/share/django_app/
cd /usr/src/
wget --no-check-certificate https://github.com/Star2Billing/cdr-stats/tarball/$CDRSTATSVERSION
tar xvzf Star2Billing-cdr-stats-*.tar.gz
rm -rf Star2Billing-cdr-stats-*.tar.gz
mv cdr-stats cdr-stats_$DATETIME
mv Star2Billing-cdr-stats-* cdr-stats
ln -s /usr/src/cdr-stats/cdr_stats /usr/share/django_app/cdr_stats


#Install Cdr-Stats depencencies
pip install -r /usr/share/django_app/cdr-stats/requirements.txt


# Update Secret Key
echo "Update Secret Key..."
RANDPASSW=`</dev/urandom tr -dc A-Za-z0-9| (head -c $1 > /dev/null 2>&1 || head -c 50)`
sed -i "s/^SECRET_KEY.*/SECRET_KEY = \'$RANDPASSW\'/g"  /usr/share/django_app/cdr_stats/settings.py
echo ""


# Disable Debug
sed -i "s/DEBUG = True/DEBUG = False/g"  /usr/share/django_app/cdr_stats/settings.py
sed -i "s/TEMPLATE_DEBUG = DEBUG/TEMPLATE_DEBUG = False/g"  /usr/share/django_app/cdr_stats/settings.py


# Configure the IP
echo "Configure CDR-Stats to run on $IPADDR : 9000..."
sed -i "s/localhost/$IPADDR/g"  /usr/share/django_app/cdr_stats/settings.py


#FreePBX specific Config
#Backup existing CDR Database
mysqldump -uroot -p$MYSQLROOTPASSWOOD asteriskcdrdb > /root/asteriskcdrdb-$DATETIME.sql


# Setup settings.py
sed -i "s/'sqlite3'/'mysql'/"  /usr/share/django_app/cdr_stats/settings.py
sed -i "s/.*'NAME'/       'NAME': 'asteriskcdrdb',#/"  /usr/share/django_app/cdr_stats/settings.py
sed -i "/'USER'/s/''/'$MYSQLUSER'/" /usr/share/django_app/cdr_stats/settings.py
sed -i "/'PASSWORD'/s/''/'$MYSQLPASSWORD'/" /usr/share/django_app/cdr_stats/settings.py
sed -i "/'HOST'/s/''/'localhost'/" /usr/share/django_app/cdr_stats/settings.py
sed -i "/'PORT'/s/''/'3306'/" /usr/share/django_app/cdr_stats/settings.py
sed -i "s/'dilla'/#'dilla'/" /usr/share/django_app/cdr_stats/settings.py
sed -i "s/8000/9000/"  /usr/share/django_app/cdr_stats/settings.py


# Create the Database
echo "Database Creation..."
cd /usr/share/django_app/cdr_stats/
mkdir database
chmod -R 777 database
python manage.py syncdb
python manage.py migrate


#Collect static files from apps and other locations in a single location.
python manage.py collectstatic -l


#Update Database
RESULT=`/usr/bin/mysql -uroot -p$MYSQLROOTPASSWOOD <<SQL

use asteriskcdrdb
	
    CREATE TABLE cdr_new (
        acctid integer NOT NULL AUTO_INCREMENT PRIMARY KEY,
        src varchar(80) NOT NULL,
        dst varchar(80) NOT NULL,
        calldate datetime NOT NULL,
        clid varchar(80) NOT NULL,
        dcontext varchar(80) NOT NULL,
        channel varchar(80) NOT NULL,
        dstchannel varchar(80) NOT NULL,
        lastapp varchar(80) NOT NULL,
        lastdata varchar(80) NOT NULL,
        duration integer unsigned NOT NULL,
        billsec integer unsigned NOT NULL,
        disposition integer unsigned NOT NULL,
        amaflags integer unsigned NOT NULL,
        accountcode integer unsigned NOT NULL,
        uniqueid varchar(32) NOT NULL,
        userfield varchar(80) NOT NULL
    );


    INSERT INTO cdr_new (src,dst,calldate,clid,dcontext,channel,dstchannel,lastapp,lastdata,duration,billsec,disposition,amaflags,accountcode,uniqueid,userfield) SELECT src,dst,calldate,clid,dcontext,channel,dstchannel,lastapp,lastdata,duration,billsec,disposition,amaflags,accountcode,uniqueid,userfield FROM cdr;

    RENAME TABLE cdr TO cdr_backup;

    RENAME TABLE cdr_new TO cdr;
    
    ALTER TABLE cdr ADD INDEX ( calldate );
    ALTER TABLE cdr ADD INDEX ( dst );
    ALTER TABLE cdr ADD INDEX ( accountcode );

quit
SQL`


# prepare Apache
echo "Prepare Apache configuration..."
echo '
Listen *:9000

    <VirtualHost *:9000>
            DocumentRoot /usr/share/django_app/cdr_stats/
            ErrorLog /usr/share/django_app/err-cdr_stats.log

            <Location "/">
                    SetHandler mod_python
                    PythonHandler django.core.handlers.modpython
                    PythonPath "[@/usr/share/django_app/cdr_stats/@, @/usr/share/django_app/@] + sys.path"
                    SetEnv DJANGO_SETTINGS_MODULE cdr_stats.settings
                    PythonDebug On
                    SetEnv PYTHON_EGG_CACHE /usr/share/django_app/cdr_stats/.python-eggs
            </Location>

            <location "/media">
                    SetHandler None
            </location>
    </VirtualHost>


' > $APACHE_CONF_DIR/cdr-stats.conf
#correct the above file
sed -i "s/@/'/g"  $APACHE_CONF_DIR/cdr-stats.conf


#Fix permission on python-egg
mkdir /usr/share/django_app/cdr_stats/.python-eggs
chmod 777 /usr/share/django_app/cdr_stats/.python-eggs
service httpd restart


#Add IPTables Rule for Access
if [ -e /etc/sysconfig/iptables -a `grep -i 9000 /etc/sysconfig/iptables | wc -l` -eq 0 ]; then
	echo "Opening port 9000"
	iptables -A INPUT -p tcp -m tcp --dport 9000 -j ACCEPT
	service iptables save
fi


clear


echo "Installation Complete"
echo ""
echo "Please note that if this is run on a system with no eth0, e.g. Proxmox"
echo "You will have to edit:-"
echo "/usr/src/cdr-stats/cdr_stats/settings.py"
echo "Line 59, MEDIA_URL = and put in your IP address manually"
echo "then restart apache with the command service httpd restart"
echo ""
echo ""
echo "Please log on to CDR-Stats at "
echo "http://$IPADDR:9000"
echo "the username and password are the ones you entered during this installation."
echo ""
echo "Thank you for installing CDR-Stats"
echo "Yours"
echo "The Star2Billing Team"
echo "http://www.star2billing.com and http://www.cdr-stats.org/"

