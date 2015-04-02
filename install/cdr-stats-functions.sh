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

#Install mode can me either CLONE or DOWNLOAD
INSTALL_MODE='CLONE'
INSTALL_DIR='/usr/share/cdrstats'
INSTALL_DIR_WELCOME='/var/www/cdr-stats'
DATABASENAME='cdrstats_db'
DB_USERSALT=`</dev/urandom tr -dc 0-9| (head -c $1 > /dev/null 2>&1 || head -c 5)`
DB_USERNAME="cdr_stats_$DB_USERSALT"
DB_PASSWORD=`</dev/urandom tr -dc A-Za-z0-9| (head -c $1 > /dev/null 2>&1 || head -c 20)`
DB_HOSTNAME='localhost'
DB_PORT='5432'
CDRSTATS_USER='cdr_stats'
CELERYD_USER="celery"
CELERYD_GROUP="celery"
CDRSTATS_ENV="cdr-stats"
HTTP_PORT="8008"
BRANCH='master'
DB_BACKEND="POSTGRESQL"
DATETIME=$(date +"%Y%m%d%H%M%S")
KERNELARCH=$(uname -p)
SCRIPT_NOTICE="This install script is only intended to run on Debian 7.X"

#Django bug https://code.djangoproject.com/ticket/16017
export LANG="en_US.UTF-8"


# Identify Linux Distribution
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

