from common.common_functions import variable_value, validate_days, ceil_strdate
from datetime import datetime


def voipcall_record_common_fun(request, form_require="no"):
    """
    Return Form with Initial data or Array (kwargs) for Voipcall_Report
    Changelist_view
    """
    if "from_date" in request.POST:
        # From
        from_date = request.POST['from_date']
        start_date = ceil_strdate(from_date, 'start')
        request.session['session_from_date'] = from_date

    if "to_date" in request.POST:
        # To
        to_date = request.POST['to_date']
        end_date = ceil_strdate(to_date, 'end')
        request.session['session_to_date'] = to_date

    if "fromday_chk" in request.POST:
        fromday_chk = 'on'
        from_day = int(request.POST['from_day'])
        from_month_year = request.POST['from_month_year']
        from_year = int(request.POST['from_month_year'][0:4])
        from_month = int(request.POST['from_month_year'][5:7])
        from_day = validate_days(from_year, from_month, from_day)
        start_date = datetime(from_year, from_month, from_day, 0, 0, 0, 0)
    else:
        fromday_chk = ''
        from_day = ''
        from_month_year = ''
        from_year = ''
        from_month = ''
        from_day = ''
        start_date = ''

    if "today_chk" in request.POST:
        today_chk = 'on'
        to_day = int(request.POST['to_day'])
        to_month_year = request.POST['to_month_year']
        to_year = int(request.POST['to_month_year'][0:4])
        to_month = int(request.POST['to_month_year'][5:7])
        to_day = validate_days(to_year, to_month, to_day)
        end_date = datetime(to_year, to_month, to_day, 23, 59, 59, 999999)
    else:
        today_chk = ''
        to_day = ''
        to_month_year = ''
        to_year = ''
        to_month = ''
        to_day = ''
        end_date = ''

    # Assign form field value to local variable
    billed = variable_value(request, 'billed')
    disposition = variable_value(request, 'status')

    from voip_report.forms import VoipSearchForm
    if form_require == "yes":
        form = VoipSearchForm(initial={'fromday_chk': fromday_chk,
                                       'from_day': from_day,
                                       'from_month_year': from_month_year,
                                       'today_chk': today_chk, 'to_day': to_day,
                                       'to_month_year': to_month_year,
                                       'billed': billed,
                                       'status': disposition})
        return form
    else:
        kwargs = {}
        if fromday_chk == 'on' and today_chk == 'on':
            kwargs['updated_date__range'] = (start_date, end_date)
        if fromday_chk == 'on' and today_chk != 'on':
            kwargs['updated_date__gte'] = start_date
        if today_chk == 'on' and fromday_chk != 'on':
            kwargs['updated_date__lte'] = end_date

        if billed == 'yes':
            kwargs['billed__exact'] = 1
        if billed == 'no':
            kwargs['billed__exact'] = 0

        if disposition != 'all':
            kwargs['disposition__exact'] = disposition

        if len(kwargs) == 0:
            tday = datetime.today()
            kwargs['updated_date__gte'] = datetime(tday.year,
                                                   tday.month,
                                                   tday.day, 0, 0, 0, 0)

        return kwargs


def get_disposition_id(name):
    """
    To get id from voip_call_disposition_list
    """
    from voip_report.forms import voip_call_disposition_list
    for i in voip_call_disposition_list:        
        if i[1] == name:
            return i[0]        


def get_disposition_name(id):
    """
    To get name from voip_call_disposition_list
    """
    from voip_report.forms import voip_call_disposition_list
    for i in voip_call_disposition_list:
        if i[0] == id:
            return i[1]