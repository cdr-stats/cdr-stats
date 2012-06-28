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

#Install mode can me either CLONE or DOWNLOAD
INSTALL_MODE='CLONE'
INSTALL_DIR='/usr/share/cdr_stats'
INSTALL_DIR_WELCOME='/var/www/cdr-stats'
DATABASENAME=$INSTALL_DIR'/database/cdr-stats.db'
MYSQLUSER=""
MYSQLPASSWORD=""
MYHOST=""
MYHOSTPORT=""
CELERYD_USER="celery"
CELERYD_GROUP="celery"
CDRSTATS_ENV="cdr-stats"
HTTP_PORT="8008"
SOUTH_SOURCE='hg+http://bitbucket.org/andrewgodwin/south/@ecaafda23e600e510e252734d67bf8f9f2362dc9#egg=South-dev'
branch=STABLE
db_backend=MySQL


#Include general functions
source bash-common-functions.sh

#Identify the OS
func_identify_os


#Function install the landing page
func_install_landing_page() {
    mkdir -p $INSTALL_DIR_WELCOME
    # Copy files
    cp -r /usr/src/cdr-stats/install/landing-page/* $INSTALL_DIR_WELCOME
    
    echo ""
    echo "Add Apache configuration for Welcome page..."
    echo '    
    <VirtualHost *:80>
        DocumentRoot '$INSTALL_DIR_WELCOME'/
        DirectoryIndex index.html index.htm index.php index.php4 index.php5
        
        <Directory '$INSTALL_DIR_WELCOME'>
            Options Indexes IncludesNOEXEC FollowSymLinks
            allow from all
            AllowOverride All
            allow from all
        </Directory>

    </VirtualHost>
    
    ' > $APACHE_CONF_DIR/welcome-cdr-stats.conf
    
    case $DIST in
        'DEBIAN')
            mv /etc/apache2/sites-enabled/000-default /tmp/
        ;;
    esac
    service $APACHE_SERVICE restart
    
    #Update Welcome page IP
    sed -i "s/LOCALHOST/$IPADDR:$HTTP_PORT/g" $INSTALL_DIR_WELCOME/index.html
}

func_check_dependencies() {
    echo ""
    echo "Checking Python dependencies..."
    echo ""
    
    #Check South
    grep_pip=`pip freeze| grep south`
    if echo $grep_pip | grep -i "south" > /dev/null ; then
        echo "OK : South installed..."
    else
        echo "Error : South not installed..."
        exit 1
    fi
    
    #Check Django
    grep_pip=`pip freeze| grep Django`
    if echo $grep_pip | grep -i "Django" > /dev/null ; then
        echo "OK : Django installed..."
    else
        echo "Error : Django not installed..."
        exit 1
    fi
    
    #Check MySQL-python
    grep_pip=`pip freeze| grep MySQL-python`
    if echo $grep_pip | grep -i "MySQL-python" > /dev/null ; then
        echo "OK : MySQL-python installed..."
    else
        echo "Error : MySQL-python not installed..."
        exit 1
    fi
    
    #Check celery
    grep_pip=`pip freeze| grep celery`
    if echo $grep_pip | grep -i "celery" > /dev/null ; then
        echo "OK : celery installed..."
    else
        echo "Error : celery not installed..."
        exit 1
    fi
    
    #Check django-tastypie
    grep_pip=`pip freeze| grep django-tastypie`
    if echo $grep_pip | grep -i "django-tastypie" > /dev/null ; then
        echo "OK : django-tastypie installed..."
    else
        echo "Error : django-tastypie not installed..."
        exit 1
    fi
    
    #Check raven
    #grep_pip=`pip freeze| grep raven`
    #if echo $grep_pip | grep -i "raven" > /dev/null ; then
    #    echo "OK : raven installed..."
    #else
    #    echo "Error : raven not installed..."
    #    exit 1
    #fi
    
    echo ""
    echo "Python dependencies successfully installed!"
    echo ""
}


#Fuction to create the virtual env
func_setup_virtualenv() {

    echo ""
    echo ""
    echo "This will install virtualenv & virtualenvwrapper"
    echo "and create a new virtualenv : $CDRSTATS_ENV"
    
    easy_install virtualenv
    easy_install virtualenvwrapper
    
    # Enable virtualenvwrapper
    chk=`grep "virtualenvwrapper" ~/.bashrc|wc -l`
    if [ $chk -lt 1 ] ; then
        echo "Set Virtualenvwrapper into bash"
        echo "export WORKON_HOME=/usr/share/virtualenvs" >> ~/.bashrc
        echo "source $SCRIPT_VIRTUALENVWRAPPER" >> ~/.bashrc
    fi
    
    # Setup virtualenv
    export WORKON_HOME=/usr/share/virtualenvs
    source $SCRIPT_VIRTUALENVWRAPPER

    mkvirtualenv $CDRSTATS_ENV
    workon $CDRSTATS_ENV
    
    echo "Virtualenv $CDRSTATS_ENV created and activated"
}

#Function to install Frontend
func_install_frontend(){

    echo ""
    echo ""
    echo "We will now install CDR-Stats on your server"
	echo "============================================"
    echo ""
    echo "Which version do you want to install ? DEVEL or STABLE [DEVEL/STABLE] (default:STABLE)"
    read branch
    echo "Do you want to install CDR-Stats with SQLite or MySQL? [SQLite/MySQL] (default:MySQL)"
    read db_backend

    #python setup tools
    echo "Install Dependencies and python modules..."
    case $DIST in
        'DEBIAN')
            apt-get -y install python-setuptools python-dev build-essential libevent-dev libapache2-mod-python libapache2-mod-wsgi git-core mercurial gawk
            easy_install pip
            
            #|FIXME: Strangely South need to be installed outside the Virtualenv
            pip install -e $SOUTH_SOURCE
                    
            if echo $db_backend | grep -i "^SQLITE" > /dev/null ; then
                apt-get -y install sqlite3 libsqlite3-dev
            else
                apt-get -y install mysql-server libmysqlclient-dev
                #Start MySQL
                /etc/init.d/mysql start
                
                #Configure MySQL
                if [ "$INSTALLMODE" = "FULL" ]; then
                    /usr/bin/mysql_secure_installation
                fi
                
				until mysql -u$MYSQLUSER -p$MYSQLPASSWORD -P$MYHOSTPORT -h$MYHOST -e ";" ; do 
					clear 
                	echo "Enter your database settings"
                	func_get_mysql_database_setting
                done
            fi
            
            #for audiofile convertion
            apt-get -y install libsox-fmt-mp3 libsox-fmt-all mpg321 ffmpeg
        ;;
        'CENTOS')
            if [ "$INSTALLMODE" = "FULL" ]; then
                yum -y update
            fi
            yum -y install autoconf automake bzip2 cpio curl curl-devel curl-devel expat-devel fileutils gcc-c++ gettext-devel gnutls-devel libjpeg-devel libogg-devel libtiff-devel libtool libvorbis-devel make ncurses-devel nmap openssl openssl-devel openssl-devel perl patch unzip wget zip zlib zlib-devel policycoreutils-python
        
            if [ ! -f /etc/yum.repos.d/rpmforge.repo ];
            	then
                	# Install RPMFORGE Repo
        			if [ $KERNELARCH = "x86_64" ]; then
						rpm -ivh http://pkgs.repoforge.org/rpmforge-release/rpmforge-release-0.5.2-2.el6.rf.x86_64.rpm
					else
						rpm -ivh http://pkgs.repoforge.org/rpmforge-release/rpmforge-release-0.5.2-2.el6.rf.i686.rpm
					fi
        	fi
        	
        	yum -y --enablerepo=rpmforge install git-core
        	
            #Install epel repo for pip and mod_python
            if [ $KERNELARCH = "x86_64" ]; then
				rpm -ivh http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-7.noarch.rpm
			else
				rpm -ivh http://dl.fedoraproject.org/pub/epel/6/i386/epel-release-6-7.noarch.rpm
			fi
			
            # disable epel repository since by default it is enabled.
            sed -i "s/enabled=1/enable=0/" /etc/yum.repos.d/epel.repo
            yum -y --enablerepo=epel install python-pip mod_python python-setuptools python-tools python-devel mercurial mod_wsgi libevent libevent-devel
            #start http after reboot
            chkconfig --levels 235 httpd on

            if echo $db_backend | grep -i "^SQLITE" > /dev/null ; then
                yum -y install sqlite
            else
                yum -y install mysql-server mysql-devel
                chkconfig --levels 235 mysqld on
                #Start Mysql
                /etc/init.d/mysqld start
                #Configure MySQL
                if [ "$INSTALLMODE" = "FULL" ]; then
                    /usr/bin/mysql_secure_installation
                fi
				until mysql -u$MYSQLUSER -p$MYSQLPASSWORD -P$MYHOSTPORT -h$MYHOST -e ";" ; do 
					clear 
                	echo "Enter your database settings"
                	func_get_mysql_database_setting
                done            
            fi
        ;;
    esac

    if [ -d "$INSTALL_DIR" ]; then
        # CDR-Stats is already installed
        echo ""
        echo ""
        echo "We detect an existing CDR-Stats Installation"
        echo "if you continue the existing installation will be removed!"
        echo ""
        echo "Press Enter to continue or CTRL-C to exit"
        read TEMP

        mkdir /tmp/old-cdr-stats_$DATETIME
        mv $INSTALL_DIR /tmp/old-cdr-stats_$DATETIME
        echo "Files from $INSTALL_DIR has been moved to /tmp/old-cdr-stats_$DATETIME"
        echo "Run backup with mysqldump..."
        mysqldump -u $MYSQLUSER --password=$MYSQLPASSWORD $DATABASENAME > /tmp/old-cdr-stats_$DATETIME.mysqldump.sql
        echo "Mysql Dump of database $DATABASENAME added in /tmp/old-cdr-stats_$DATETIME.mysqldump.sql"
        echo "Press Enter to continue"
        read TEMP
    fi

    #Create and enable virtualenv
    func_setup_virtualenv
    
    #get CDR-Stats
    echo "Install CDR-Stats..."
    cd /usr/src/
    rm -rf cdr-stats
    mkdir /var/log/cdr-stats

    case $INSTALL_MODE in
        'CLONE')
            git clone git://github.com/Star2Billing/cdr-stats.git
            
            #Install Develop / Master
            if echo $branch | grep -i "^DEVEL" > /dev/null ; then
                cd cdr-stats
                git checkout -b develop --track origin/develop
            fi
        ;;
        # 'DOWNLOAD')
        #    VERSION=master
        #    wget --no-check-certificate https://github.com/Star2Billing/cdr-stats/tarball/$VERSION
        #    mv master Star2Billing-cdr-stats-$VERSION.tar.gz
        #    tar xvzf Star2Billing-cdr-stats-*.tar.gz
        #    rm -rf Star2Billing-cdr-stats-*.tar.gz
        #    mv cdr-stats cdr-stats_$DATETIME
        #    mv Star2Billing-cdr-stats-* cdr-stats        
        #;;
    esac

    # Copy files
    cp -r /usr/src/cdr-stats/cdr_stats $INSTALL_DIR

    #Install CDR-Stats depencencies
    easy_install -U distribute
    echo "Install basic requirements..."
    for line in $(cat /usr/src/cdr-stats/install/requirements/basic-requirements.txt | grep -v \#)
    do
        pip install $line
    done
    echo "Install Django requirements..."
    for line in $(cat /usr/src/cdr-stats/install/requirements/django-requirements.txt | grep -v \#)
    do
        pip install $line
    done
    
    #Add South install again
    pip install -e $SOUTH_SOURCE
    
    #Check Python dependencies
    func_check_dependencies
    
    # copy settings_local.py into cdr-stats dir
    cp /usr/src/cdr-stats/install/conf/settings_local.py $INSTALL_DIR

    # Update Secret Key
    echo "Update Secret Key..."
    RANDPASSW=`</dev/urandom tr -dc A-Za-z0-9| (head -c $1 > /dev/null 2>&1 || head -c 50)`
    sed -i "s/^SECRET_KEY.*/SECRET_KEY = \'$RANDPASSW\'/g"  $INSTALL_DIR/settings.py
    echo ""

    # Disable Debug
    sed -i "s/DEBUG = True/DEBUG = False/g"  $INSTALL_DIR/settings_local.py
    sed -i "s/TEMPLATE_DEBUG = DEBUG/TEMPLATE_DEBUG = False/g"  $INSTALL_DIR/settings_local.py

    if echo $db_backend | grep -i "^SQLITE" > /dev/null ; then
        # Setup settings_local.py for SQLite
        sed -i "s/'init_command/#'init_command/g"  $INSTALL_DIR/settings_local.py
    else    
        # Setup settings_local.py for MySQL
        sed -i "s/'django.db.backends.sqlite3'/'django.db.backends.mysql'/"  $INSTALL_DIR/settings_local.py
        sed -i "s/.*'NAME'/       'NAME': '$DATABASENAME',#/"  $INSTALL_DIR/settings_local.py
        sed -i "/'USER'/s/''/'$MYSQLUSER'/" $INSTALL_DIR/settings_local.py
        sed -i "/'PASSWORD'/s/''/'$MYSQLPASSWORD'/" $INSTALL_DIR/settings_local.py
        sed -i "/'HOST'/s/''/'$MYHOST'/" $INSTALL_DIR/settings_local.py
        sed -i "/'PORT'/s/''/'$MYHOSTPORT'/" $INSTALL_DIR/settings_local.py
    
        # Create the Database
        echo "Remove Existing Database if exists..."
  		if [ -d "/var/lib/mysql/$DATABASENAME" ]; then
	        echo "mysql --user=$MYSQLUSER --password=$MYSQLPASSWORD -e 'DROP DATABASE $DATABASENAME;'"
    	    mysql --user=$MYSQLUSER --password=$MYSQLPASSWORD -e "DROP DATABASE $DATABASENAME;"
		fi
        echo "Create Database..."
        echo "mysql --user=$MYSQLUSER --password=$MYSQLPASSWORD -e 'CREATE DATABASE $DATABASENAME CHARACTER SET UTF8;'"
        mysql --user=$MYSQLUSER --password=$MYSQLPASSWORD -e "CREATE DATABASE $DATABASENAME CHARACTER SET UTF8;"
    fi
    
    cd $INSTALL_DIR/
    
    #Fix permission on python-egg
    mkdir $INSTALL_DIR/.python-eggs
    chown $APACHE_USER:$APACHE_USER $INSTALL_DIR/.python-eggs
    mkdir database
    
    #upload audio files
    mkdir -p $INSTALL_DIR/usermedia/upload/audiofiles
    chown -R $APACHE_USER:$APACHE_USER $INSTALL_DIR/usermedia
    
    #following lines is for apache logs
    touch /var/log/cdr-stats/cdr-stats.log
    touch /var/log/cdr-stats/cdr-stats-db.log
    touch /var/log/cdr-stats/err-apache-cdr-stats.log
    chown -R $APACHE_USER:$APACHE_USER /var/log/cdr-stats
    
    python manage.py syncdb --noinput
    python manage.py migrate
    echo ""
    echo ""
    echo "Create a super admin user..."
    python manage.py createsuperuser
    
    #echo ""
    #echo "Create a super user for API, use a different username..."
    #python manage.py createsuperuser
    #echo ""
    #echo "Enter the Username you enteded for the API"
    #read APIUSERNAME
    #echo ""
    #echo "Enter the Password for the API "
    #read APIPASSWORD

    #Collect static files from apps and other locations in a single location.
    python manage.py collectstatic -l --noinput
    
    #Permission on database folder if we use SQLite    
    chown -R $APACHE_USER:$APACHE_USER $INSTALL_DIR/database/
    
    
    #Configure for Asterisk / Freeswitch etc...
    case $INSTALL_TYPE in
        'ASTERISK')
            DATABASENAME='asteriskcdr'
            MYSQLUSER='root'
            MYSQLPASSWORD='password'
            MYHOST='localhost'
            MYHOSTPORT='3306'

            echo ""
            echo "Enter database settings for Asterisk..."
            echo ""
            func_get_mysql_database_setting_asteriskcdrdb

            #Update Mysql schema
            echo "We will now add a Primary Key to your CDR database"
            echo "We advice you to first backup your database prior continuing"
            echo ""
            echo "Press Enter to continue or CTRL-C to exit"
            read TEMP
            mysql -u$MYSQLUSER -p$MYSQLPASSWORD -P$MYHOSTPORT -h$MYHOST $DATABASENAME -e "ALTER TABLE cdr ADD acctid BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST;"

            #enable CDR-Stats for Asterisk
            sed -i "s/freeswitch/asterisk/g"  $INSTALL_DIR/settings_local.py
            
            #Configure CDR Import
            sed -i "s/MYSQL_IMPORT_CDR_DBNAME/$DATABASENAME/g"  $INSTALL_DIR/settings_local.py
            sed -i "s/MYSQL_IMPORT_CDR_TABLENAME/cdr/g"  $INSTALL_DIR/settings_local.py
            sed -i "s/MYSQL_IMPORT_CDR_HOST/$MYHOST/g"  $INSTALL_DIR/settings_local.py
            sed -i "s/MYSQL_IMPORT_CDR_USER/$MYSQLUSER/g"  $INSTALL_DIR/settings_local.py
            sed -i "s/MYSQL_IMPORT_CDR_PASSWORD/$MYSQLPASSWORD/g"  $INSTALL_DIR/settings_local.py
        ;;
        'FREESWITCH')
            echo "Defaut settings are fine with FreeSwitch..."
        ;;
    esac

    # prepare Apache
    echo "Prepare Apache configuration..."
    echo '
    '$WSGI_ADDITIONAL'
    
    Listen *:'$HTTP_PORT'
    
    <VirtualHost *:'$HTTP_PORT'>
        DocumentRoot '$INSTALL_DIR'/
        ErrorLog /var/log/cdr-stats/err-apache-cdr-stats.log
        LogLevel warn

        Alias /static/ "'$INSTALL_DIR'/static/"

        <Location "/static/">
            SetHandler None
        </Location>

        WSGIPassAuthorization On
        WSGIDaemonProcess cdr-stats user='$APACHE_USER' user='$APACHE_USER' threads=25
        WSGIProcessGroup cdr-stats
        WSGIScriptAlias / '$INSTALL_DIR'/django.wsgi

        <Directory '$INSTALL_DIR'>
            AllowOverride all
            Order deny,allow
            Allow from all
            '$WSGIApplicationGroup'
        </Directory>

    </VirtualHost>
    
    ' > $APACHE_CONF_DIR/cdr-stats.conf
    #correct the above file
    sed -i "s/@/'/g"  $APACHE_CONF_DIR/cdr-stats.conf
    
    IFCONFIG=`which ifconfig 2>/dev/null||echo /sbin/ifconfig`
    IPADDR=`$IFCONFIG eth0|gawk '/inet addr/{print $2}'|gawk -F: '{print $2}'`
    if [ -z "$IPADDR" ]; then
        clear
        echo "we have not detected your IP address automatically, please enter it manually"
        read IPADDR
	fi
	    
    #Update Authorize local IP
    sed -i "s/SERVER_IP_PORT/$IPADDR:$HTTP_PORT/g" $INSTALL_DIR/settings_local.py
    sed -i "s/#'SERVER_IP',/'$IPADDR',/g" $INSTALL_DIR/settings_local.py
    sed -i "s/SERVER_IP/$IPADDR/g" $INSTALL_DIR/settings_local.py
    
    
    #add service for socketio server
    echo "Add service for socketio server..."
    cp /usr/src/cdr-stats/install/cdr-stats-socketio /etc/init.d/cdr-stats-socketio
    chmod +x /etc/init.d/cdr-stats-socketio
    case $DIST in
        'DEBIAN')
            #Add SocketIO to Service
            cd /etc/init.d; update-rc.d cdr-stats-socketio defaults 99
            /etc/init.d/cdr-stats-socketio start
        ;;
        'CENTOS')
            #Add SocketIO to Service
            chkconfig --add cdr-stats-socketio
            chkconfig --level 2345 cdr-stats-socketio on
            /etc/init.d/cdr-stats-socketio start
        ;;
    esac
    
    #Setup Timezone
    case $DIST in
        'DEBIAN')
            service apache2 restart
            #Get TZ
			ZONE=$(head -1 /etc/timezone)
        ;;
        'CENTOS')
        	#Get TZ
			. /etc/sysconfig/clock
        ;;
    esac
    #Set Timezone in settings_local.py
    sed -i "s@Europe/Madrid@$ZONE@g" $INSTALL_DIR/settings_local.py
        
    if [ "$INSTALLMODE" = "FULL" ]; then
        #Setup Firewall / SELINUX
        case $DIST in
            'CENTOS')
                echo ""
                echo "We will now add port $HTTP_PORT  and port 80 to your Firewall"
                echo "Press Enter to continue or CTRL-C to exit"
                read TEMP
            
                #add HTTP port
                iptables -I INPUT 2 -p tcp -m state --state NEW -m tcp --dport $HTTP_PORT -j ACCEPT
                iptables -I INPUT 3 -p tcp -m state --state NEW -m tcp --dport 80 -j ACCEPT
                service iptables save
                
                #Selinux to allow apache to access this directory
                chcon -Rv --type=httpd_sys_content_t /usr/share/virtualenvs/cdr-stats/
                chcon -Rv --type=httpd_sys_content_t $INSTALL_DIR/usermedia
                semanage port -a -t http_port_t -p tcp $HTTP_PORT
                #Allowing Apache to access Redis port
                semanage port -a -t http_port_t -p tcp 6379
                semanage port -a -t http_port_t -p tcp 27017
            ;;
        esac
    fi
    
    #Restart HTTP Server
    service $APACHE_SERVICE restart

    echo ""
    echo ""
    echo "**************************************************************"
    echo "Congratulations, CDR-Stats Web Application is now installed!"
    echo "**************************************************************"
    echo ""
    echo "Please log on to CDR-Stats at "
    echo "http://$IPADDR:$HTTP_PORT"
    echo "the username and password are the ones you entered during this installation."
    echo ""
    echo "Thank you for installing CDR-Stats"
    echo "Yours"
    echo "The Star2Billing Team"
    echo "http://www.star2billing.com and http://www.cdr-stats.org/"
    echo ""
    echo ""
}


