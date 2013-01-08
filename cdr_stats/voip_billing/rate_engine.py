from country_dialcode.models import Prefix
from voip_billing.models import *
from voip_report.models import *
from voip_billing.function_def import *
from datetime import *


def rate_engine(voipcall_id=None, voipplan_id=None, destination_no=None):
    """
    To determine the cost of the voip call and get provider/gateway
    to use to deliver the call.
    """
    if voipcall_id is not None:
        voipcall = VoIPCall.objects.get(pk=voipcall_id)

    if destination_no is not None:
        destination_prefix_list = prefix_list_string(str(destination_no))
    else:
        destination_prefix_list = \
        prefix_list_string(str(voipcall.recipient_number))

    #destination_prefix_list = '34, 346, 3465, 34650'
    #voipplan_id = 1
    query = VoIPRetailPlan.objects.raw(
        'SELECT rpid as id, cpid, cr_prefix, prefix as rt_prefix, rrid, \
        carrier_rate, retail_rate, crid, provider_id, gateway_id, sum_metric \
        FROM ( \
            SELECT DISTINCT allsellrates.*, \
                    voipbilling_voip_carrier_rate.id AS crid, \
                    voipbilling_voip_carrier_rate.prefix AS cr_prefix, \
                    voip_provider.id AS provider_id, \
                    voip_provider.gateway_id AS gateway_id, \
                    voipbilling_voip_carrier_rate.carrier_rate,\
                    (voipbilling_voip_carrier_plan.metric + \
                     allsellrates.metric + voip_provider.metric)\
                     AS sum_metric, \
                     voipbilling_voip_carrier_plan.id AS cpid \
            FROM ( \
            SELECT DISTINCT voipbilling_voip_retail_plan.id AS rpid, \
                    voipbilling_voip_retail_rate.prefix, \
                    voipbilling_voip_retail_rate.id AS rrid, \
                    voipbilling_voip_retail_rate.retail_rate AS retail_rate, \
                    voipbilling_voip_retail_plan.metric AS metric \
                    FROM voipbilling_voip_retail_rate, \
                         voipbilling_voip_retail_plan, \
                         voipbilling_voipplan_voipretailplan \
                    WHERE voipbilling_voip_retail_rate.prefix IN  (%s) \
                    AND voipbilling_voip_retail_plan.id = \
                        voipbilling_voip_retail_rate.voip_retail_plan_id \
                    AND voipbilling_voipplan_voipretailplan.voipplan_id = %s \
                    AND voipbilling_voipplan_voipretailplan.voipretailplan_id \
                        = voipbilling_voip_retail_plan.id \
                    ORDER BY length(prefix) DESC, retail_rate ASC\
                    )  AS allsellrates, \
                    voipbilling_voip_carrier_rate, simu_prefix, \
                    voipbilling_voipplan_voipcarrierplan, \
                    voipbilling_voip_carrier_plan, voip_provider \
            WHERE voipbilling_voipplan_voipcarrierplan.voipplan_id = %s \
                    AND \
            voipbilling_voipplan_voipcarrierplan.voipcarrierplan_id = \
            voipbilling_voip_carrier_plan.id \
                    AND \
            voipbilling_voip_carrier_rate.voip_carrier_plan_id = \
            voipbilling_voip_carrier_plan.id \
                    AND voipbilling_voip_carrier_rate.prefix IN  (%s) \
                    AND \
            voipbilling_voip_carrier_plan.voip_provider_id = voip_provider.id\
                    ORDER BY voipbilling_voip_carrier_plan.id, \
                             length(cr_prefix) DESC, \
                             length(allsellrates.prefix) DESC \
        ) AS bothrates \
        ORDER BY length(cr_prefix) DESC, length(rt_prefix) DESC, \
        sum_metric ASC, carrier_rate ASC, retail_rate ASC LIMIT 0, 1' % \
        (destination_prefix_list, str(voipplan_id), str(voipplan_id),
        destination_prefix_list))

    # This return is used by rate simulator
    # (admin + client)
    if destination_no is not None:
        return query

    data = ''

    for i in query:
        #print "rpid: %d, cpid: %d, cr_prefix: %d, rt_prefix: %d, rrid: %d, \
        # carrier_rate: %f, retail_rate: %f, crid: %d,\
        # provider_id: %d, gateway_id: %d, sum_metric: %d " % \
        # (i.id, i.cpid, i.cr_prefix, i.rt_prefix, i.rrid, i.carrier_rate,
        # i.retail_rate , i.crid, i.provider_id, i.gateway_id, i.sum_metric)
        data = i

    # Create VoIP report record
    obj = VoIPCall_Report()
    obj.voipcall_ptr_id = voipcall.id
    if data != '':
        obj.carrier_cost = data.carrier_rate
        obj.carrier_rate_id = data.crid
        obj.retail_cost = data.retail_rate
        obj.retail_rate_id = data.rrid
        obj.gateway_id = data.gateway_id
        voipcall.prefix = Prefix.objects.get(prefix=data.rt_prefix)
    else:
        voipcall.disposition = 20 # No Route

    obj.voipplan_id = voipplan_id
    obj.user_id = voipcall.user_id
    obj.starting_date = voipcall.starting_date
    obj.created_date = datetime.now()
    obj.updated_date = datetime.now()

    obj.save()
    voipcall.save()

    result_data = {}
    result_data = {'voipcall_id': voipcall.id}

    # This return is used by voip call task
    # to determine gateway
    if data != "":  # Return Gateway ID
        result_data['gateway_id'] = int(data.gateway_id)
        return result_data
    else:  # Default Gateway ID
        #result_data['gateway_id'] = int(2)
        return result_data
