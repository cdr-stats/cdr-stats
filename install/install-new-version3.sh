
#------------------------------
#       Postgresql 9.4
#------------------------------

# https://wiki.postgresql.org/wiki/Apt/FAQ#I_want_to_try_the_beta_version_of_the_next_PostgreSQL_release

#Snipcode
#http://www.snip2code.com/Snippet/82849/Install-Postgres-9-4

# remove existing 9.3 installation
/etc/init.d/postgresql stop
apt-get --force-yes -fuy remove --purge postgresql postgresql-9.1 postgresql-client

# install 9.4
apt-get install python-software-properties
add-apt-repository 'deb http://apt.postgresql.org/pub/repos/apt/ precise-pgdg main 9.4'
apt-get update
apt-get install -y postgresql-client-9.4 postgresql-9.4

# update the postgres config files
/bin/bash -c "cat <<EOF > /etc/postgresql/9.4/main/pg_hba.conf
local   all             postgres                                trust
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
EOF"

initdb

# restart
/etc/init.d/postgresql restart


#------------------------------
#       InfluxDB
#------------------------------

# http://influxdb.com/docs/v0.8/introduction/installation.html

# for 64-bit systems
wget http://s3.amazonaws.com/influxdb/influxdb_latest_amd64.deb
dpkg -i influxdb_latest_amd64.deb

/etc/init.d/influxdb start