#Function install the landing page
func_install_landing_page() {
    mkdir -p $WELCOME_DIR
    # Copy files
    cp -r /usr/src/cdr-stats/install/landing-page/* $WELCOME_DIR
    echo ""
    echo "Add Nginx configuration for Welcome page..."
    cp -rf /usr/src/cdr-stats/install/nginx/global /etc/nginx/
    case $DIST in
        'DEBIAN')
            cp /usr/src/cdr-stats/install/nginx/sites-available/cdr_stats.conf /etc/nginx/sites-available/
            ln -s /etc/nginx/sites-available/cdr_stats.conf /etc/nginx/sites-enabled/cdr_stats.conf
            #Remove default NGINX landing page
            rm /etc/nginx/sites-enabled/default
        ;;
        'CENTOS')
            cp /usr/src/cdr-stats/install/nginx/sites-available/cdr_stats.conf /etc/nginx/conf.d/
            rm /etc/nginx/conf.d/default.conf
        ;;
    esac

    cp -rf /usr/src/cdr-stats/install/nginx/global /etc/nginx/

    #Restart Nginx
    service nginx restart

    #Update Welcome page IP
    sed -i "s/LOCALHOST/$IPADDR:$HTTP_PORT/g" $WELCOME_DIR/index.html
}


# Checking Python dependencies
func_check_dependencies() {
    echo ""
    echo "Checking Python dependencies..."
    echo ""

    #Check Django
    grep_pip=`pip freeze| grep Django`
    if echo $grep_pip | grep -i "Django" > /dev/null ; then
        echo "OK : Django installed..."
    else
        echo "Error : Django not installed..."
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

    echo ""
    echo "Python dependencies successfully installed!"
    echo ""
}


#Fuction to create the virtual env
func_setup_virtualenv() {
    echo "This will install virtualenv & virtualenvwrapper"
    echo "and create a new virtualenv : $CDRSTATS_ENV"

    pip install virtualenv
    pip install virtualenvwrapper

    #Prepare settings for installation
    case $DIST in
        'DEBIAN')
            SCRIPT_VIRTUALENVWRAPPER="/usr/local/bin/virtualenvwrapper.sh"
        ;;
        'CENTOS')
            SCRIPT_VIRTUALENVWRAPPER="/usr/bin/virtualenvwrapper.sh"
        ;;
    esac

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


# Prepare system
func_prepare_system_common(){
    #Create CDRStats User
    echo "Create CDRStats User/Group : $CDRSTATS_USER"
    useradd $CDRSTATS_USER --user-group --system --no-create-home

    case $DIST in
        'DEBIAN')
            apt-get update

            export LANGUAGE=en_US.UTF-8
            export LANG=en_US.UTF-8
            export LC_ALL=en_US.UTF-8
            locale-gen en_US.UTF-8
            dpkg-reconfigure locales
            apt-get -y install --reinstall language-pack-en

            apt-get -y install postgresql postgresql-contrib
            pg_createcluster 9.1 main --start

            apt-get -y install python-setuptools python-dev build-essential libevent-dev python-pip
            #We need both Postgresql and Mysql for the Connectors
            apt-get -y install libmysqlclient-dev mysql-client-core-5.5
            apt-get -y install git-core mercurial gawk
            #PostgreSQL
            apt-get -y install libpq-dev
        ;;
        'CENTOS')
            yum -y update
            yum -y install autoconf automake bzip2 cpio curl curl-devel curl-devel expat-devel fileutils gcc-c++ gettext-devel gnutls-devel libjpeg-devel libogg-devel libtiff-devel libtool libvorbis-devel make ncurses-devel nmap openssl openssl-devel openssl-devel perl patch unzip wget zip zlib zlib-devel policycoreutils-python sudo
            yum -y install git

            #Install epel repo for pip and mod_python
            if [ $KERNELARCH = "x86_64" ]; then
                rpm -ivh http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm
            else
                rpm -ivh http://dl.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm
            fi
            # disable epel repository since by default it is enabled.
            sed -i "s/enabled=1/enable=0/" /etc/yum.repos.d/epel.repo

            yum -y --enablerepo=epel install python-pip mod_python python-setuptools python-tools python-devel mercurial libevent libevent-devel
        ;;
    esac
}

#Function to prepare the system, add user, install dependencies, etc...
func_prepare_system_frontend(){

    func_prepare_system_common

    case $DIST in
        'DEBIAN')
            apt-get -y install libapache2-mod-python libapache2-mod-wsgi
            #PostgreSQL
            apt-get -y install postgresql
            #Start PostgreSQL
            /etc/init.d/postgresql start
        ;;
        'CENTOS')
            yum -y install mysql mysql-devel mysql-server
            yum -y --enablerepo=epel install mod_wsgi

            #start http after reboot
            chkconfig --levels 235 httpd on

            if echo $DB_BACKEND | grep -i "^SQLITE" > /dev/null ; then
                yum -y install sqlite
            elif echo $DB_BACKEND | grep -i "^POSTGRESQL" > /dev/null ; then
                #Configure PostgreSQL
                echo "Configure PostgreSQL pg_hba.conf"
                yum -y install postgresql-server postgresql-devel
                chkconfig --levels 235 postgresql on
                echo "service postgresql initdb"
                echo "/etc/init.d/postgresql initdb"
                /etc/init.d/postgresql initdb
                /etc/init.d/postgresql start

                mv /var/lib/pgsql/data/pg_hba.conf /var/lib/pgsql/data/pg_hba.conf.bak
                sed -e '/^local/ d' -e '/^host / d' /var/lib/pgsql/data/pg_hba.conf.bak > /var/lib/pgsql/data/pg_hba.conf
                echo 'local   all         postgres                          trust' >> /var/lib/pgsql/data/pg_hba.conf
                echo 'local   all         all                               md5' >> /var/lib/pgsql/data/pg_hba.conf
                echo 'host    all         postgres    127.0.0.1/32          trust' >> /var/lib/pgsql/data/pg_hba.conf
                echo 'host    all         all         127.0.0.1/32          md5' >> /var/lib/pgsql/data/pg_hba.conf
                echo 'host    all         postgres    ::1/128               trust' >> /var/lib/pgsql/data/pg_hba.conf
                echo 'host    all         all         ::1/128               md5' >> /var/lib/pgsql/data/pg_hba.conf
                #Restart PostgreSQL
                service postgresql restart
            else
                #Install & Start MySQL
                yum -y install mysql-server mysql-devel
                chkconfig --levels 235 mysqld on
                #Start Mysql
                /etc/init.d/mysqld start
                #Configure MySQL
                /usr/bin/mysql_secure_installation
                until mysql -u$MYSQLUSER -p$MYSQLPASSWORD -P$MYHOSTPORT -h$MYHOST -e ";" ; do
                    clear
                    echo "Enter your database settings"
                    func_get_mysql_database_setting
                done
            fi
        ;;
    esac

    #Prepare Database
    echo "Prepare Database"
    if echo $DB_BACKEND | grep -i "^SQLITE" > /dev/null ; then
        #Permission on database folder if we use SQLite
        mkdir $INSTALL_DIR/database
        chown -R $APACHE_USER:$APACHE_USER $INSTALL_DIR/database/

    elif echo $DB_BACKEND | grep -i "^POSTGRESQL" > /dev/null ; then
        # Create the Database
        echo "We will remove existing Database"
        echo "Press Enter to continue"
        echo ""
        echo "sudo -u postgres dropdb $DATABASENAME"
        echo "Remove Existing Database if exists..."
        echo "Press Enter to continue"
        read TEMP
        sudo -u postgres dropdb $DATABASENAME
        # if [ `sudo -u postgres psql -qAt --list | egrep $DATABASENAME | wc -l` -eq 1 ]; then
        #     echo "sudo -u postgres dropdb $DATABASENAME"
        #     sudo -u postgres dropdb $DATABASENAME
        # fi
        echo "Create Database..."
        echo "sudo -u postgres createdb $DATABASENAME"
        sudo -u postgres createdb $DATABASENAME

        #CREATE ROLE / USER
        echo "Create Postgresql user $DB_USERNAME"
        #echo "sudo -u postgres createuser --no-createdb --no-createrole --no-superuser $DB_USERNAME"
        #sudo -u postgres createuser --no-createdb --no-createrole --no-superuser $DB_USERNAME
        echo "sudo -u postgres psql --command=\"create user $DB_USERNAME with password 'XXXXXXXXXX';\""
        sudo -u postgres psql --command="CREATE USER $DB_USERNAME with password '$DB_PASSWORD';"

        echo "Grant all privileges to user..."
        echo "sudo -u postgres psql --command=\"GRANT ALL PRIVILEGES on database $DATABASENAME to $DB_USERNAME;\""
        sudo -u postgres psql --command="GRANT ALL PRIVILEGES on database $DATABASENAME to $DB_USERNAME;"
    else
        # Create the Database
        echo "Remove Existing Database if exists..."
        if [ -d "/var/lib/mysql/$DATABASENAME" ]; then
            echo "mysql --user=$DB_USERNAME --password=$DB_PASSWORD -e 'DROP DATABASE $DATABASENAME;'"
            mysql --user=$DB_USERNAME --password=$DB_PASSWORD -e "DROP DATABASE $DATABASENAME;"
        fi
        echo "Create Database..."
        echo "mysql --user=$DB_USERNAME --password=$DB_PASSWORD -e 'CREATE DATABASE $DATABASENAME CHARACTER SET UTF8;'"
        mysql --user=$DB_USERNAME --password=$DB_PASSWORD -e "CREATE DATABASE $DATABASENAME CHARACTER SET UTF8;"
    fi
}


#Function to backup the data from the previous installation
func_backup_prev_install(){

    if [ -d "$INSTALL_DIR" ]; then
        # CDR-Stats is already installed
        echo ""
        echo "We detect an existing CDR-Stats Installation"
        echo "if you continue the existing installation will be removed!"
        echo ""
        echo "Press Enter to continue or CTRL-C to exit"
        read TEMP

        mkdir /tmp/old-cdr-stats_$DATETIME
        mv $INSTALL_DIR /tmp/old-cdr-stats_$DATETIME
        echo "Files from $INSTALL_DIR has been moved to /tmp/old-cdr-stats_$DATETIME"

        if [ `sudo -u postgres psql -qAt --list | egrep '^$DATABASENAME\|' | wc -l` -eq 1 ]; then
            echo "Run backup with postgresql..."
            sudo -u postgres pg_dump $DATABASENAME > /tmp/old-cdr-stats_$DATETIME.pgsqldump.sql
            echo "PostgreSQL Dump of database $DATABASENAME added in /tmp/old-cdr-stats_$DATETIME.pgsqldump.sql"
            echo "Press Enter to continue"
            read TEMP
        fi
    fi
}

#Function to install the code source
func_install_source(){

    #get CDR-Stats
    echo "Install CDR-Stats..."
    cd /usr/src/
    rm -rf cdr-stats
    mkdir /var/log/cdr-stats

    git clone -b $BRANCH git://github.com/Star2Billing/cdr-stats.git
    cd cdr-stats

    #Install Develop / Master
    if echo $BRANCH | grep -i "^develop" > /dev/null ; then
        git checkout -b develop --track origin/develop
    fi

    # Copy files
    cp -r /usr/src/cdr-stats/cdr_stats $INSTALL_DIR
}


#Function to install Python dependencies
func_install_pip_deps(){

    echo "func_install_pip_deps..."

    #Upgrade pip to latest (1.5)
    pip install pip --upgrade

    #For python 2.6 only
    pip install importlib

    case $DIST in
        'DEBIAN')
            #pip now only installs stable versions by default, so we need to use --pre option
            pip install --pre pytz
        ;;
        'CENTOS')
            pip install pytz
        ;;
    esac

    echo "Install basic requirements..."
    for line in $(cat /usr/src/cdr-stats/install/requirements/basic-requirements.txt | grep -v \#)
    do
        pip install $line
    done
    echo "Install Django requirements..."
    for line in $(cat /usr/src/cdr-stats/install/requirements/django-requirements.txt | grep -v \#)
    do
        pip install $line --allow-all-external --allow-unverified django-admin-tools
    done

    #Check Python dependencies
    func_check_dependencies

    echo "**********"
    echo "PIP Freeze"
    echo "**********"
    pip freeze
}

#Function to prepare settings_local.py
func_prepare_settings(){
    #Copy settings_local.py into cdr-stats dir
    cp /usr/src/cdr-stats/install/conf/settings_local.py $INSTALL_DIR

    #Update Secret Key
    echo "Update Secret Key..."
    RANDPASSW=`</dev/urandom tr -dc A-Za-z0-9| (head -c $1 > /dev/null 2>&1 || head -c 50)`
    sed -i "s/^SECRET_KEY.*/SECRET_KEY = \'$RANDPASSW\'/g"  $INSTALL_DIR/settings.py
    echo ""

    #Disable Debug
    sed -i "s/DEBUG = True/DEBUG = False/g"  $INSTALL_DIR/settings_local.py
    sed -i "s/TEMPLATE_DEBUG = DEBUG/TEMPLATE_DEBUG = False/g"  $INSTALL_DIR/settings_local.py

    if echo $DB_BACKEND | grep -i "^SQLITE" > /dev/null ; then
        # Setup settings_local.py for SQLite
        sed -i "s/'init_command/#'init_command/g"  $INSTALL_DIR/settings_local.py
    elif echo $DB_BACKEND | grep -i "^POSTGRESQL" > /dev/null ; then
        #Setup settings_local.py for POSTGRESQL
        sed -i "s/DATABASENAME/$DATABASENAME/"  $INSTALL_DIR/settings_local.py
        sed -i "s/DB_USERNAME/$DB_USERNAME/" $INSTALL_DIR/settings_local.py
        sed -i "s/DB_PASSWORD/$DB_PASSWORD/" $INSTALL_DIR/settings_local.py
        sed -i "s/DB_HOSTNAME/$DB_HOSTNAME/" $INSTALL_DIR/settings_local.py
        sed -i "s/DB_PORT/$DB_PORT/" $INSTALL_DIR/settings_local.py
    else
        # Setup settings_local.py for MySQL
        sed -i "s/'django.db.backends.postgresql_psycopg2'/'django.db.backends.mysql'/"  $INSTALL_DIR/settings_local.py
        sed -i "s/DATABASENAME/$DATABASENAME/"  $INSTALL_DIR/settings_local.py
        sed -i "s/DB_USERNAME/$DB_USERNAME/" $INSTALL_DIR/settings_local.py
        sed -i "s/DB_PASSWORD/$DB_PASSWORD/" $INSTALL_DIR/settings_local.py
        sed -i "s/DB_HOSTNAME/$DB_HOSTNAME/" $INSTALL_DIR/settings_local.py
        sed -i "s/DB_PORT/$DB_PORT/" $INSTALL_DIR/settings_local.py
    fi

    #Setup Timezone
    case $DIST in
        'DEBIAN')
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
}

