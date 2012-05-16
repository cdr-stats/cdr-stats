.. _freeswitch-installation-overview:

============================
Installation with FreeSWITCH
============================

.. _freeswitch-installation-via-script:

Installation via Script
=======================

On an existing installation of Freeswitch, mod_cdr_mongodb needs to be 
compiled into Freeswitch. This procedure is described at 
http://wiki.freeswitch.org/wiki/Mod_cdr_mongodb

After having recompiled Freeswitch to support MongoDB CDR, make the 
following changes:

In freeswitch/conf/autoload_configs/cdr_mongodb.conf.xml 

Change::

    <param name="log-b-leg" value="false"/>
    
To::

    <param name="log-b-leg" value="true"/>


Change::
    
    <param name="namespace" value="test.cdr"/>

To::

    <param name="namespace" value="freeswitch_cdr.cdr"/> 


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
This script is intended to be run on a fresh Ubuntu 12.04 LTS or CentOS 6.2 installation::

    $ wget –no-check-certificate https://raw.github.com/Star2Billing/cdr-stats/master/install/install-all-cdr-stats-freeswitch.sh -O install-all-cdr-stats-freeswitch.sh
    $
    $ bash install-all-cdr-stats-freeswitch.sh
    
The install routine will ask a number of questions, all of which are self explanatory.
