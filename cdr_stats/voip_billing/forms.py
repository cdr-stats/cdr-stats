from django import forms
from django.utils.translation import ugettext_lazy as _
from common.common_functions import isint
from voip_billing.function_def import plan_list, rate_range
from cdr.forms import sw_list_with_all


class FileImport(forms.Form):
    """
    General Form : CSV file upload
    """
    csv_file = forms.FileField(label=_("Upload CSV File "), required=True,
                            error_messages={'required': 'Please upload File'},
                            help_text=_("Browse CSV file"))

    def clean_file(self):
        """
        Form Validation :  File extension Check
        """
        filename = self.cleaned_data["csv_file"]
        file_exts = ("csv", "txt")
        if not str(filename).split(".")[1].lower() in file_exts:
            raise forms.ValidationError(_(u'Document types accepted: %s' %
                                        ' '.join(file_exts)))
        else:
            return filename


class RetailRate_fileImport(FileImport):
    """
    Admin Form : Import CSV file with Retail Plan
    """
    plan_id = forms.ChoiceField(label=_("Retail Plan"),
                                choices=plan_list("retail"), required=False,
                                help_text=_("Select Retail Plan"))


class CarrierRate_fileImport(FileImport):
    """
    Admin Form : Import CSV file with Carrier Plan
    """
    plan_id = forms.ChoiceField(label=_("Carrier Plan"),
                                choices=plan_list("carrier"), required=False,
                                help_text=_("Select Carrier Plan"))
    chk = forms.BooleanField(label=_("Make Retail Plan"), required=False,
                        help_text=_("Select if you want to make retail plan"))
    retail_plan_id = forms.ChoiceField(label=_("Retail Plan"),
                                choices=plan_list("retail"), required=False,
                                help_text=_("Select Retail Plan"))
    profit_percentage = forms.CharField(label=_("Profit in % :"),
                    widget=forms.TextInput(attrs={'size': 3}), required=False,
                    help_text=_("Enter digit without %"))

    def clean_profit_percentage(self):
        """
        Validation Check:
        Percentage Value must be in digit (int/float)
        """
        chk = self.cleaned_data["chk"]
        p_p = self.cleaned_data["profit_percentage"]
        if chk == True:
            if isint(p_p) == False:
                raise forms.ValidationError(_("Please enter int/float value"))
            else:
                return p_p


class Carrier_Rate_fileExport(forms.Form):
    """
    Admin Form : Carrier Rate Export
    """
    plan_id = forms.ChoiceField(label=_("Carrier Plan"),
                                choices=plan_list("carrier"), required=False)


class Retail_Rate_fileExport(forms.Form):
    """
    Admin Form : Retail Rate Export
    """
    plan_id = forms.ChoiceField(label=_("Retail Plan"),
                                choices=plan_list("retail"), required=False)

class VoIPPlan_fileExport(forms.Form):
    """
    Admin Form : VoIP Plan Export
    """
    plan_id = forms.ChoiceField(label=_("VoIP Plan"),
                    choices=plan_list("voip"), required=False,
                    help_text=_('This will export the VoIPPlan using '\
                    'LCR on each prefix-rate tuple'))

class PrefixRetailRrateForm(forms.Form):
    """
    Client Form : To know Retail Rate for prefix
    """
    prefix = forms.CharField(label=_("Enter Prefix :"),
                   widget=forms.TextInput(attrs={'size': 15}), required=False)


class SendVoIPForm(forms.Form):
    """
    Client Form : To Send VoIP
    """
    destination_no = forms.CharField(label=_("Destination"), required=True,
                                     help_text=_('Enter Digit Only'))
    txt_msg = forms.CharField(label=_("Message"),
                              widget=forms.Textarea,
                              help_text=_('Not more than 120 characters'),
                              required=True)

    def clean_destination_no(self):
        """
        Form Validation :  destination_no Check
        """
        destination_no = self.cleaned_data['destination_no']
        if isint(destination_no) == False:
            raise forms.ValidationError("Enter Digit only!")
        return destination_no

    def clean_txt_msg(self):
        """
        Form Validation :  text message length Check
        """
        txt_msg = self.cleaned_data['txt_msg']
        if len(txt_msg) > 120:
            raise forms.ValidationError("Message should be less \n "
                                        "than 120 characters !!")
        return txt_msg


class SimulatorForm(SendVoIPForm):
    """
    Admin/Client Form : To Simulator
    """
    plan_id = forms.ChoiceField(label=_("VoIP Plan"),
                                choices=plan_list("voip"), required=False)

    def __init__(self, user, *args, **kwargs):
        super(SimulatorForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['plan_id', 'destination_no', ]
        if not user.is_superuser:
            self.fields['plan_id'] = forms.ChoiceField(widget=forms.HiddenInput())

    def clean_plan_id(self):
        """
        Form Validation :  Check Plan id
        """
        plan_id = int(self.cleaned_data['plan_id'])
        if plan_id == 0:
            raise forms.ValidationError("Select VoIP Plan !!")
        return plan_id


class CustomRateFilterForm(forms.Form):
    """
    Admin Form : Custom Rate Filter
    """
    rate_range = forms.ChoiceField(label=_(" "),
                                   choices=rate_range(), required=False)
    rate = forms.CharField(label=_(" "),
                           widget=forms.TextInput(attrs={'size': 10}),
                           required=False)


class BillingForm(SimulatorForm):

    from_date = forms.CharField(label=_('From'), required=True, max_length=10)
    to_date = forms.CharField(label=_('To'), required=True, max_length=10)
    switch = forms.ChoiceField(label=_('Switch'), required=False, choices=sw_list_with_all())

    def __init__(self, user, *args, **kwargs):
        super(BillingForm, self).__init__(user, *args, **kwargs)
        self.fields.keyOrder = ['from_date', 'to_date', 'plan_id', 'switch']
        if not user.is_superuser:
            self.fields['plan_id'] = forms.ChoiceField(widget=forms.HiddenInput())


class HourlyBillingForm(BillingForm):

    def __init__(self, user, *args, **kwargs):
        super(HourlyBillingForm, self).__init__(user, *args, **kwargs)
        self.fields.keyOrder = ['from_date', 'plan_id', 'switch']
        if not user.is_superuser:
            self.fields['plan_id'] = forms.ChoiceField(widget=forms.HiddenInput())