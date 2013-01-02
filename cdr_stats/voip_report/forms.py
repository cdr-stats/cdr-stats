from django import forms
from django.forms import *
from django.contrib import *
from django.contrib.admin.widgets import *
from django.utils.translation import ugettext_lazy as _
from voip2bill.voip_billing.forms import *
from voip2bill.voip_report.models import VOIPCALL_DISPOSITION
from voip2bill.voip_report.function_def import *
from datetime import *

voip_call_disposition_list = []
voip_call_disposition_list.append(('all', 'ALL'))
for i in VOIPCALL_DISPOSITION:
    voip_call_disposition_list.append((i[0], i[1]))


class VoipSearchForm(SearchForm):
    """
    VoIP call Report Search Parameters
    """
    billed = forms.ChoiceField(label=_('Billed :'),
                               choices=billed_list(),
                               required=False,)
    status = forms.ChoiceField(label=_('Disposition :'),
                               choices=voip_call_disposition_list,
                               required=False,)
