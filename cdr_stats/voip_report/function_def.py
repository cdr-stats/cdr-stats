from voip_report.forms import voip_call_disposition_list


def get_disposition_id(name):
    """
    To get id from voip_call_disposition_list
    """
    for i in voip_call_disposition_list:        
        if i[1] == name:
            return i[0]        


def get_disposition_name(id):
    """
    To get name from voip_call_disposition_list
    """
    for i in voip_call_disposition_list:
        if i[0] == id:
            return i[1]