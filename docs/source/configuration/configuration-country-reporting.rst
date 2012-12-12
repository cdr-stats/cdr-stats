.. _configuration-country-reporting:

Country Reporting
=================

CDR-Stats is able to identify the destination country of the call. This is a
useful fraud prevention measure, so that calls to unexpected destinations
are immediately apparent. Places that should not be called should be added
in the Blacklist in the admin section so that these destinations are
highlighted in the call data records.

However, in order to get accurate reporting, the call detail records have to
be in international format, e.g. in the USA, this means 11 digit numbers,
beginning with a 1, and for other countries, the numbers called should be
prefixed with the international dial code.

There is a facility for manipulating the dialled digits reported in the call
detail records, as well as identifying calls as internal calls. This is done
in the "general" section of /usr/share/cdr-stats/settings_local.py.

1. Prefix Limits
----------------

PREFIX_LIMIT_MIN & PREFIX_LIMIT_MAX are used to determine how many digits are used to match against the dialcode prefix database, e.g::

    PREFIX_LIMIT_MIN = 2
    PREFIX_LIMIT_MAX = 5

2. Phone Number Length
----------------------

If a phone number has less significant digits than PN_MIN_DIGITS it will be considered an extension::

    PN_MIN_DIGITS = 6
    PN_MAX_DIGITS = 9

*NB The Number of significant digits does not include national (0) or international dialing codes (00 or 011), or where 9 is pressed for an outside line.*

3. Adding Country Code
----------------------
If a phone number has more digits than PN_DIGITS_MIN but less than PN_DIGITS_MAX then the phone number will be considered as local or national call and the LOCAL_DIALCODE will be added::

    LOCAL_DIALCODE = 1

Set the dialcode of your country e.g. 44 for UK, 1 for US

4. Prefixes to Ignore
---------------------

List of prefixes to ignore, these prefixes are removed from the phone number prior to analysis. In cases where
customers dial 9 for an outside line, 9, 90 or 900 may need to be removed as well to ensure accurate reporting::

    PREFIX_TO_IGNORE = "+,0,00,000,0000,00000,011,55555,99999"

Examples
--------

So for the USA, to cope with 10 or 11 digit dialling, PN_MAX_DIGITS would be set to 10, and LOCAL_DIALCODE set to 1. Thus 10 digit numbers would have a 1 added, but 11 digit numbers are left untouched.

In the UK, the number of significant digits is either 9 or 10 after the "0" trunk code. So to ensure that all UK numbers had 44 prefixed to them and the single leading 0 removed, the prefixes to ignore would include 0, the PN_MAX_DIGITS would be set to 10, and the LOCAL_DIALCODE would be 44.

In Spain, where there is no "0" trunk code, and the length of all numbers is 9, then the PN_MAX_DIGITS  would be set to 9, and the LOCAL_DIALCODE set to 34.

NB: After changing this file, then both celery and apache should be restarted.
