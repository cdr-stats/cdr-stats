from django import *
from django import forms
from cdr.models import *
from cdr.functions_def import *
from django.forms import *
from django.contrib import *
from django.contrib.admin.widgets import *

from uni_form.helpers import FormHelper, Submit, Reset
from uni_form.helpers import Layout, Fieldset, Row, HTML


class LayoutTestForm(forms.Form):

    is_company = forms.CharField(label="company", required=False, widget=forms.CheckboxInput())
    email = forms.CharField(label="email", max_length=30, required=True, widget=forms.TextInput())
    password1 = forms.CharField(label="password", max_length=30, required=True, widget=forms.PasswordInput())
    password2 = forms.CharField(label="re-enter password", max_length=30, required=True, widget=forms.PasswordInput())
    first_name = forms.CharField(label="first name", max_length=30, required=True, widget=forms.TextInput())
    last_name = forms.CharField(label="last name", max_length=30, required=True, widget=forms.TextInput())
    
    # Attach a formHelper to your forms class.
    helper = FormHelper()
    
    # Create some HTML that you want in the page.
    # Yes, in real life your CSS would be cached, but this is just a simple example.
    style = """
    <style>
        .formRow {
            color: red;
        }
    </style>

    """
    # create the layout object
    layout = Layout(
                    # first fieldset shows the company
                    Fieldset('', 'is_company'),

                    # second fieldset shows the contact info
                    Fieldset('Contact details',
                            HTML(style),
                            'email',
                            Row('password1','password2'),
                            'first_name',
                            'last_name',
                             )
                    )

    helper.add_layout(layout)

    submit = Submit('add','Add this contact')
    helper.add_input(submit)


class CdrSearchForm(forms.Form):
    destination = forms.CharField(label=u'DESTINATION',widget=forms.TextInput(attrs={'size': 15}))
    destination_type = forms.TypedChoiceField(coerce=bool,choices=((1, 'Exact'), (2, 'Begins with'), (3, 'Contains'), (4, 'Ends with')),widget=forms.RadioSelect)
    source = forms.CharField(label=u'SOURCE',widget=forms.TextInput(attrs={'size': 15}))
    source_type = forms.TypedChoiceField(coerce=bool,choices=((1, 'Exact'), (2, 'Begins with'), (3, 'Contains'), (4, 'Ends with')),widget=forms.RadioSelect)
    channel = forms.CharField(label=u'CHANNEL',widget=forms.TextInput(attrs={'size': 15}))


class MonthLoadSearchForm(CdrSearchForm):
    from_month_year= forms.ChoiceField(label=u'SELECT MONTH',choices=month_year_range())
    comp_months = forms.ChoiceField(label=u'Number of months to compare',choices=comp_month_range())
    def __init__(self, *args, **kwargs):
        super(MonthLoadSearchForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['from_month_year', 'comp_months', 'destination', 'destination_type', 'source', 'source_type', 'channel']


class DailyLoadSearchForm(CdrSearchForm):
    from_day = forms.ChoiceField(label=u'From',choices=day_range())
    from_month_year= forms.ChoiceField(label=u'SELECT DAY',choices=month_year_range())
    comp_months = forms.ChoiceField(label=u'Number of months to compare',choices=comp_month_range())
    

class CompareCallSearchForm(CdrSearchForm):
    from_day = forms.ChoiceField(label=u'From',choices=day_range())
    from_month_year= forms.ChoiceField(label=u'SELECT DAY',choices=month_year_range())
    comp_days = forms.ChoiceField(label=u'Number of days to compare',choices=comp_day_range())
    graph_view=forms.ChoiceField(label=u'graph',choices=((1,'Number of calls by hours'),(2,'Minutes by hours')))


class CdrSearchForm(forms.Form):
    selection_of_month_day = forms.TypedChoiceField(coerce=bool,choices=((1, 'Selection of the month'), (2, 'Selection of the day'), ),widget=forms.RadioSelect)
    
    from_chk_month = forms.BooleanField(label="",required=False)
    from_month_year_1= forms.ChoiceField(label=u'From :',choices=month_year_range())
    to_chk_month = forms.BooleanField(label="",required=True)
    to_month_year_1 = forms.ChoiceField(label=u'To :',choices=month_year_range())

    from_chk_day = forms.BooleanField(label=u"",required=False)
    from_day = forms.ChoiceField(label=u'From :',choices=day_range())
    from_month_year_2= forms.ChoiceField(label=u'',choices=month_year_range())
    to_chk_day = forms.BooleanField(label="",required=True)
    to_day = forms.ChoiceField(label=u'To :',choices=day_range())
    to_month_year_2 = forms.ChoiceField(label=u'',choices=month_year_range())
    result = forms.TypedChoiceField(label=u'RESULT:',coerce=bool,choices=(('1', 'Minutes'), ('2', 'Seconds')),widget=forms.RadioSelect)
    
class loginForm(forms.Form):
    user = forms.CharField(max_length=40, label='Login', required=True, widget=forms.TextInput(attrs={'size':'10'}))
    password = forms.CharField(max_length=40, label='password', required=True, widget=forms.PasswordInput(attrs={'size':'10'}))
    
    
    
