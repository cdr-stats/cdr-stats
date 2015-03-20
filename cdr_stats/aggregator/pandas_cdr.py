#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2014 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from django.db import connection
from aggregator.cdr import condition_switch_id, condition_user
import pandas as pd
from pandas.io import sql
import time


# TODO: move sqlquery to aggregator/cdr.py
sqlquery = """
    SELECT
        dateday,
        switch_id,
        coalesce(nbcalls,0) AS nbcalls,
        coalesce(duration,0) AS duration,
        coalesce(billsec,0) AS billsec,
        coalesce(buy_cost,0) AS buy_cost,
        coalesce(sell_cost,0) AS sell_cost
    FROM
        generate_series(
                        date_trunc('#INTERVAL#', %(start_date)s),
                        date_trunc('#INTERVAL#', %(end_date)s),
                        '1 #INTERVAL#')
        as dateday
    LEFT OUTER JOIN (
        SELECT
            date_trunc('#INTERVAL#', starting_date) as time_interval,
            switch_id as switch_id,
            SUM(nbcalls) as nbcalls,
            SUM(duration) as duration,
            SUM(billsec) as billsec,
            SUM(buy_cost) as buy_cost,
            SUM(sell_cost) as sell_cost
        FROM matv_voip_cdr_aggr_hour
        WHERE
            starting_date > date_trunc('#INTERVAL#', %(start_date)s) and
            starting_date <= date_trunc('#INTERVAL#', %(end_date)s)
            #USER_CONDITION#
            #SWITCH_CONDITION#
        GROUP BY time_interval, switch_id
        ) results
    ON (dateday = results.time_interval)"""


def conv_timestamp(date):
    """
    function to be used by map to convert list of datetime to timestamp
    """
    return int(1000 * time.mktime(date.timetuple()))


def get_report_cdr_per_switch(user, interval, start_date, end_date, switch_id):
    """
    Use pandas to prepare series to display cdr hour report per switch

    **Attributes**:

        - interval: this could be hour / day / week / month
        - start_date: start date
        - end_date: end date
        - switch_id: id of the switch (0 is all)
    """
    series = {}
    subsqlquery = sqlquery.replace("#USER_CONDITION#", condition_user(user))
    subsqlquery = subsqlquery.replace("#SWITCH_CONDITION#", condition_switch_id(switch_id))
    subsqlquery = subsqlquery.replace("#INTERVAL#", interval)
    params = {
        'start_date': start_date,
        'end_date': end_date,
    }
    df = sql.read_sql_query(subsqlquery, connection, params=params)
    table = pd.tools.pivot.pivot_table(df,
        values=['nbcalls', 'duration', 'billsec', 'buy_cost', 'sell_cost'],
        index=['dateday'],
        columns=['switch_id'],
        fill_value=0)
    metric_list = ['nbcalls', 'duration', 'billsec', 'buy_cost', 'sell_cost']

    # build a serie for each metric
    for metric in metric_list:
        series[metric] = {}
        # list_columns, ie for switches [1.0, 2.0]
        list_columns = table[metric].columns.tolist()
        list_columns = map(int, list_columns)

        # Transpose
        ntable = table[metric].T
        # Build the result dictionary
        series[metric]['columns'] = list_columns
        series[metric]['x_date'] = list(table.index)
        # convert into timestamp value
        series[metric]['x_timestamp'] = map(conv_timestamp, list(table.index))
        series[metric]['values'] = {}

        valsum = 0
        for col in list_columns:
            series[metric]['values'][str(col)] = list(ntable.loc[col])
            # valsum += map(sum, list(ntable.loc[col]))
            for i in list(ntable.loc[col]):
                valsum += i
        series[metric]['total'] = valsum
    return series
