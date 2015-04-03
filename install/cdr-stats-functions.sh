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
CONFIG_DIR='/usr/share/cdrstats/cdr_stats'
WELCOME_DIR='/var/www/cdr-stats'
DATABASENAME='cdrstats_db'
CDRPUSHER_DBNAME="cdr-pusher"
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
BRANCH='develop'
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

    #Check django-postgres
    grep_pip=`pip freeze| grep django-postgres`
    if echo $grep_pip | grep -i "django-postgres" > /dev/null ; then
        echo "OK : django-postgres installed..."
    else
        echo "Error : django-postgres not installed..."
        exit 1
    fi

    echo ""
    echo "Python dependencies successfully installed!"
    echo ""
}


#Function to install Dependencies
func_install_dependencies(){

    #python setup tools
    echo "Install Dependencies and python modules..."

    case $DIST in
        'DEBIAN')
            chk=`grep "backports" /etc/apt/sources.list|wc -l`
            if [ $chk -lt 1 ] ; then
                echo "Setup new sources.list entries"
                #Used by Node.js
                echo "deb http://ftp.us.debian.org/debian wheezy-backports main" >> /etc/apt/sources.list
                #Used by PostgreSQL
                echo 'deb http://apt.postgresql.org/pub/repos/apt/ wheezy-pgdg main' >> /etc/apt/sources.list.d/pgdg.list
                wget --no-check-certificate --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
            fi
            apt-get update
            export LANGUAGE=en_US.UTF-8
            export LANG=en_US.UTF-8
            export LC_ALL=en_US.UTF-8
            locale-gen en_US.UTF-8

            # dpkg-reconfigure locales
            # apt-get -y install --reinstall language-pack-en

            apt-get -y remove apache2.2-common apache2
            apt-get -y install sudo curl

            #Install Postgresql
            apt-get -y install libpq-dev
            apt-get -y install postgresql-9.4 postgresql-contrib-9.4
            pg_createcluster 9.4 main --start
            /etc/init.d/postgresql start

            apt-get -y install python-software-properties
            apt-get -y install python-setuptools python-dev build-essential
            apt-get -y install nginx supervisor
            apt-get -y install git-core mercurial gawk cmake
            apt-get -y install python-pip
            #Install Node.js & NPM
            apt-get -y install nodejs-legacy
            curl -sL https://deb.nodesource.com/setup | bash -
            apt-get install -y nodejs
            #Memcached
            apt-get -y install memcached
        ;;
        'CENTOS')
            yum -y groupinstall "Development Tools"
            yum -y install git sudo cmake
            yum -y install python-setuptools python-tools python-devel mercurial memcached
            yum -y install mlocate vim git wget
            yum -y install policycoreutils-python

            # install Node & npm
            yum -y --enablerepo=epel install npm

            #Install, configure and start nginx
            yum -y install --enablerepo=epel nginx
            chkconfig --levels 235 nginx on
            service nginx start

            #Install & Start PostgreSQL 9.1
            #CentOs
            rpm -ivh http://yum.pgrpms.org/9.1/redhat/rhel-6-x86_64/pgdg-centos91-9.1-4.noarch.rpm
            #Redhad
            #rpm -ivh http://yum.pgrpms.org/9.1/redhat/rhel-6-x86_64/pgdg-redhat91-9.1-5.noarch.rpm
            yum -y install postgresql91-server postgresql91-devel
            chkconfig --levels 235 postgresql-9.1 on
            service postgresql-9.1 initdb
            ln -s /usr/pgsql-9.1/bin/pg_config /usr/bin
            ln -s /var/lib/pgsql/9.1/data /var/lib/pgsql
            ln -s /var/lib/pgsql/9.1/backups /var/lib/pgsql
            sed -i "s/ident/md5/g" /var/lib/pgsql/data/pg_hba.conf
            sed -i "s/ident/md5/g" /var/lib/pgsql/9.1/data/pg_hba.conf
            service postgresql-9.1 restart
        ;;
    esac


    echo ""
    echo "easy_install -U setuptools pip distribute"
    easy_install -U setuptools pip distribute

    # install Bower
    npm install -g bower

    #Create CDRStats User
    echo "Create CDRStats User/Group : $CDRSTATS_USER"
    useradd $CDRSTATS_USER --user-group --system --no-create-home
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

    git clone -b $BRANCH git://github.com/areski/cdr-stats.git
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
    for line in $(cat /usr/src/cdr-stats/install/requirements/basic-requirements.txt | grep -v '^#' | grep -v '^$')
    do
        echo "pip install $line"
        pip install $line
    done
    echo "Install Django requirements..."
    for line in $(cat /usr/src/cdr-stats/install/requirements/django-requirements.txt | grep -v '^#' | grep -v '^$')
    do
        echo "pip install $line --allow-all-external --allow-unverified django-admin-tools"
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
    cp /usr/src/cdr-stats/install/conf/settings_local.py $CONFIG_DIR

    #Update Secret Key
    echo "Update Secret Key..."
    RANDPASSW=`</dev/urandom tr -dc A-Za-z0-9| (head -c $1 > /dev/null 2>&1 || head -c 50)`
    sed -i "s/^SECRET_KEY.*/SECRET_KEY = \'$RANDPASSW\'/g"  $CONFIG_DIR/settings.py
    echo ""

    #Disable Debug
    sed -i "s/DEBUG = True/DEBUG = False/g"  $CONFIG_DIR/settings_local.py
    sed -i "s/TEMPLATE_DEBUG = DEBUG/TEMPLATE_DEBUG = False/g"  $CONFIG_DIR/settings_local.py

    #Setup settings_local.py for POSTGRESQL
    sed -i "s/DATABASENAME/$DATABASENAME/"  $CONFIG_DIR/settings_local.py
    sed -i "s/DB_USERNAME/$DB_USERNAME/" $CONFIG_DIR/settings_local.py
    sed -i "s/DB_PASSWORD/$DB_PASSWORD/" $CONFIG_DIR/settings_local.py
    sed -i "s/DB_HOSTNAME/$DB_HOSTNAME/" $CONFIG_DIR/settings_local.py
    sed -i "s/DB_PORT/$DB_PORT/" $CONFIG_DIR/settings_local.py

    # settings for CDRPUSHER_DBNAME
    sed -i "s/CDRPUSHER_DBNAME/$CDRPUSHER_DBNAME/"  $CONFIG_DIR/settings_local.py

    #Setup Timezone
    case $DIST in
        'DEBIAN')
            #Get TZ
            ZONE=$(head -1 /etc/timezone)
        ;;
        'CENTOS')
            #Get TZ
            . /etc/sysconfig/clock
            echo ""
            echo "We will now add port $HTTP_PORT  and port 80 to your Firewall"
            echo "Press Enter to continue or CTRL-C to exit"
            read TEMP
        ;;
    esac

    #Set Timezone in settings_local.py
    sed -i "s@Europe/Madrid@$ZONE@g" $CONFIG_DIR/settings_local.py

    #Fix Iptables
    case $DIST in
        'CENTOS')
            #Add http port
            iptables -I INPUT 2 -p tcp -m state --state NEW -m tcp --dport $HTTP_PORT -j ACCEPT
            iptables -I INPUT 3 -p tcp -m state --state NEW -m tcp --dport 80 -j ACCEPT

            service iptables save

            #Selinux to allow apache to access this directory
            chcon -Rv --type=httpd_sys_content_t /usr/share/virtualenvs/cdr-stats/
            chcon -Rv --type=httpd_sys_content_t $INSTALL_DIR/usermedia
            semanage port -a -t http_port_t -p tcp $HTTP_PORT
            #Allowing Apache to access Redis port
            semanage port -a -t http_port_t -p tcp 6379
        ;;
    esac

    IFCONFIG=`which ifconfig 2>/dev/null||echo /sbin/ifconfig`
    IPADDR=`$IFCONFIG eth0|gawk '/inet addr/{print $2}'|gawk -F: '{print $2}'`
    if [ -z "$IPADDR" ]; then
        clear
        echo "we have not detected your IP address automatically!"
        echo "Please enter your IP address manually:"
        read IPADDR
        echo ""
    fi
    #Update Authorize local IP
    sed -i "s/SERVER_IP_PORT/$IPADDR:$HTTP_PORT/g" $CONFIG_DIR/settings_local.py
    sed -i "s/#'SERVER_IP',/'$IPADDR',/g" $CONFIG_DIR/settings_local.py
    sed -i "s/SERVER_IP/$IPADDR/g" $CONFIG_DIR/settings_local.py
}