#Function to install backend
func_install_backend() {
    echo ""
    echo ""
    echo "This will install CDR-Stats Backend, Celery & Redis on your server"
    echo "Press Enter to continue or CTRL-C to exit"
    read TEMP
    
    #TODO Add install of dependencies...

    IFCONFIG=`which ifconfig 2>/dev/null||echo /sbin/ifconfig`
    IPADDR=`$IFCONFIG eth0|gawk '/inet addr/{print $2}'|gawk -F: '{print $2}'`
    if [ -z "$IPADDR" ]; then
        clear
        echo "we have not detected your IP address automatically, please enter it manually"
        read IPADDR
	fi
    
    #Create directory for pid file
    mkdir -p /var/run/celery
    
    #Install Celery & redis-server
    echo "Install Redis-server ..."
    func_install_redis_server

    #Memcache installation
    #pip install python-memcached

    echo ""
    echo "Configure Celery..."
    
    case $DIST in
        'DEBIAN')
            # Add init-scripts
            cp /usr/src/cdr-stats/install/celery-init/debian/etc/default/cdr-stats-celeryd /etc/default/
            cp /usr/src/cdr-stats/install/celery-init/debian/etc/init.d/cdr-stats-celeryd /etc/init.d/
            
            # Configure init-scripts
            sed -i "s/CELERYD_USER='celery'/CELERYD_USER='$CELERYD_USER'/g"  /etc/default/cdr-stats-celeryd
            sed -i "s/CELERYD_GROUP='celery'/CELERYD_GROUP='$CELERYD_GROUP'/g"  /etc/default/cdr-stats-celeryd

            chmod +x /etc/default/cdr-stats-celeryd
            chmod +x /etc/init.d/cdr-stats-celeryd

            /etc/init.d/cdr-stats-celeryd restart
            
            cd /etc/init.d; update-rc.d cdr-stats-celeryd defaults 99
            
            #Check permissions on /dev/shm to ensure that celery can start and run for openVZ. 
			DIR="/dev/shm"
			echo "Checking the permissions for $dir"
			stat $DIR
			echo "##############################################"
			if [ `stat -c "%a" $DIR` -ge 777 ] ; then
     			echo "$DIR has Read Write permissions."
			else
     			echo "$DIR has no read write permissions."
        		chmod -R 777 /dev/shm
        		if [ `grep -i /dev/shm /etc/fstab | wc -l` -eq 0 ]; then
                	echo "Adding fstab entry to set permissions /dev/shm"
                	echo "none /dev/shm tmpfs rw,nosuid,nodev,noexec 0 0" >> /etc/fstab
        		fi
			fi
        ;;
        'CENTOS')
            # Add init-scripts
            cp /usr/src/cdr-stats/install/celery-init/centos/etc/default/cdr-stats-celeryd /etc/default/
            cp /usr/src/cdr-stats/install/celery-init/centos/etc/init.d/cdr-stats-celeryd /etc/init.d/

            # Configure init-scripts
            sed -i "s/CELERYD_USER='celery'/CELERYD_USER='$CELERYD_USER'/g"  /etc/default/cdr-stats-celeryd
            sed -i "s/CELERYD_GROUP='celery'/CELERYD_GROUP='$CELERYD_GROUP'/g"  /etc/default/cdr-stats-celeryd
            chmod +x /etc/init.d/cdr-stats-celeryd
            /etc/init.d/cdr-stats-celeryd restart
            
            chkconfig --add cdr-stats-celeryd
            chkconfig --level 2345 cdr-stats-celeryd on
        ;;
    esac
    
    #Active logrotate
    func_logrotate

    echo ""
    echo ""
    echo "**************************************************************"
    echo "Congratulations, CDR-Stats Backend is now installed"
    echo "**************************************************************"
    echo ""
    echo "Yours"
    echo "The Star2Billing Team"
    echo "http://www.star2billing.com and http://www.cdr-stats.org/"
    echo ""
    echo ""
}