#Function Prepare Settings for the CDR backend
func_prepare_backend_settings(){

    #Configure Backend Asterisk / Freeswitch etc...
    case $INSTALL_TYPE in
        'ASTERISK')
            DATABASENAME='asteriskcdr'
            MYSQLUSER='root'
            MYSQLPASSWORD='password'
            MYHOST='127.0.0.1'
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

            #Enable CDR-Stats for Asterisk
            sed -i "s/'freeswitch'/'asterisk'/g"  $INSTALL_DIR/settings_local.py

            #Configure CDR Import
            sed -i "s/MYSQL_IMPORT_CDR_DBNAME/$DATABASENAME/g"  $INSTALL_DIR/settings_local.py
            sed -i "s/MYSQL_IMPORT_CDR_TABLENAME/cdr/g"  $INSTALL_DIR/settings_local.py
            sed -i "s/MYSQL_IMPORT_CDR_HOST/$MYHOST/g"  $INSTALL_DIR/settings_local.py
            sed -i "s/MYSQL_IMPORT_CDR_USER/$MYSQLUSER/g"  $INSTALL_DIR/settings_local.py
            sed -i "s/MYSQL_IMPORT_CDR_PASSWORD/$MYSQLPASSWORD/g"  $INSTALL_DIR/settings_local.py
        ;;
        'FREESWITCH')
            echo "You will need to configure your CDR Connectors to access your CDRs"
            echo "After the installation please edit the config file: $INSTALL_DIR/settings_local.py"
            read TEMP
        ;;
    esac
}

