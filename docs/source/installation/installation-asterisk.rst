.. _asterisk-installation-overview:

==========================
Installation with Asterisk
==========================

.. _asterisk-installation-via-script:

Installation via Script
=======================

Before commencing installation, it is necessary that Asterisk is configured to
write CDR to a MySQL database. If this has not been done already, there are
some resources to configure Asterisk to write its CDR records to MySQL at
http://www.asteriskdocs.org/en/3rd_Edition/asterisk-book-html-chunk/asterisk-SysAdmin-SECT-1.html

It is wise to take a backup of the CDR database. A note needs to be taken of
the CDR database name, the CDR table, as well as the MySQL root password as
this will be required during the installation of CDR-Stats.

Run the following commands at the console::

    $ wget –no-check-certificate https://raw.github.com/areski/cdr-stats/master/install/install-cdr-stats-asterisk.sh -O install-cdr-stats-asterisk.sh
    $
    $ bash ./install-cdr-stats-asterisk.sh


The install routine will ask a number of questions, all of which are self explanatory.

Note that CDR-Stats can be installed on the same server as Asterisk, or on a separate server
connecting remotely to the Asterisk CDR database.
