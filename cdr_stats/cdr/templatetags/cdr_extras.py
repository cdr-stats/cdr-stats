from django import template
from django.template.defaultfilters import *
from datetime import datetime
import operator

register = template.Library()


@register.filter()
def row(value,tags):
    """
    Strips all [X]HTML tags except the space seperated list of tags
    from the output.

    Usage: keeptags:"strong em ul li"
    """
    import re
    from django.utils.html import strip_tags, escape
    tags = [re.escape(tag) for tag in tags.split()]
    tags_re = '(%s)' % '|'.join(tags)
    singletag_re = re.compile(r'<(%s\s*/?)>' % tags_re)
    starttag_re = re.compile(r'<(%s)(\s+[^>]+)>' % tags_re)
    endtag_re = re.compile(r'<(/%s)>' % tags_re)
    value = singletag_re.sub('##~~~\g<1>~~~##', value)
    value = starttag_re.sub('##~~~\g<1>\g<3>~~~##', value)
    value = endtag_re.sub('##~~~\g<1>~~~##', value)
    value = strip_tags(value)
    value = escape(value)
    recreate_re = re.compile('##~~~([^~]+)~~~##')
    value = recreate_re.sub('<\g<1>>', value)
    return value

row.is_safe = True

@register.filter()
def mul(value,arg):
        return value * arg
mul.is_safe = True

@register.filter()
def div(value, arg):
    if arg is None:
        return 0
    elif arg is 0:
        return 0
    else:
        return value / arg

@register.filter()
def subtract(value, arg):
    return value - arg

@register.filter
def adjust_for_pagination(value, page):
    value, page = int(value), int(page)
    adjusted_value = value + ((page - 1) * 10)
    return adjusted_value


@register.filter()
def time_in_min(value,arg):
    if int(value)!=0:
        if arg == 'min':
            min = int(value / 60)
            sec = int(value % 60)
            return "%02d" % min + ":" + "%02d" % sec + "min"
        else:
            min = int(value / 60)
            min = (min * 60)
            sec = int(value % 60)
            total_sec = min + sec
            return str(total_sec + " sec")
    else:
        return str("0:0 min")

@register.filter()
def conv_min(value):
    if int(value)!=0:
        min = int(value / 60)
        sec = int(value % 60)
        return "%02d" % min + ":" + "%02d" % sec
    else:
        return value

@register.filter()
def display_2bill(value,currency):
    try:
        value = float(float(value)/float(currency))
    except:      
        return value
    m = value - int(value)
    if m:
        return '%.3f' % value
    else:
        return '%.3f' % int(value)

"""
    Displays a floating point number as 34.2 (with one decimal place) but only if there's a point to be displayed
"""
@register.filter()
def floatformat2(text):
    try:
        f = float(text)
    except:
        return text
    m = f - int(f)
    if m:
        return '%.3f' % f
    else:
        return '%.3f' % int(f)
floatformat2.is_safe = True


@register.filter()
def percent(value):
    return str(round(value * 100, 2)) + " %"

@register.filter()
def month_int(value):
    val=int(value[0:2])
    return val

@register.filter()
def month_name(value,arg):
    month_dict = {1:"Jan",2:"Feb",3:"Mar",4:"Apr", 5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    no=int(value)
    m_name = month_dict[no]
    return str(m_name) + " " + str(arg)

@register.filter()
def cal_width(value,max):
    width = (value/float(max))*200
    return width


register.filter('row', row)
register.filter('mul', mul)
register.filter('subtract', subtract)
register.filter('adjust_for_pagination', adjust_for_pagination)
register.filter('div', div)
register.filter('conv_min', conv_min)
register.filter('time_in_min', time_in_min)
register.filter('display_2bill', display_2bill)
register.filter('floatformat2', floatformat2)
register.filter('percent', percent)
register.filter('month_int', month_int)
register.filter('month_name', month_name)
register.filter('cal_width', cal_width)