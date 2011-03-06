from cdr.functions_def import *
from django.forms import *
from django.contrib.admin.widgets import *
from django.utils.translation import ugettext_lazy as _
from uni_form.helpers import FormHelper, Submit, Reset
from uni_form.helpers import Layout, Fieldset, Row, Column, HTML



class SearchForm(forms.Form):

    destination = forms.CharField(label=_('Destination'), required=False, widget=forms.TextInput(attrs={'size': 15, 'class':'span-10'}))
    destination_type = forms.ChoiceField(label='', required=False,
                    choices=((1, _('Equals')), (2, _('Begins with')), (3, _('Contains')), (4, _('Ends with')))
                    )
    source = forms.CharField(label=_('Source'), required=False, widget=forms.TextInput(attrs={'size': 15, 'class':'span-10'}))
    source_type = forms.ChoiceField(label='', required=False,
                    choices=((1, _('Equals')), (2, _('Begins with')), (3, _('Contains')), (4, _('Ends with'))),
                    )
    channel = forms.CharField(label='Channel', required=False, widget=forms.TextInput(attrs={'size': 15,'class':'span-10'}))
    
    layout = Fieldset(
                '',
                Row(
                    Column('destination'),
                    Column('destination_type'),
                ),
                Row(
                    Column('source'),
                    Column('source_type'),
                ),
                'channel',
            )

class CdrSearchForm(forms.Form):
    
    from_date = CharField(label=_('From'), required=True, max_length=10, help_text=_("Please use the following format")+": <em>YYYY-MM-DD</em>.")
    to_date = CharField(label=_('To'), required=True, max_length=10, help_text=_("Please use the following format")+": <em>YYYY-MM-DD</em>.")
    
    result = forms.TypedChoiceField(label=_('Result:'), required=False, coerce=bool,
                choices = (('1', _('Minutes')), ('2', _('Seconds'))),widget=forms.RadioSelect)

    # Attach a formHelper to your forms class.
    helper = FormHelper()
    helper.form_method = 'POST'
    submit = Submit('search', _('Search'))
    helper.add_input(submit)
    helper.use_csrf_protection = True
    

class MonthLoadSearchForm(SearchForm):

    from_month_year= forms.CharField(label=_('Select date'), required=True, max_length=10, widget=forms.TextInput(attrs={'class':'span-10'}))
    comp_months = forms.ChoiceField(label='', required=False, choices=comp_month_range())

    layout = Layout(
        Fieldset(
                '',
                Row(
                    Column('from_month_year'),
                    Column('comp_months'),
                ),
        ),
        SearchForm.layout,
    )
    
    # Attach a formHelper to your forms class.
    helper = FormHelper()
    
    submit = Submit('search', _('Search'))
    helper.add_input(submit)
    helper.use_csrf_protection = True
    helper.add_layout(layout)
    
    def __init__(self, *args, **kwargs):
        super(MonthLoadSearchForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['from_month_year', 'comp_months', 'destination', 'destination_type', 'source', 'source_type', 'channel']


class DailyLoadSearchForm(SearchForm):

    from_date = forms.CharField(label=_('Select date'), required=True, max_length=10, help_text=_("Please use the following format")+": <em>YYYY-MM-DD</em>.", widget=forms.TextInput(attrs={'class':'span-10'}))
    
    layout = Layout(
        Fieldset(
                '',
                'from_date',
        ),
        SearchForm.layout,
    )
    
    # Attach a formHelper to your forms class.
    helper = FormHelper()

    submit = Submit('search', _('Search'))
    helper.add_input(submit)
    helper.use_csrf_protection = True
    helper.add_layout(layout)

    def __init__(self, *args, **kwargs):
        super(DailyLoadSearchForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['from_date', 'destination', 'destination_type', 'source', 'source_type', 'channel']
    

class CompareCallSearchForm(SearchForm):

    from_date = forms.CharField(label=_('Select date'), required=True, max_length=10, help_text=_("Please use the following format")+": <em>YYYY-MM-DD</em>.", widget=forms.TextInput(attrs={'class':'span-10'}))
    comp_days = forms.ChoiceField(label='', required=False, choices=comp_day_range())
    graph_view=forms.ChoiceField(label=_('Graph'), required=False,
            choices=((1, _('Calls per Hour')), (2,_('Minutes per Hour'))))
    
    layout = Layout(
        Fieldset(
                '',
                Row(
                    Column('from_date'),
                    Column('comp_days'),
                ),
        ),
        SearchForm.layout,
        'graph_view',
    )
    
    # Attach a formHelper to your forms class.
    helper = FormHelper()
    
    submit = Submit('search', _('Search'))
    helper.add_input(submit)
    helper.use_csrf_protection = True
    helper.add_layout(layout)

    def __init__(self, *args, **kwargs):
        super(CompareCallSearchForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['from_date','comp_days', 'destination', 'destination_type', 'source', 'source_type', 'channel','graph_view']


class ConcurrentCallForm(forms.Form):
    result = forms.TypedChoiceField( label=_('Result'), required=True, coerce=bool, empty_value=1,
                choices = (('1', _('Today')), ('2', _('Yesterday')), ('3', _('Current Week')), ('4', _('Previous Week')), ('5', _('Current Month')), ('6', _('Previous Month'))))
             
    
    # Attach a formHelper to your forms class.
    helper = FormHelper()
    helper.form_method = 'POST'
    submit = Submit('search', _('Search'))
    helper.add_input(submit)
    helper.use_csrf_protection = True


class loginForm(forms.Form):

    user = forms.CharField(max_length=40, label=_('Login'), required=True, widget=forms.TextInput(attrs={'size':'10'}))
    password = forms.CharField(max_length=40, label=_('Password'), required=True, widget=forms.PasswordInput(attrs={'size':'10'}))
    