#Install recent version of redis-server
func_install_redis_server() {
    case $DIST in
        'DEBIAN')
            if [ "$(lsb_release -cs)" == "precise" ]; then
                #Ubuntu 12.04 TLS
                apt-get -y install redis-server
                /etc/init.d/redis-server.dpkg-dist start
            else
                #Ubuntu 10.04 TLS
                cd /usr/src
                wget http://redis.googlecode.com/files/redis-2.4.14.tar.gz
                tar -zxf redis-2.4.14.tar.gz
                cd redis-2.4.14
                make
                make install
                
                cp /usr/src/cdr-stats/install/redis/debian/etc/redis.conf /etc/redis.conf
                cp /usr/src/cdr-stats/install/redis/debian/etc/init.d/redis-server /etc/init.d/redis-server
                chmod +x /etc/init.d/redis-server
                useradd redis
                mkdir -p /var/lib/redis
                mkdir -p /var/log/redis
                chown redis.redis /var/lib/redis
                chown redis.redis /var/log/redis
                
                cd /etc/init.d/
                update-rc.d -f redis-server defaults

                #Start redis-server
                /etc/init.d/redis-server start
            fi
        ;;
        'CENTOS')
            #install redis
            yum -y --enablerepo=epel install redis
            
            chkconfig --add redis
            chkconfig --level 2345 redis on
            
            /etc/init.d/redis start
            #Fixme : /etc/init.d/redis
            # pid seems to point at wrong place
            # not critical but /etc/init.d/redis status won't work
        ;;
    esac
}

