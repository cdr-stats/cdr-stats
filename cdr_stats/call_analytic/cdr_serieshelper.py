#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2015 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#


from influxdb import InfluxDBClient
from influxdb import SeriesHelper


# InfluxDB connections settings
host = 'localhost'
port = 8086
user = 'root'
password = 'root'
dbname = 'mydb'

myclient = InfluxDBClient(host, port, user, password, dbname)


class CDRSeriesHelper(SeriesHelper):
    # Meta class stores time series helper configuration.

    class Meta:
        # The client should be an instance of InfluxDBClient.
        client = myclient
        # The series name must be a string. Add dependent fields/tags in curly brackets.
        series_name = 'events.stats.{server_name}'
        # Defines all the fields in this time series.
        fields = ['some_stat', 'other_stat']
        # Defines all the tags for the series.
        tags = ['server_name']
        # Defines the number of data points to store prior to writing on the wire.
        bulk_size = 5
        # autocommit must be set to True when using bulk_size
        autocommit = True


# The following will create *five* (immutable) data points.
# Since bulk_size is set to 5, upon the fifth construction call, *all* data
# points will be written on the wire via CDRSeriesHelper.Meta.client.
CDRSeriesHelper(server_name='us.east-1', some_stat=159, other_stat=10)
CDRSeriesHelper(server_name='us.east-1', some_stat=158, other_stat=20)
CDRSeriesHelper(server_name='us.east-1', some_stat=157, other_stat=30)
CDRSeriesHelper(server_name='us.east-1', some_stat=156, other_stat=40)
CDRSeriesHelper(server_name='us.east-1', some_stat=155, other_stat=50)

# self.influxdbcdr.set_columns(
#             ["time", "duration", "billsec", "country_id", "hangup_id", "switch_id", "user_id"])
# self.influxdbcdr.add_points([1413460800, 10, 8, 55, 16, 1, 1])
