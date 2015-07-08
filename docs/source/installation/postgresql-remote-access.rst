
.. _configure-postgresql-remote-access:

Configure Postgresql for Remote Access
--------------------------------------

2.1 First backup your conf files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Backup postgresql.conf & pg_hba.conf::

    cp /etc/postgresql/9.4/main/postgresql.conf /etc/postgresql/9.4/main/postgresql.conf.bkup
    cp /etc/postgresql/9.4/main/pg_hba.conf /etc/postgresql/9.4/main/pg_hba.conf.bkup


2.2 Allow TCP/IP socket
~~~~~~~~~~~~~~~~~~~~~~~

Edit the PostgreSQL configuration file, using a text editor such as vi.

Configure PostgreSQL to listen for remote connections::

    sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/9.4/main/postgresql.conf


2.3 Enable client authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure PostgreSQL to accept remote connections (from any host on your network)::

    cat >> /etc/postgresql/9.4/main/pg_hba.conf <<EOF
    # Accept all IPv4 connections
    host    all         all         <SWITCH_IP>/24             md5
    EOF

Make sure you replace <SWITCH_IP>/24 with your actual network IP address range.

If you want to accept CDR from only from one IP address, then enter the IP in switch, followed by /32, e.g. <SWITCH_IP>/32


2.4 Restart PostgreSQL Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Restart PostgreSQL for the changes to take effect::

    /etc/init.d/postgresql restart


2.5 Setup firewall Iptables
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Make sure iptables is not blocking communication, open port 5432::

    iptables -A INPUT -p tcp -s 0/0 --sport 1024:65535 -d <SWICH_IP>  --dport 5432 -m state --state NEW,ESTABLISHED -j ACCEPT
    iptables -A OUTPUT -p tcp -s <SWICH_IP> --sport 5432 -d 0/0 --dport 1024:65535 -m state --state ESTABLISHED -j ACCEPT

Restart firewall::

    /etc/init.d/iptables restart


2.6 Test your setup
~~~~~~~~~~~~~~~~~~~

In order to test, you will need to install PostgreSQL client, on Debian you can install as follows::

    apt-get install postgresql-client

For CentOS::

    yum install postgresql

Use psql command from client system. Connect to remote server using IP address and login using vivek username and sales database, enter::

    $ psql -h <POSTGRESQL_IP> -U USERNAME -d CDRPUSHER_DBNAME


Replace POSTGRESQL_IP, USERNAME and CDRPUSHER_DBNAME, with the one from your CDR-Stats server.

Check `settings_local.py` for the username and password.
