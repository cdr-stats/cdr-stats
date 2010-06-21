from django import template
from django.template.defaultfilters import *
from datetime import datetime
import operator

register = template.Library()

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
        return str("00:00 min")

@register.filter()
def conv_min(value):
    if int(value)!=0:
        min = int(value / 60)
        sec = int(value % 60)
        return "%02d" % min + ":" + "%02d" % sec
    else:
        return "00:00"

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

register.filter('conv_min', conv_min)
register.filter('time_in_min', time_in_min)
register.filter('month_int', month_int)
register.filter('month_name', month_name)
register.filter('cal_width', cal_width)