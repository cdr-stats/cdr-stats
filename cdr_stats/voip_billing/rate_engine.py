#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2013 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from voip_billing.models import VoIPRetailPlan
from voip_billing.function_def import prefix_list_string


def rate_engine(voipplan_id, dest_number):
    """
    To determine the cost of the voip call and get provider/gateway
    to use to deliver the call.
    """

    if not voipplan_id or not dest_number:
        return []

    dest_prefix = prefix_list_string(str(dest_number))
    if not dest_prefix:
        return []

    #Build SQL query to rate calls
    sql = 'SELECT rpid as id, cpid, cr_prefix, prefix as rt_prefix, rrid, \
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
                WHERE voipbilling_voip_retail_rate.prefix IN (%s) \
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
            WHERE voipbilling_voipplan_voipcarrierplan.voipplan_id = %s AND \
                voipbilling_voipplan_voipcarrierplan.voipcarrierplan_id = voipbilling_voip_carrier_plan.id AND \
                voipbilling_voip_carrier_rate.voip_carrier_plan_id = voipbilling_voip_carrier_plan.id AND \
                voipbilling_voip_carrier_rate.prefix IN (%s) AND \
                voipbilling_voip_carrier_plan.voip_provider_id = voip_provider.id\
            ORDER BY voipbilling_voip_carrier_plan.id, cr_prefix DESC, allsellrates.prefix DESC \
        ) AS bothrates \
        ORDER BY cr_prefix DESC, rt_prefix DESC, \
        sum_metric ASC, carrier_rate ASC, retail_rate ASC LIMIT 1' % \
        (str(dest_prefix), str(voipplan_id), str(voipplan_id), str(dest_prefix))
    qset = VoIPRetailPlan.objects.raw(sql)

    # table = []
    # for i in qset:
    #     table.append([i.id, i.cpid, i.cr_prefix, i.rt_prefix, i.rrid, i.carrier_rate,\
    #         i.retail_rate , i.crid, i.provider_id, i.gateway_id, i.sum_metric])
    #     from tabulate import tabulate
    #     print tabulate(table, headers=['i.id', 'i.cpid', 'i.cr_prefix', 'i.rt_prefix', 'i.rrid', 'i.carrier_rate',\
    #             'i.retail_rate ', 'i.crid', 'i.provider_id', 'i.gateway_id', 'i.sum_metric'])

    return qset