#function to configure SELinux
func_configure_selinux(){
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
            setsebool -P httpd_can_network_connect 1
            setsebool -P httpd_can_network_connect_db 1
        ;;
    esac
}

#Function to configure Apache
func_configure_http_server(){
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

    #Restart HTTP Server
    service $APACHE_SERVICE restart
}

#Install Django CDR-stats
func_django_cdrstats_install(){
    cd $INSTALL_DIR/
    #Fix permission on python-egg
    mkdir $INSTALL_DIR/.python-eggs
    chown $APACHE_USER:$APACHE_USER $INSTALL_DIR/.python-eggs

    #upload audio files
    mkdir -p $INSTALL_DIR/usermedia/upload/audiofiles
    chown -R $APACHE_USER:$APACHE_USER $INSTALL_DIR/usermedia

    python manage.py syncdb --noinput
    python manage.py migrate
    echo "Create a super admin user..."
    python manage.py createsuperuser

    echo "Install Bower deps"
    python manage.py bower_install -- --allow-root

    #Collect static files from apps and other locations in a single location.
    python manage.py collectstatic --noinput

    #Install Celery & redis-server
    echo "Install Redis-server ..."
    func_install_redis_server
    #Redis is needed to load countries

    #Load Countries Dialcode
    python manage.py load_country_dialcode
}

