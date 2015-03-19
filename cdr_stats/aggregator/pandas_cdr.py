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
# from datetime import datetime, date, timedelta
import pandas as pd
from pandas.io import sql
# import numpy as np


def prepare_cdr_hour_report_per_switch():
    df = sql.read_sql_query("""SELECT
        dateday,
        switch_id,
        coalesce(nbcalls,0) AS nbcalls,
        coalesce(duration,0) AS duration,
        coalesce(billsec,0) AS billsec,
        coalesce(buy_cost,0) AS buy_cost,
        coalesce(sell_cost,0) AS sell_cost
    FROM
        generate_series(
                        date_trunc('hour', current_timestamp - interval '6' hour),
                        date_trunc('hour', current_timestamp + interval '2' hour),
                        '1 hour')
        as dateday
    LEFT OUTER JOIN (
        SELECT
            date_trunc('hour', starting_date) as dayhour,
            switch_id as switch_id,
            SUM(nbcalls) as nbcalls,
            SUM(duration) as duration,
            SUM(billsec) as billsec,
            SUM(buy_cost) as buy_cost,
            SUM(sell_cost) as sell_cost
        FROM matv_voip_cdr_aggr_hour
        WHERE
            starting_date > date_trunc('hour', current_timestamp - interval '6' hour) and
            starting_date <= date_trunc('hour', current_timestamp + interval '2' hour)

        GROUP BY dayhour, switch_id
        ) results
    ON (dateday = results.dayhour)""", connection, index_col=["dateday", "switch_id"])
    print df
    table = pd.tools.pivot.pivot_table(df,
        values=['nbcalls', 'duration', 'billsec', 'buy_cost', 'sell_cost'],
        index=['dateday'],
        columns=['switch_id'],
        fill_value=0)
    print table.nbcalls

    num_column = len(table.nbcalls.columns.tolist())
    # list_column, ie for switches [1.0, 2.0]
    list_column = table.nbcalls.columns.tolist()

    first_column = table.nbcalls.columns.tolist()[0]
    second_column = table.nbcalls.columns.tolist()[1]

    print (num_column, list_column, first_column, second_column)

    # Transpose
    ntable = table.nbcalls.T
    # List of values for nbcalls second_column
    for i in ntable.loc[second_column]:
        print i

    # display dates
    for i in table.index:
        print i
        # 2015-03-19 12:00:00+01:00
        # 2015-03-19 13:00:00+01:00
        # 2015-03-19 14:00:00+01:00
