# -*- coding: utf-8 -*-
#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2012 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from dajaxice.decorators import dajaxice_register
from dajax.core import Dajax

from cdr_alert.models import Whitelist, Blacklist
from cdr.functions_def import remove_prefix,\
    prefix_list_string, get_country_id
from country_dialcode.models import Country, Prefix


@login_required
@dajaxice_register
def add_blacklist_country(request, country_id):
    dajax = Dajax()

    try:
        country = Country.objects.get(id=int(country_id))
        country_id = country.id
        prefix_list =\
            Prefix.objects.values('prefix').filter(country_id=country_id)
        for prefix in prefix_list:

            for key, value in prefix.iteritems():
                rec_count = Blacklist.objects.filter(user=request.user,
                                                     phonenumber_prefix=int(value),
                                                     country_id=country_id).count()

                # No duplicate record, so insert
                if rec_count == 0:
                    blacklist = Blacklist.objects.create(
                        user=request.user,
                        phonenumber_prefix=int(value),
                        country_id=country_id,
                    )

        result = '<div class="alert alert-success">Alert : (%s) has been successfully added in blacklist !!</div>' % (country.countryname)
        dajax.assign('#id_alert_success', 'innerHTML', str(result))
    except:
        pass
        #dajax.alert("%s is not exist !!" % (id))
        #for error in form.errors:
        #    dajax.add_css_class('#id_%s' % error, 'error')
    return dajax.json()


@login_required
@dajaxice_register
def add_blacklist_prefix(request, prefix):
    dajax = Dajax()

    try:
        prefix_list =\
            Prefix.objects.values('prefix').filter(prefix__in=[eval(prefix)])

        country_id = get_country_id('['+prefix+']')

        added_prefix = []
        for prefix in prefix_list:

            for key, value in prefix.iteritems():
                rec_count = Blacklist.objects.filter(user=request.user,
                    phonenumber_prefix=int(value),
                    country_id=country_id).count()

                # No duplicate record, so insert
                if rec_count == 0:
                    blacklist = Blacklist.objects.create(
                        user=request.user,
                        phonenumber_prefix=int(value),
                        country_id=country_id,
                    )
                    added_prefix.append(value)

        result = '<div class="alert alert-success">Alert : (%s) has been successfully added in blacklist !!</div>' \
                 % (str(added_prefix))
        dajax.assign('#id_alert_success', 'innerHTML', str(result))
    except:
        pass
        #dajax.alert("%s is not exist !!" % (id))
        #for error in form.errors:
        #    dajax.add_css_class('#id_%s' % error, 'error')
    return dajax.json()
