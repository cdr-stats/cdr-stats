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
from django import forms
from django.forms import ModelForm
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from mod_utils.helper import Export_choice

from crispy_forms.layout import HTML
from crispy_forms.bootstrap import FormActions
from crispy_forms.layout import Submit


class HorizRadioRenderer(forms.RadioSelect.renderer):
    """This overrides widget method to put radio buttons horizontally
    instead of vertically.
    """
    def render(self):
        """Outputs radios"""
        return mark_safe(u'\n'.join([u'%s\n' % w for w in self]))


class Exportfile(forms.Form):
    """
    Abstract Form : export file in various format e.g. XLS, CSV, JSON
    """
    export_to = forms.TypedChoiceField(label=_('export to').capitalize(), required=True,
                                       choices=list(Export_choice),
                                       widget=forms.RadioSelect(renderer=HorizRadioRenderer))


class SaveUserModelForm(ModelForm):
    """SaveUserModelForm ModelForm"""

    def save(self, *args, **kwargs):
        """save that retrieve the user"""
        self.user = kwargs.pop('user', None)
        kwargs['commit'] = False
        obj = super(SaveUserModelForm, self).save(*args, **kwargs)
        if self.user:
            obj.user = self.user
        obj.save()
        return obj


def common_submit_buttons(layout_section=None, default_action='add'):
    """
    function to remove the first button and add update and delete button
    """
    start_div = '<div class="row"><div class="col-md-12 text-right">'
    end_div = '</div></div>'
    if default_action == 'update':
        form_action = FormActions(
            HTML('%s<button type="submit" id="update" name="update" class="btn btn-primary" value="submit">'
                 '<i class="fa fa-edit fa-lg"></i> %s</button>'
                 '<button type="submit" id="delete" name="delete" class="btn btn-danger" value="submit">'
                 '<i class="fa fa-trash-o fa-lg"></i> %s</button>%s' % (start_div, _('update').title(), _('delete').title(), end_div))
        )
        if layout_section is None:
            return form_action
        layout_section.append(form_action)
    elif default_action == 'add':
        form_action = FormActions(
            HTML('%s<button type="submit" id="add" name="add" class="btn btn-primary" value="submit">'
                 '<i class="fa fa-save fa-lg"></i> %s</button>%s' % (start_div, _('save').title(), end_div)
                 ),
        )
        if layout_section is None:
            return form_action
        layout_section.append(form_action)
    elif default_action == 'import':
        form_action = FormActions(
            HTML('%s<button type="submit" id="add" name="add" class="btn btn-primary" value="submit">'
                 '<i class="fa fa-save fa-lg"></i> %s</button>%s' % (start_div, _('import').title(), end_div)
                 ),
        )
        layout_section.append(form_action)
    elif default_action == 'search':
        start_div = '<div class="row"><div class="col-md-12 text-left">'
        form_action = FormActions(
            HTML('%s<button type="submit" id="id_submit" name="submit" class="btn btn-primary" value="submit">'
                 '<i class="fa fa-search fa-lg"></i> %s</button>%s' % (start_div, _('search').title(), end_div)
                 )
        )
        layout_section.append(form_action)
    elif default_action == 'reset-rate':
        form_action = FormActions(HTML("""<a href="/rates/" class="btn btn-danger"><i class="fa fa-trash-o fa-lg"></i> %s</a>""" %_('clear').title()))
        layout_section.append(form_action)
    return layout_section