#Configure Logs files and logrotate
func_prepare_logger() {
    touch /var/log/cdr-stats/cdr-stats.log
    touch /var/log/cdr-stats/cdr-stats-db.log
    chown -R $CDRSTATS_USER:$CDRSTATS_USER /var/log/cdr-stats

    echo "Install Logrotate..."
    # First delete to avoid error when running the script several times.
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


#Create PGSQL
func_create_pgsql_database(){

    # Create the Database
    echo "We will remove existing Database"
    echo "Press Enter to continue"
    read TEMP
    echo "sudo -u postgres dropdb $DATABASENAME"
    sudo -u postgres dropdb $DATABASENAME
    # echo "Remove Existing Database if exists..."
    #if [ `sudo -u postgres psql -qAt --list | egrep $DATABASENAME | wc -l` -eq 1 ]; then
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
    echo "sudo -u postgres psql --command=\"create user $DB_USERNAME with password 'XXXXXXXXXXXX';\""
    sudo -u postgres psql --command="CREATE USER $DB_USERNAME with password '$DB_PASSWORD';"

    echo "Grant all privileges to user..."
    sudo -u postgres psql --command="GRANT ALL PRIVILEGES on database $DATABASENAME to $DB_USERNAME;"
}

#NGINX / SUPERVISOR
func_nginx_supervisor(){

    #Leave virtualenv
    deactivate
    #Install Supervisor
    pip install supervisor

    #Configure and Start supervisor
    case $DIST in
        'DEBIAN')
            cp /usr/src/cdr-stats/install/supervisor/gunicorn_cdrstats.conf /etc/supervisor/conf.d/
            cp /usr/src/cdr-stats/install/supervisor/debian/supervisord /etc/init.d/supervisor
            chmod +x /etc/init.d/supervisor
        ;;
        'CENTOS')
            cp /usr/src/cdr-stats/install/supervisor/centos/supervisord /etc/init.d/supervisor
            chmod +x /etc/init.d/supervisor
            chkconfig --levels 235 supervisor on
            cp /usr/src/cdr-stats/install/supervisor/centos/supervisord.conf /etc/supervisord.conf
            mkdir -p /etc/supervisor/conf.d
            cp /usr/src/cdr-stats/install/supervisor/gunicorn_cdr_stats.conf /etc/supervisor/conf.d/
            mkdir /var/log/supervisor/
        ;;
    esac
    /etc/init.d/supervisor stop
    sleep 2
    /etc/init.d/supervisor start
}

