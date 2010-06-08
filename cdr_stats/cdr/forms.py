from django import *
from django import forms
from cdr.models import *
from cdr.functions_def import *
from django.forms import *
from django.contrib import *
from django.contrib.admin.widgets import *

class MonthLoadSearchForm(forms.Form):
    from_month_year= forms.ChoiceField(label=u'SELECT MONTH',choices=month_year_range())
    comp_months = forms.ChoiceField(label=u'Number of months to compare',choices=comp_month_range())
    destination = forms.CharField(label=u'DESTINATION',widget=forms.TextInput(attrs={'size': 15}))
    destination_type = forms.TypedChoiceField(coerce=bool,choices=((1, 'Exact'), (2, 'Begins with'), (3, 'Contains'), (4, 'Ends with')),widget=forms.RadioSelect)
    source = forms.CharField(label=u'SOURCE',widget=forms.TextInput(attrs={'size': 15}))
    source_type = forms.TypedChoiceField(coerce=bool,choices=((1, 'Exact'), (2, 'Begins with'), (3, 'Contains'), (4, 'Ends with')),widget=forms.RadioSelect)
    channel = forms.CharField(label=u'CHANNEL',widget=forms.TextInput(attrs={'size': 15}))
    
class DailyLoadSearchForm(forms.Form):
    from_day = forms.ChoiceField(label=u'From',choices=day_range())
    from_month_year= forms.ChoiceField(label=u'SELECT MONTH',choices=month_year_range())
    comp_months = forms.ChoiceField(label=u'Number of months to compare',choices=comp_month_range())
    destination = forms.CharField(label=u'DESTINATION',widget=forms.TextInput(attrs={'size': 15}))
    destination_type = forms.TypedChoiceField(coerce=bool,choices=((1, 'Exact'), (2, 'Begins with'), (3, 'Contains'), (4, 'Ends with')),widget=forms.RadioSelect)
    source = forms.CharField(label=u'SOURCE',widget=forms.TextInput(attrs={'size': 15}))
    source_type = forms.TypedChoiceField(coerce=bool,choices=((1, 'Exact'), (2, 'Begins with'), (3, 'Contains'), (4, 'Ends with')),widget=forms.RadioSelect)
    channel = forms.CharField(label=u'CHANNEL',widget=forms.TextInput(attrs={'size': 15}))

class CompareCallSearchForm(forms.Form):
    from_day = forms.ChoiceField(label=u'From',choices=day_range())
    from_month_year= forms.ChoiceField(label=u'SELECT MONTH',choices=month_year_range())
    comp_days = forms.ChoiceField(label=u'Number of days to compare',choices=comp_day_range())
    destination = forms.CharField(label=u'DESTINATION',widget=forms.TextInput(attrs={'size': 15}))
    destination_type = forms.TypedChoiceField(coerce=bool,choices=((1, 'Exact'), (2, 'Begins with'), (3, 'Contains'), (4, 'Ends with')),widget=forms.RadioSelect)
    source = forms.CharField(label=u'SOURCE',widget=forms.TextInput(attrs={'size': 15}))
    source_type = forms.TypedChoiceField(coerce=bool,choices=((1, 'Exact'), (2, 'Begins with'), (3, 'Contains'), (4, 'Ends with')),widget=forms.RadioSelect)
    channel = forms.CharField(label=u'CHANNEL',widget=forms.TextInput(attrs={'size': 15}))
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


    destination = forms.CharField(label=u'DESTINATION',widget=forms.TextInput(attrs={'size': 15}))
    destination_type = forms.TypedChoiceField(coerce=bool,choices=((1, 'Exact'), (2, 'Begins with'), (3, 'Contains'), (4, 'Ends with')),widget=forms.RadioSelect)

    source = forms.CharField(label=u'SOURCE',widget=forms.TextInput(attrs={'size': 15}))
    source_type = forms.TypedChoiceField(coerce=bool,choices=((1, 'Exact'), (2, 'Begins with'), (3, 'Contains'), (4, 'Ends with')),widget=forms.RadioSelect)

    channel = forms.CharField(label=u'CHANNEL',widget=forms.TextInput(attrs={'size': 15}))

    duration_1 = forms.CharField(label=u'DURATION',widget=forms.TextInput(attrs={'size': 15}))
    duration_1_type = forms.TypedChoiceField(coerce=bool,choices=((1, '>'), (2, '>='), (3, '='), (4, '<='),(5, '<')),widget=forms.RadioSelect)
    duration_2 = forms.CharField(label=u'',widget=forms.TextInput(attrs={'size': 15}))
    duration_2_type = forms.TypedChoiceField(coerce=bool,choices=((1, '>'), (2, '>='), (3, '<='),(4, '<')),widget=forms.RadioSelect)

    result = forms.TypedChoiceField(label=u'RESULT:',coerce=bool,choices=((1, 'Minutes'), (2, 'Seconds')),widget=forms.RadioSelect)
    
class loginForm(forms.Form):
    user = forms.CharField(max_length=40, label='Login', required=True, widget=forms.TextInput(attrs={'size':'10'}))
    password = forms.CharField(max_length=40, label='password', required=True, widget=forms.PasswordInput(attrs={'size':'10'}))