#Function to install Frontend
func_install_frontend(){

    echo ""
    echo ""
    echo "We will now install CDR-Stats on your server"
    echo "============================================"
    echo ""

    #Prepare
    func_prepare_system_frontend

    #Backup
    func_backup_prev_install

    #Install Code Source
    func_install_source

    #Create and enable virtualenv
    func_setup_virtualenv

    #Install Pip Dependencies
    func_install_pip_deps

    #Prepare Settings
    func_prepare_settings

    #Prepare Backend Settings
    func_prepare_backend_settings

    #Configure Logs files and logrotate
    func_prepare_logger

    #Install Django cdr-stats
    func_django_cdrstats_install

    #Configure SELinux
    func_configure_selinux

    #Configure Apache
    func_configure_http_server

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
    echo "Yours,"
    echo "The Star2Billing Team"
    echo "http://www.star2billing.com and http://www.cdr-stats.org/"
    echo ""
    echo ""
}


#Function to install backend
func_install_backend() {
    echo ""
    echo "This will install CDR-Stats Backend, Celery & Redis on your server"
    echo "Press Enter to continue or CTRL-C to exit"
    read TEMP

    #Configure Logs files and logrotate
    func_prepare_logger

    #Create directory for pid file
    mkdir -p /var/run/celery

    #Install Celery & redis-server
    echo "Install Redis-server ..."
    func_install_redis_server

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
            if [ `stat -c "%a" $DIR` -ge 777 ] ; then
                echo "$DIR has read write permissions."
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

    echo ""
    echo ""
    echo "**************************************************************"
    echo "Congratulations, CDR-Stats Backend is now installed"
    echo "**************************************************************"
    echo ""
    echo "Yours,"
    echo "The Star2Billing Team"
    echo "http://www.star2billing.com and http://www.cdr-stats.org/"
    echo ""
    echo ""
}

#Function to install Standalone Backend
func_install_standalone_backend(){

    echo ""
    echo "This will install the CDR-backend without configuring Apache, etc..."
    read TEMP

    func_prepare_system_common

    #Install Code Source
    func_install_source

    #Install Pip Dependencies
    func_install_pip_deps

    #Prepare Settings
    func_prepare_settings

    #Prepare Backend Settings
    func_prepare_backend_settings

    #Configure Logs files and logrotate
    func_prepare_logger

    #Install CDR-Stats Backend
    func_install_backend
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
                wget https://redis.googlecode.com/files/redis-2.6.4.tar.gz
                tar -zxf redis-2.6.4.tar.gz
                cd redis-2.6.4
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
        ;;
    esac
}

#Configure Logs files and logrotate
func_prepare_logger() {
    touch /var/log/cdr-stats/cdr-stats.log
    touch /var/log/cdr-stats/cdr-stats-db.log
    touch /var/log/cdr-stats/err-apache-cdr-stats.log
    chown -R $APACHE_USER:$APACHE_USER /var/log/cdr-stats

    rm /etc/logrotate.d/cdr_stats
    touch /etc/logrotate.d/cdr_stats
    echo '
/var/log/cdr-stats/*.log {
        daily
        rotate 10
        size = 50M
        missingok
        compress
    }
'  > /etc/logrotate.d/cdr_stats

    logrotate /etc/logrotate.d/cdr_stats
}