#CELERY SUPERVISOR
func_celery_supervisor(){

    #Leave virtualenv
    deactivate
    #Install Supervisor
    pip install supervisor

    #Configure and Start supervisor
    case $DIST in
        'DEBIAN')
            cp /usr/src/cdr-stats/install/supervisor/celery_cdrstats.conf /etc/supervisor/conf.d/
            cp /usr/src/cdr-stats/install/supervisor/debian/supervisord /etc/init.d/supervisor
            chmod +x /etc/init.d/supervisor
        ;;
        'CENTOS')
            cp /usr/src/cdr-stats/install/supervisor/centos/supervisord /etc/init.d/supervisor
            chmod +x /etc/init.d/supervisor
            chkconfig --levels 235 supervisor on
            cp /usr/src/cdr-stats/install/supervisor/centos/supervisord.conf /etc/supervisord.conf
            mkdir -p /etc/supervisor/conf.d
            cp /usr/src/cdr-stats/install/supervisor/celery_cdrstats.conf /etc/supervisor/conf.d/
            mkdir /var/log/supervisor/
        ;;
    esac
    /etc/init.d/supervisor stop
    sleep 2
    /etc/init.d/supervisor start
}


#Install Django CDR-stats
func_django_cdrstats_install(){
    cd $INSTALL_DIR/
    python manage.py syncdb --noinput
    python manage.py migrate

    clear
    echo ""
    echo "Create a super admin user..."
    python manage.py createsuperuser

    echo "Install Bower deps"
    python manage.py bower_install -- --allow-root

    echo "Collects the static files"
    python manage.py collectstatic --noinput

    #Load Countries Dialcode
    python manage.py load_country_dialcode
}


