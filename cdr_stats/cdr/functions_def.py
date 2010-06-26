from django.utils.translation import gettext as _
from cdr.models import *
from datetime import *
from random import *
import calendar
import string
import urllib
import time

#related to date manipulation
def relative_days(from_day,from_year):
    if from_day == 30:
        relative_days=2
        return relative_days
    elif from_day == 31:
        relative_days=1
        return relative_days
    else:
        if calendar.isleap(from_year) == 'false':
            relative_days=2
        else:
            relative_days=1
        return relative_days


def uniq(inlist):
    # order preserving
    uniques = []
    for item in inlist:
        if item not in uniques:
            uniques.append(item)
    return uniques


def get_unique_id():
    """get unique id"""
    length=8
    chars="abcdefghijklmnopqrstuvwxyz1234567890"
    return ''.join([choice(chars) for i in range(length)])


def comp_month_range():
    word_months = _("months")
    word_month = _("month")
    COMP_MONTH_LIST= ( (12,'- 12 '+word_months),
                        (11,'- 11 '+word_months),
                        (10,'- 10 '+word_months),
                        (9,'- 9 '+word_months),
                        (8,'- 8 '+word_months),
                        (7,'- 7 '+word_months),
                        (6,'- 6 '+word_months),
                        (5,'- 5 '+word_months),
                        (4,'- 4 '+word_months),
                        (3,'- 3 '+word_months),
                        (2,'- 2 '+word_months),
                        (1,'- 1 '+word_month), 
                       )
    return COMP_MONTH_LIST


def comp_day_range():
    word_days = _("days")
    word_day = _("day")
    COMP_DAY_LIST= ( (7,'- 7 '+word_days),
                     (6,'- 6 '+word_days),
                     (5,'- 5 '+word_days),
                     (4,'- 4 '+word_days),
                     (3,'- 3 '+word_days),
                     (2,'- 2 '+word_days),
                     (1,'- 1 '+word_day),)
    return COMP_DAY_LIST


def date_range(start, end):
    r = (end+timedelta(days=1)-start).days
    return [start+timedelta(days=i) for i in range(r)]


def day_range():
    DAYS = range(1,32)
    days = map(lambda x:(x,x),DAYS)
    return days


def validate_days(year, month, day):
    total_days = calendar.monthrange(year,month)
    if day > total_days[1]:
        return total_days[1]
    else:
        return day


def month_year_range():
    tday = datetime.today()
    year_actual = tday.year
    YEARS = range(year_actual-1, year_actual+1)
    YEARS.reverse()
    m_list = []
    for n in YEARS:
        if year_actual == n:
            month_no = tday.month + 1
        else:
            month_no = 13
        months_list = range(1,month_no)
        months_list.reverse()
        for m in months_list:
            name = datetime(n, m,1).strftime("%B")
            str_year = datetime(n, m,1).strftime("%Y")
            str_month = datetime(n, m,1).strftime("%m")
            sample_str = str_year+"-"+str_month
            sample_name_str = name + "-" + str_year
            m_list.append( (sample_str,sample_name_str) )
    return m_list


# get news from http://cdr-stats.org/news.php
def get_news():
    
    news_final = []
    try :
        news_handler = urllib.urlopen('http://www.cdr-stats.org/news.php')
        news = news_handler.read()
        news = nl2br(news)
        news = string.split(news, '<br/>')
        
        news_array = {}
        value = {}
        for newsweb in news:
            value = string.split(newsweb, '|')
            if len(value[0]) > 1 :
                news_array[value[0]]=value[1]

        info = {}
        for k in news_array:
            link = k[int(k.find("http://")-1):len(k)]
            info = k[0:int(k.find("http://")-1)]
            info = string.split(k, ' - ')
            news_final.append((info[0],info[1],news_array[k]))

        news_handler.close()
    except IndexError:
        pass
    except IOError:
        pass
        
    return news_final


#variable check with request
def variable_value(request,field_name):
    if request.method == 'GET':
        if field_name in request.GET:
            field_name = request.GET[field_name]
        else:
            field_name = ''

    if request.method == 'POST':
        if field_name in request.POST:
            field_name = request.POST[field_name]
        else:
            field_name = ''

    return field_name

#source_type/destination_type filed check with request
def source_desti_field_chk(base_field,base_field_type,field_name):
    kwargs = {}
    if base_field != '':
        if base_field_type == '1':
            kwargs[field_name + '__exact']      = base_field
        if base_field_type == '2':
            kwargs[field_name + '__startswith'] = base_field
        if base_field_type == '3':
            kwargs[field_name + '__contains']   = base_field
        if base_field_type == '4':
            kwargs[field_name + '__endswith']   = base_field

    return kwargs


#related to string operation
def nl2br(s):
    return '<br/>'.join(s.split('\n'))


def reverseString(s):
    return s[::-1]


def int_convert_to_minute(value):
    min = int(int(value) / 60)
    sec = int(int(value) % 60)
    return "%02d" % min + ":" + "%02d" % sec