#Add Logrotate
func_logrotate() {
    touch /etc/logrotate.d/cdr_stats
    echo '
/var/log/cdr-stats/celery*log {
    missingok
    rotate 10
    compress
    size 10M
    postrotate
        /etc/init.d/cdr-stats-celeryd restart > /dev/null
    endscript
}
'  > /etc/logrotate.d/cdr_stats

    logrotate /etc/logrotate.d/cdr_stats
}

#Install MongoDB
func_install_mongodb() {
    cd /usr/src/
    rm install-mongodb.sh
    wget https://raw.github.com/Star2Billing/cdr-stats/master/install/install-mongodb.sh
    bash install-mongodb.sh
}


#Menu Section for Script
show_menu_cdr_stats() {
	clear
	echo " > CDR-Stats Installation Menu"
	echo "====================================="
	echo "	1)  Install All"
	echo "	2)  Install CDR-Stats Web Frontend"
	echo "	3)  Install CDR-Stats Backend / CDR-Stats-Celery"
	echo "	4)  Install MongoDB"
	echo "	0)  Quit"
	echo -n "(0-4) : "
	read OPTION < /dev/tty
}


run_menu_cdr_stats_install() {
    ExitFinish=0
    while [ $ExitFinish -eq 0 ]; do
        # Show menu with Installation items
        show_menu_cdr_stats
        case $OPTION in
            1)
                func_install_mongodb
                func_install_frontend
                func_install_backend
                echo done
            ;;
            2)
                func_install_frontend
            ;;
            3)
                func_install_backend
            ;;
            4)
                func_install_mongodb
            ;;
            0)
                ExitFinish=1
            ;;
            *)
        esac
    done
}

run_menu_cdr_stats_install_landingpage() {
    ExitFinish=0
    while [ $ExitFinish -eq 0 ]; do
        # Show menu with Installation items
        show_menu_cdr_stats
        case $OPTION in
            1)
                func_install_mongodb
                func_install_frontend
                func_install_landing_page
                func_install_backend
                echo done
            ;;
            2)
                func_install_frontend
                func_install_landing_page
            ;;
            3)
                func_install_backend
            ;;
            4)
                func_install_mongodb
            ;;
            0)
                ExitFinish=1
            ;;
            *)
        esac
    done
}