#Function to install Frontend
func_install_frontend(){

    echo ""
    echo "We will now install CDR-Stats..."
    echo ""

    #Install Depedencies
    func_install_dependencies

    #Install Redis
    func_install_redis

    #Create and enable virtualenv
    func_setup_virtualenv

    #Backup
    func_backup_prev_install

    #Install Code Source
    func_install_source

    #Install Pip Dependencies
    func_install_pip_deps

    #Prepare Settings
    func_prepare_settings

    #Create PostgreSQL Database
    func_create_pgsql_database

    #Install Django cdr-stats
    func_django_cdrstats_install

    #Install Nginx / Supervisor
    func_nginx_supervisor

    #Configure Logs files and logrotate
    func_prepare_logger

    echo ""
    echo "************************************************************"
    echo "Congratulations, CDR-Stats Web Application is now installed!"
    echo "************************************************************"
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
    echo "************************************************************"
    echo ""
}


#Function to install backend
func_install_backend() {
    echo ""
    echo "This will install CDR-Stats Backend, Celery & Redis on your server"
    echo "Press Enter to continue or CTRL-C to exit"
    read TEMP

    #Create directory for pid file
    mkdir -p /var/run/celery

    #Install Celery & redis-server
    func_install_redis

    echo "Install Celery via supervisor..."
    func_celery_supervisor

    case $DIST in
        'DEBIAN')
            #Check permissions on /dev/shm to ensure that celery can start and run for openVZ.
            DIR="/dev/shm"
            echo "Checking the permissions for $dir"
            stat $DIR
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
    esac

    echo ""
    echo "**********************************************************"
    echo "Congratulations, CDR-Stats Backend is now installed!"
    echo "**********************************************************"
    echo ""
    echo "Thank you for installing CDR-Stats"
    echo "Yours"
    echo "The Star2Billing Team"
    echo "http://www.star2billing.com and http://www.cdr-stats.org/"
    echo ""
    echo "*********************************************************"
    echo ""
}


#Install Redis
func_install_redis() {
    echo "Install Redis-server ..."
    case $DIST in
        'DEBIAN')
            echo "deb http://packages.dotdeb.org wheezy all" > /etc/apt/sources.list.d/dotdeb.list
            echo "deb-src http://packages.dotdeb.org wheezy all" >> /etc/apt/sources.list.d/dotdeb.list
            wget --no-check-certificate --quiet -O - http://www.dotdeb.org/dotdeb.gpg | apt-key add -
            apt-get update
            apt-get -y install redis-server
            /etc/init.d/redis-server restart
        ;;
        'CENTOS')
            yum -y --enablerepo=epel install redis
            chkconfig --add redis
            chkconfig --level 2345 redis on
            /etc/init.d/redis start
        ;;
    esac
}
