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


