#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2012 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from country_dialcode.models import Prefix
from voip_billing.models import VoIPRetailPlan
from voip_billing.function_def import prefix_list_string
from datetime import datetime


def rate_engine(voipcall_id=None, voipplan_id=None, destination_no=None):
    """
    To determine the cost of the voip call and get provider/gateway
    to use to deliver the call.
    """
    if voipcall_id is not None:
        #TODO : check with cdr_common
        #voipcall = VoIPCall.objects.get(pk=voipcall_id)
        voipcall = ''
        pass

    if destination_no is not None:
        destination_prefix_list = prefix_list_string(str(destination_no))
    else:
        destination_prefix_list = prefix_list_string(str(voipcall.recipient_number))

    #destination_prefix_list = '34, 346, 3465, 34650'
    #voipplan_id = 1

    # updated query For postgresql
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
                    ORDER BY prefix DESC, retail_rate ASC\
                    )  AS allsellrates, dialcode_prefix,\
                    voipbilling_voip_carrier_rate, \
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
                             cr_prefix DESC, \
                             allsellrates.prefix DESC \
        ) AS bothrates \
        ORDER BY cr_prefix DESC, rt_prefix DESC, \
        sum_metric ASC, carrier_rate ASC, retail_rate ASC LIMIT 1' %\
        (str(destination_prefix_list), str(voipplan_id), str(voipplan_id), str(destination_prefix_list)))

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

    # TODO: Create VoIP report record    
    

    result_data = {'voipcall_id': 1} #voipcall.id

    # This return is used by voip call task
    # to determine gateway
    if data != "":  # Return Gateway ID
        result_data['gateway_id'] = int(data.gateway_id)
        return result_data
    else:  # Default Gateway ID
        #result_data['gateway_id'] = int(2)
        return result_data
