from cdr.models import *
from datetime import *
import calendar
from random import *
import string

def get_unique_id():
    """get unique id"""
    length=8
    chars="abcdefghijklmnopqrstuvwxyz1234567890"
    return ''.join([choice(chars) for i in range(length)])


def comp_month_range():
    COMP_MONTH_LIST= ( (6,'- 6 months'),(5,'- 5 months'),(4,'- 4 months'),(3,'- 3 months'),(2,'- 2 months'),(1,'- 1 months'), )
    return COMP_MONTH_LIST

def day_range():
    DAYS = range(1,32)
    days = map(lambda x:(x,x),DAYS)
    return days

def validate_days(year,month,day):
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
