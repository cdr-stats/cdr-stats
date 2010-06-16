from django import *
from django import forms
from cdr.models import *
from cdr.functions_def import *
from django.forms import *
from django.contrib import *
from django.contrib.admin.widgets import *
from django.utils.translation import ugettext_lazy as _
from uni_form.helpers import FormHelper, Submit, Reset
from uni_form.helpers import Layout, Fieldset, Row, Column, HTML


class LayoutTestForm(forms.Form):

    is_company = forms.CharField(label="company", required=False, widget=forms.CheckboxInput())
    email = forms.CharField(label="email2", max_length=30, required=True, widget=forms.TextInput())
    password1 = forms.CharField(label="password", max_length=30, required=True, widget=forms.PasswordInput())
    password2 = forms.CharField(label="re-enter password", max_length=30, required=True, widget=forms.PasswordInput())
    first_name = forms.CharField(label="first name", max_length=30, required=True, widget=forms.TextInput())
    last_name = forms.CharField(label="last name", max_length=30, required=True, widget=forms.TextInput())
    source_type = forms.TypedChoiceField(coerce=bool,choices=((1, 'Exact'), (2, 'Begins with'), (3, 'Contains'), (4, 'Ends with')),widget=forms.RadioSelect)
    
    # Attach a formHelper to your forms class.
    helper = FormHelper()
    
    # create the layout object
    layout = Layout(
                # first fieldset shows the company
                Fieldset('', 'is_company'),

                # second fieldset shows the contact info
                Fieldset('Contact details',
                        'email',
                        Row('password1','password2'),
                        'first_name',
                        'last_name',
                        'source_type'
                         )
                )

    helper.add_layout(layout)

    submit = Submit('add','Add this contact')
    helper.add_input(submit)


class CdrSearchForm(forms.Form):
    destination = forms.CharField(label=u'Destination', required=False, widget=forms.TextInput(attrs={'size': 15}))
    destination_type = forms.TypedChoiceField(coerce=bool, required=False, choices=((1, 'Exact'), (2, 'Begins with'), (3, 'Contains'), (4, 'Ends with')),widget=forms.RadioSelect)
    source = forms.CharField(label=u'Source', required=False, widget=forms.TextInput(attrs={'size': 15}))
    source_type = forms.TypedChoiceField(coerce=bool, required=False, choices=((1, 'Exact'), (2, 'Begins with'), (3, 'Contains'), (4, 'Ends with')),widget=forms.RadioSelect)
    channel = forms.CharField(label=u'Channel', required=False, widget=forms.TextInput(attrs={'size': 15}))


class MonthLoadSearchForm(CdrSearchForm):
    from_month_year= forms.ChoiceField(label=u'Select month', required=False, choices=month_year_range())
    comp_months = forms.ChoiceField(label=u'Number of months to compare', required=False, choices=comp_month_range())
    
    # Attach a formHelper to your forms class.
    helper = FormHelper()
    
    submit = Submit('search', 'Search')
    helper.add_input(submit)
    helper.use_csrf_protection = True
    
    def __init__(self, *args, **kwargs):
        super(MonthLoadSearchForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['from_month_year', 'comp_months', 'destination', 'destination_type', 'source', 'source_type', 'channel']


class MyForm(forms.Form):
    title = forms.CharField(label=_("Title"), max_length=30, widget=forms.TextInput())
    # this displays how to attach a formHelper to your forms class.
    helper = FormHelper()
    helper.form_id = 'this-form-rocks'
    helper.form_class = 'search'
    helper.use_csrf_protection = True
    submit = Submit('search','search this site')
    helper.add_input(submit)
    reset = Reset('reset','reset button')
    helper.add_input(reset)
    

class DailyLoadSearchForm(CdrSearchForm):
    from_day = forms.ChoiceField(label=u'From', required=False, choices=day_range())
    from_month_year= forms.ChoiceField(label=u'Select day', required=False, choices=month_year_range())
    
    # Attach a formHelper to your forms class.
    helper = FormHelper()

    submit = Submit('search', 'Search')
    helper.add_input(submit)
    helper.use_csrf_protection = True

    def __init__(self, *args, **kwargs):
        super(DailyLoadSearchForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['from_day','from_month_year', 'destination', 'destination_type', 'source', 'source_type', 'channel']
    

class CompareCallSearchForm(CdrSearchForm):
    from_day = forms.ChoiceField(label=u'From', required=False, choices=day_range())
    from_month_year= forms.ChoiceField(label=u'Select day', required=False, choices=month_year_range())
    comp_days = forms.ChoiceField(label=u'Number of days to compare', required=False, choices=comp_day_range())
    graph_view=forms.ChoiceField(label=u'Graph', required=False, choices=((1,'Number of calls by hours'),(2,'Minutes by hours')))

    # Attach a formHelper to your forms class.
    helper = FormHelper()

    submit = Submit('search', 'Search')
    helper.add_input(submit)
    helper.use_csrf_protection = True

    def __init__(self, *args, **kwargs):
        super(CompareCallSearchForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['from_day','from_month_year','comp_days', 'destination', 'destination_type', 'source', 'source_type', 'channel','graph_view']


class CdrSearchForm(forms.Form):
    
    from_day = forms.ChoiceField(label=u'From :', required=False, choices=day_range())
    from_month_year = forms.ChoiceField(label=u'', required=False, choices=month_year_range())
    to_day = forms.ChoiceField(label=u'To :', required=False, choices=day_range())
    to_month_year = forms.ChoiceField(label=u'', required=False, choices=month_year_range())
    
    result = forms.TypedChoiceField(label=u'Result:', required=False, coerce=bool,choices=(('1', 'Minutes'), ('2', 'Seconds')),widget=forms.RadioSelect)
    
    # create the layout object
    layout = Layout(
                # second fieldset shows the contact info
                Fieldset(
                        'Search Options :',
                        Column('from_day','from_month_year'),
                        Column('to_day','to_month_year'),
                        'result',
                     )
                )

    # Attach a formHelper to your forms class.
    helper = FormHelper()
    helper.form_method = 'GET'
    submit = Submit('search', 'Search')
    helper.add_input(submit)
    helper.use_csrf_protection = True
    helper.add_layout(layout)
    
class loginForm(forms.Form):
    user = forms.CharField(max_length=40, label='Login', required=True, widget=forms.TextInput(attrs={'size':'10'}))
    password = forms.CharField(max_length=40, label='password', required=True, widget=forms.PasswordInput(attrs={'size':'10'}))
    
    
    
