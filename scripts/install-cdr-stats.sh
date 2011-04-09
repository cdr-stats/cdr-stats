#!/bin/sh
#   Installation script for CDR-Stats
#   Copyright (C) <2011>  <Star2Billing S.L> 
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
#wget --no-check-certificate https://github.com/Star2Billing/cdr-stats/raw/master/scripts/install-cdr-stats.sh


#Variables
#comment out the appropriate line below to install the desired version
VERSION=master
#VERSION=v1.3.0
DATETIME=$(date +"%Y%m%d%H%M%S")
KERNELARCH=$(uname -p)
DISTRO='UBUNTU'
#DISTRO='CENTOS'
MYSQLUSER=root
MYSQLPASSWORD=passw0rd


clear
echo ""
echo ""
echo "This will install CDR-Stats on your server"
echo "press any key to continue or CTRL-C to exit"
read TEMP

# APACHE CONF
APACHE_CONF_DIR="/etc/apache2/sites-enabled/"
#APACHE_CONF_DIR="/etc/httpd/conf.d/"

IFCONFIG=`which ifconfig 2>/dev/null||echo /sbin/ifconfig`
IPADDR=`$IFCONFIG eth0|gawk '/inet addr/{print $2}'|gawk -F: '{print $2}'`


#python setup tools
echo "Install Dependencies and python modules..."
case $DISTRO in
    'UBUNTU')
        apt-get -y install python-setuptools python-dev build-essential 
        apt-get -y install libapache2-mod-python libapache2-mod-wsgi
        easy_install pip
        easy_install virtualenv
        #ln -s /usr/local/bin/pip /usr/bin/pip
        
        #Install Extra dependencies on New OS
        apt-get -y install mysql-server libmysqlclient-dev
        apt-get -y install git-core
        apt-get install mercurial
    ;;
    'CENTOS')
        #install the RPMFORGE Repository

        if [ ! -f /etc/yum.repos.d/rpmforge.repo ];
            then
	            # Install RPMFORGE Repo
        rpm --import http://apt.sw.be/RPM-GPG-KEY.dag.txt		
        echo '
[rpmforge]
name = Red Hat Enterprise $releasever - RPMforge.net - dag
mirrorlist = http://apt.sw.be/redhat/el5/en/mirrors-rpmforge
enabled = 0
protect = 0
gpgkey = file:///etc/pki/rpm-gpg/RPM-GPG-KEY-rpmforge-dag
gpgcheck = 1
' > /etc/yum.repos.d/rpmforge.repo
        fi

        yum -y --enablerepo=rpmforge install git-core mercurial
        
        #Install Python
        yum -y install python-setuptools python-tools python-devel mod_python
        #Install PIP
        easy_install pip
    ;;
esac


echo "Install CDR-Stats..."
mkdir /usr/share/django_app/
cd /usr/src/
wget --no-check-certificate https://github.com/Star2Billing/cdr-stats/tarball/$VERSION
tar xvzf Star2Billing-cdr-stats-*.tar.gz
rm -rf Star2Billing-cdr-stats-*.tar.gz
mv cdr-stats cdr-stats_$DATETIME
mv Star2Billing-cdr-stats-* cdr-stats
ln -s /usr/src/cdr-stats/cdr_stats /usr/share/django_app/cdr_stats


#Install Cdr-Stats depencencies
pip install -r /usr/share/django_app/cdr_stats/requirements.txt


# Update Secret Key
echo "Update Secret Key..."
RANDPASSW=`</dev/urandom tr -dc A-Za-z0-9| (head -c $1 > /dev/null 2>&1 || head -c 50)`
sed -i "s/^SECRET_KEY.*/SECRET_KEY = \'$RANDPASSW\'/g"  /usr/share/django_app/cdr_stats/settings.py
echo ""


# Disable Debug
sed -i "s/DEBUG = True/DEBUG = False/g"  /usr/share/django_app/cdr_stats/settings.py
sed -i "s/TEMPLATE_DEBUG = DEBUG/TEMPLATE_DEBUG = False/g"  /usr/share/django_app/cdr_stats/settings.py


# Setup settings.py
sed -i "s/'sqlite3'/'mysql'/"  /usr/share/django_app/cdr_stats/settings.py
sed -i "s/.*'NAME'/       'NAME': 'cdr-stats',#/"  /usr/share/django_app/cdr_stats/settings.py
sed -i "/'USER'/s/''/'$MYSQLUSER'/" /usr/share/django_app/cdr_stats/settings.py
sed -i "/'PASSWORD'/s/''/'$MYSQLPASSWORD'/" /usr/share/django_app/cdr_stats/settings.py
sed -i "/'HOST'/s/''/'localhost'/" /usr/share/django_app/cdr_stats/settings.py
sed -i "/'PORT'/s/''/'3306'/" /usr/share/django_app/cdr_stats/settings.py


# Create the Database
echo "Database Creation..."
cd /usr/share/django_app/cdr_stats/
#if we use SQLite 
mkdir database
chmod -R 777 database
python manage.py syncdb
#python manage.py migrate


#Collect static files from apps and other locations in a single location.
python manage.py collectstatic -l



# prepare Apache
echo "Prepare Apache configuration..."
echo '
Listen *:9000

<VirtualHost *:9000>
    DocumentRoot /usr/share/django_app/cdr_stats/
    ErrorLog /var/log/err-cdr-stats.log
    LogLevel warn

    WSGIPassAuthorization On
    WSGIDaemonProcess cdr_stats user=www-data user=www-data threads=25
    WSGIProcessGroup cdr_stats
    WSGIScriptAlias / /usr/share/django_app/cdr_stats/django.wsgi

    <Directory /usr/share/django_app/cdr_stats>
        Order deny,allow
        Allow from all
    </Directory>

</VirtualHost>


' > $APACHE_CONF_DIR/cdr-stats.conf
#correct the above file
sed -i "s/@/'/g"  $APACHE_CONF_DIR/cdr-stats.conf


#Fix permission on python-egg
mkdir /usr/share/django_app/cdr_stats/.python-eggs
chmod 777 /usr/share/django_app/cdr_stats/.python-eggs

case $DISTRO in
    'UBUNTU')
        chown -R www-data.www-data /usr/share/django_app/cdr_stats/database/
        service apache2 restart
    ;;
    'CENTOS')
        service httpd restart
    ;;
esac


clear
echo "Installation Complete"
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

