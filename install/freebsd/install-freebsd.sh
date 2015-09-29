#!/bin/sh

###### Customize settings ######
INSTALL_DIR=/usr/local/cdr_stats
DATABASENAME=cdrstats
DB_USERNAME=cdrstats
DB_PASSWORD=secret
DB_HOSTNAME=localhost
DB_PORT=3306
APACHE_USER=www
################################

ESC_INSTALL_DIR=$(echo $INSTALL_DIR | sed 's/\//\\\//g')
export LC_ALL="en_US.UTF-8"


step_mysql()
{
  pkg install -y mysql55-server
  echo 'mysql_enable="YES"' >> /etc/rc.conf
  /usr/local/etc/rc.d/mysql-server start

  mysql -e "CREATE DATABASE $DATABASENAME CHARACTER SET UTF8;"
  mysql -e "GRANT ALL PRIVILEGES ON $DATABASENAME.* TO $DB_USERNAME@localhost IDENTIFIED BY '$DB_PASSWORD'"
}

step_git_mercurial()
{
  pkg install -y git mercurial
}

step_apache()
{
  pkg install -y apache24 ap24-mod_wsgi3
  echo 'apache24_enable="YES"' >> /etc/rc.conf

  sed "s/INSTALL_DIR/$ESC_INSTALL_DIR/g" install-freebsd.vhost > /usr/local/etc/apache24/Includes/cdr-stats.conf
}

step_redis()
{
  pkg install -y redis
  echo 'redis_enable="YES"' >> /etc/rc.conf
  mkdir -p /var/lib/redis
  /usr/local/etc/rc.d/redis start
}

step_user()
{
  pw useradd cdr_stats -c CDR-Stats
}

step_prerequirements()
{
  pkg install -y python py27-pip py27-sqlite3
  pip install virtualenv
  pip install virtualenvwrapper
  pip install distribute
  pip install versiontools>=1.3.1  # FreeBSD issue
}

step_github()
{
  mkdir -p /usr/local/src $INSTALL_DIR
  cd /usr/local/src
  git clone git://github.com/cdr-stats/cdr-stats.git
  cp -r /usr/local/src/cdr-stats/cdr_stats/* $INSTALL_DIR/
}

step_requirements()
{
  for line in $(cat /usr/local/src/cdr-stats/requirements/basic.txt | grep -v \#) ; do
    pip install $line
  done

  for line in $(cat /usr/local/src/cdr-stats/requirements/django.txt | grep -v \#) ; do
    pip install $line
  done
}

step_config()
{
  sed "
s/DEBUG = True/DEBUG = False/g;
s/TEMPLATE_DEBUG = DEBUG/TEMPLATE_DEBUG = False/g;
s/'django.db.backends.postgresql_psycopg2'/'django.db.backends.mysql'/;
s/DATABASENAME/$DATABASENAME/;
s/DB_USERNAME/$DB_USERNAME/;
s/DB_PASSWORD/$DB_PASSWORD/;
s/DB_HOSTNAME/$DB_HOSTNAME/;
s/DB_PORT/$DB_PORT/" /usr/local/src/cdr-stats/install/conf/settings_local.py > $INSTALL_DIR/settings_local.py
}

step_logs()
{
  mkdir -p /var/log/cdr-stats
  touch /var/log/cdr-stats/cdr-stats.log
  touch /var/log/cdr-stats/cdr-stats-db.log
  touch /var/log/cdr-stats/err-apache-cdr-stats.log
  chown -R ${APACHE_USER}:${APACHE_USER} /var/log/cdr-stats
}

step_tune()
{
  OLD_DIR=$cwd
  cd $INSTALL_DIR

  mkdir .python-eggs
  chown ${APACHE_USER}:${APACHE_USER} .python-eggs
  mkdir database

  #upload audio files
  mkdir -p usermedia/upload/audiofiles
  chown -R ${APACHE_USER}:${APACHE_USER} usermedia

  sed -i.bak "s/\/usr\/share\/cdr_stats/$ESC_INSTALL_DIR/" django.wsgi
  sed -i.bak "s/# 'init_command'/'init_command'/;s/'autocommit'/# 'autocommit'/" settings_local.py

  python manage.py syncdb --noinput
  python manage.py migrate
  python manage.py createsuperuser
  python manage.py collectstatic
}

step_run()
{
  /usr/local/etc/rc.d/apache24 start

  cp /usr/local/src/cdr-stats/install/celery-init/debian/etc/init.d/cdr-stats-celeryd /usr/local/etc/rc.d
  /usr/local/etc/rc.d/cdr-stats-celeryd restart
}


trap "SKIP=1" 2

for STEP in $(grep ^step_ $0 | sed -E 's/\(\)//'); do
  SKIP=0
  echo "### $STEP - press Enter to run, Ctrl+C to skip."
  read CHOICE
  if [ $SKIP = 0 ]; then
    eval ${STEP}
  fi
  echo "### $STEP - ended."
  echo
done
