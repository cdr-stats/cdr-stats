
.. _install-cdr-stats:

Install CDR-Stats
=================


.. _install-download:

Download and Install CDR-Stats
------------------------------

Our install script support Debian 7.x and Debian 8.x, we recommend the latest version of Debian.

Install CDR-Stats *Master* branch:

This will copy and un the `master` install script::

    cd /usr/src/ ; rm install-cdr-stats.sh ; wget --no-check-certificate https://raw.github.com/areski/cdr-stats/master/install/install-cdr-stats.sh -O install-cdr-stats.sh ; bash install-cdr-stats.sh


During the installation, a number of self explanatory questions will be asked, including the root username and password.

On completion CDR-Stats will be ready to use once it is configured to your requirements in settings_local.py as described in the next section, and the CDR-Pusher is installed, usually to your switch, to send CDR to CDR-Stats.


.. _install-config-file:

Config file - settings.py & settings_local.py
---------------------------------------------

The main config file for CDR-Stats is located at `/usr/share/cdrstats/cdr_stats/settings_local.py`

Before importing CDR, there are some settings that need to be changed to suit your location.


Email Backend
~~~~~~~~~~~~~

Configure these settings to register to your SMTP server for sending outbound mail.


Allowed Hosts
~~~~~~~~~~~~~

Normally, this IP address will be configured correctly as part of the installation process, however if the IP address changes, or if you are accessing via another IP, e.g. port forwarding through a firewall or you use an FQDN, the additional IP addresses via which you access CDR-Stats will need to be added here enclosed in single ‘quotation’ marks and separated with a comma.


General
~~~~~~~

The general settings deal with how the dialled digits are treated in order to normalise them for matching to a rate.

PHONENUMBER_PREFIX_LIMIT_MIN & PHONENUMBER_PREFIX_LIMIT_MAX are used to determine how many digits are used to match against the dialcode prefix database, e.g::

    PHONENUMBER_PREFIX_LIMIT_MIN = 2
    PHONENUMBER_PREFIX_LIMIT_MAX = 5

If  a phone number has less digits  than PHONENUMBER_MIN_DIGITS it will be considered an extension::

    PHONENUMBER_MIN_DIGITS = 6
    PHONENUMBER_MAX_DIGITS = 9

If a phone number has more digits than PHONENUMBER_DIGITS_MIN but less than PHONE_DIGITS_MAX then the phone number will be considered as local or national call and the LOCAL_DIALCODE will be added::

    LOCAL_DIALCODE = 1

Set the dialcode of your country (44 for UK, 1 for US)::

    PREFIX_TO_IGNORE = "+,0,00,000,0000,00000,011,55555,99999"

List of prefixes to ignore, these prefixes are removed from the phone number prior to analysis.


Country Examples
~~~~~~~~~~~~~~~~

So for the USA, to cope with 10 or 11 digit dialling, PHONENUMBER_MAX_DIGITS would be set to 10, and LOCAL_DIALCODE set to 1. Thus 10 digit numbers would have a 1 added, but 11 digit numbers are left untouched.

In the UK, the number of significant digits is either 9 or 10 after the “0” trunk code. So to ensure that all UK numbers had 44 prefixed to them and the single leading 0 removed, the prefixes to ignore would include 0, the PHONENUMBER_MAX_DIGITS would be set to 10, and the LOCAL_DIALCODE would be 44.

In Spain, where there is no “0” trunk code, and the length of all numbers is 9, then the PHONENUMBER_MAX_DIGITS  would be set to 9, and the LOCAL_DIALCODE set to 34.

When any changes are made to this file, then Celery should be restarted to apply the changes.
