from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.cache import cache
from country_dialcode.models import Prefix
from common.common_functions import variable_value, isint
from voip_billing.models import VoIPPlan, VoIPRetailPlan, VoIPRetailRate,\
    VoIPCarrierPlan, VoIPCarrierRate
import os


def plan_list(name):
    """
    Return List of Carrier/Retail/VoIP Plans
    """
    list = ()
    if name == "carrier":
        list = VoIPCarrierPlan.objects.all()
    if name == "retail":
        list = VoIPRetailPlan.objects.all()
    if name == "voip":
        list = VoIPPlan.objects.all()
    return ((l.id, l.name) for l in list)


def rate_filter_range_field_chk(rate, rate_range, field_name):
    """
    Rate range fileds (e.g. >,>=,=,<=,<)
    are checked.
    """
    kwargs = {}
    if rate_range != '' and rate != '':
        if rate_range == 'gte':
            kwargs[field_name + '__gte'] = rate
        if rate_range == 'gt':
            kwargs[field_name + '__gt'] = rate
        if rate_range == 'eq':
            kwargs[field_name] = rate
        if rate_range == 'lt':
            kwargs[field_name + '__lt'] = rate
        if rate_range == 'lte':
            kwargs[field_name + '__lte'] = rate
    return kwargs


def prfix_list():
    """
    Prefix List
    """
    list = Prefix.objects.all()
    LIST = map(lambda x: (int(x.prefix), int(x.prefix)), list)
    return LIST


def prefix_list_string(phone_number):
    """
    To return prefix string
    For Example :-
    phone_no = 34650784355
    prefix_string = (34650, 3465, 346, 34)
    """
    phone_number = str(phone_number)
    prefix_range = range(settings.PN_MIN_DIGITS,
                         settings.PN_MAX_DIGITS + 1)
    prefix_range.reverse()
    destination_prefix_list = ''
    for i in prefix_range:
        if i == settings.PN_MIN_DIGITS:
            destination_prefix_list = destination_prefix_list + \
            phone_number[0:i]
        else:
            destination_prefix_list = destination_prefix_list + \
            phone_number[0:i] + ', '
    return str(destination_prefix_list)


def simulator_function(request, view=None):
    """
    Common Simulator function for admin as well as client
    """
    destination_no = ''
    voipplan_id = ''
    error = ''
    if request.method == 'POST':
        destination_no = variable_value(request, "destination_no")
        voipplan_id = variable_value(request, "plan_id")
        try:
            isint(destination_no)
            
            from voip_billing.rate_engine import rate_engine

            if destination_no != '':
                query = rate_engine(destination_no=destination_no,
                                    voipplan_id=voipplan_id)
                data = []                
                if view == "admin":
                    for i in query:
                        c_r_plan = VoIPCarrierRate.objects.get(id=i.crid)
                        r_r_plan = VoIPRetailRate.objects.get(id=i.rrid)
                        data.append((voipplan_id,
                                     c_r_plan.voip_carrier_plan_id.id,
                                     c_r_plan.voip_carrier_plan_id.name,
                                     r_r_plan.voip_retail_plan_id.id,
                                     r_r_plan.voip_retail_plan_id.name,
                                     i.crid, i.carrier_rate,
                                     i.rrid, i.retail_rate, i.rt_prefix))
                else:  # view = "client"
                    for i in query:
                        r_r_plan = VoIPRetailRate.objects.get(id=i.rrid)
                        data.append((voipplan_id,
                                     r_r_plan.voip_retail_plan_id.name,
                                     i.retail_rate))
        except:
            error = _("Enter destination no !!")

    ctx = {
        'data': data,
        'error': error
    }
    return ctx


def rate_range():
    """
    Filter range symbol
    """
    LIST = (('', 'All'),
            ('gte', '>='),
            ('gt', '>'),
            ('eq', '='),
            ('lt', '<'),
            ('lte', '<='))
    return LIST


def banned_prefix_qs(voipplan_id):
    """
    Banned Prefix queryset should be cached
    """
    from django.db import connection, transaction
    cursor = connection.cursor()
    sql_statement = ('SELECT voipbilling_ban_prefix.prefix_id FROM '\
        'voipbilling_ban_prefix,voipbilling_banplan,voipbilling_voipplan_banplan '\
        'WHERE voipbilling_ban_prefix.ban_plan_id = voipbilling_banplan.id '\
        'AND voipbilling_banplan.id = voipbilling_voipplan_banplan.banplan_id '\
        'AND voipbilling_voipplan_banplan.voipplan_id = %s')
    cursor.execute(sql_statement, [str(voipplan_id)])
    row = cursor.fetchall()
    result = []
    for record in row:
        modrecord = {}
        modrecord['prefix'] = record[0]
        result.append(modrecord)
    return result


def prefix_allowed_to_voip_call(destination_number, voipplan_id):
    """
    Check destination no with ban prefix & voip_plan
    """
    destination_prefix_list = prefix_list_string(destination_number)
    banned_prefix_list = banned_prefix_qs(voipplan_id)
    # Cache the query set of banned prefix
    result = cache.get('test_key')
    if result is None:
        cache.set("test_key", banned_prefix_list, 60)
    flag = False
    for j in eval(destination_prefix_list):
        for i in banned_prefix_list:
            # Banned Prefix - VoIP call is not allowed
            if i['prefix'] == j:
                flag = True
                break
        # if flag is true
        # VoIP call is not allowed
        if flag:
            return False
    # VoIP call is allowed
    return True


def check_celeryd_process():
    """
    Check celeryd service running or not
    """
    process = os.popen("ps x | grep celeryd").read().splitlines()
    if len(process) > 2:
        return True
    else:
        return False