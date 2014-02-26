# -*- coding: utf-8 -*-
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

from django.utils.safestring import mark_safe
from django.template.defaultfilters import register
from django_lets_go.common_functions import word_capital
import re
from string import Template


def striphtml(data):
    p = re.compile(r'<.*?>')
    return mark_safe(p.sub('', data))


@register.simple_tag(name='field_html_code')
def field_html_code(field, main_class='col-md-6 col-xs-8', flag_error_text=True, flag_help_text=True):
    """
    Usage: {% field_html_code field 'col-md-6 col-xs-8' %}
    """
    tmp_div = Template("""
        <div class="$main_class">
            <div class="form-group $has_error">
                <label class="control-label" for="$field_auto_id">$field_label</label>
                $field
                $field_errors
                $field_help_text
            </div>
        </div>
    """)
    has_error = 'has-error' if field.errors else ''
    field_errors = ''
    if field.errors and flag_error_text:
        field_errors = '<span class="help-block">%s</span>\n' % striphtml(str(field.errors)).capitalize()

    field_help_text = ''
    if flag_help_text:
        field_help_text = '<span class="help-block">%s</span>\n' % (field.help_text.capitalize())

    htmlcell = tmp_div.substitute(
        main_class=main_class, has_error=has_error,
        field_auto_id=field.auto_id, field_label=word_capital(field.label),
        field=str(field).decode("utf-8"), field_errors=field_errors,
        field_help_text=field_help_text)

    return mark_safe(htmlcell)


@register.filter(name='check_url_for_template_width')
def check_url_for_template_width(current_url):
    """"""
    full_width_on_requested_path = [
        '/cdr_dashboard/',
    ]
    if current_url == '/':
        return True
    else:
        current_url = str(current_url)
        for path in full_width_on_requested_path:
            if path in current_url:
                return True
        return False
