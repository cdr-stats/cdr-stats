.. _freeswitch-installation-overview:

============================
Installation with FreeSWITCH
============================

.. _freeswitch-installation-via-script:

Installation via Script
=======================

On an existing installation of Freeswitch, mod_cdr_sqlite needs to be compiled
into Freeswitch. This procedure is described at https://wiki.freeswitch.org/wiki/Mod_cdr_sqlite

After having recompiled Freeswitch to support Sqlite CDR, make the following changes:

In freeswitch/conf/autoload_configs/cdr_sqlite.conf.xml

Change::

    <param name="legs" value="a"/>

To::

    <param name="legs" value="ab"/>


Then reload the Freeswitch configuration.


**Now run the following commands at the console**::

    $ wget –no-check-certificate https://raw.github.com/Star2Billing/cdr-stats/master/install/install-cdr-stats.sh -O install-cdr-stats.sh
    $
    $ bash install-cdr-stats.sh

When prompted, chose the option to install the Freeswitch version.

The install routine will ask a number of questions, all of which are self explanatory.


.. _freeswitch-installation-new-server:

Installation on New Server
==========================

Another script is available to install Freeswitch along with CDR-Stats.
This script is intended to be run on a fresh Debian 7.X or CentOS 6.X installation::

    $ wget –no-check-certificate https://raw.github.com/Star2Billing/cdr-stats/master/install/install-all-cdr-stats-freeswitch.sh -O install-all-cdr-stats-freeswitch.sh
    $
    $ bash install-all-cdr-stats-freeswitch.sh

The install routine will ask a number of questions, all of which are self explanatory.
