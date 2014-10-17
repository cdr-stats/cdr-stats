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

from influxdb import InfluxDBClient


class Influx(object):
    """docstring for Influx"""

    def __init__(self, host, port, user, password, dbname, serie_name):
        """
        Constructor
        """
        self._host, self._port, self._user, self._password, self._dbname = host, port, user, password, dbname
        self.added_points = 0
        self.client = None
        self.columns = []
        self.serie_name = serie_name
        self._prepare_connect()

    def _prepare_connect(self):
        self.write_series = [{
            'name':    self.serie_name,
            'columns': self.columns,
            'points':  []
        }]
        self._connect_client()

    def _connect_client(self):
        """
        Configure the client to InfluxDB API
        """
        self.client = InfluxDBClient(self._host, self._port, self._user, self._password, self._dbname)

    def set_columns(self, new_columns):
        """
        Set the columns to new value new_columns
        """
        self.columns = new_columns
        self.write_series[0]['columns'] = new_columns

    def add_points(self, values):
        """
        Add points to the serie
        """
        self.added_points += 1
        self.write_series[0]['points'].append(values)

    def write_points(self):
        """
        write the serie to the InfluxDB client
        """
        print self.added_points
        print self.write_series
        if self.added_points > 0:
            self.added_points = 0
            self.client.write_points(self.write_series)
            # print self.write_series

    def delete_series(self):
        """
        delete the serie to the InfluxDB client
        """
        self.client.delete_series(self.serie_name)

    def empty_points(self):
        """
        Reset the json document used to write series
        """
        self.added_points = 0
        self.write_series = [{
            'name':    self.serie_name,
            'columns': self.columns,
            'points':  []
        }]

    def query(self, query):
        """
        Query Database

        Return first element
        """
        print query
        return self.client.query(query)[0]

    def create_database(self):
        """
        Create Database
        """
        self.client.create_database(self._dbname)

    def delete_database(self):
        """
        Delete Database
        """
        self.client.delete_database(self._dbname)

    def query_column_aggr_time_group(self, column='country_id', time_bucket='1h', past='15d', aggr='COUNT'):
        query = ("SELECT {0}({1}) FROM {2} GROUP BY {3}, time({4}) fill(0) "
                "WHERE time > now() - {5}").format(aggr, column, self.serie_name, column, time_bucket, past)
        result = self.query(query)
        # print("Result: {0}".format(result))
        return result

    def query_column_aggr_time(self, column='duration', time_bucket='1h', past='15d', aggr='MEAN'):
        """
        SELECT MEAN(duration) FROM cdr GROUP BY time(30m) fill(0) WHERE time > now() - 10h
        """
        query = ("SELECT {0}({1}) FROM {2} GROUP BY time({3}) fill(0) "
                "WHERE time > now() - {4}").format(aggr, column, self.serie_name, time_bucket, past)
        result = self.query(query)
        # print("Result: {0}".format(result))
        return result


class InfluxCDR(Influx):
    """docstring for InfluxCDR"""

    def __init__(self, *args, **kwargs):
        self.columns = ["time", "duration", "billsec", "country_id", "hangup_id", "switch_id", "user_id"]
        kwargs['serie_name'] = "cdr"
        super(InfluxCDR, self).__init__(*args, **kwargs)

    def query_country(self, past='2w'):
        """
        SELECT COUNT(country_id) FROM cdr GROUP BY country_id, time(1h) fill(0) where time > now() - 10h
        """
        return self.query_column_aggr_time_group(
            column='country_id', time_bucket='1h', past=past, aggr='COUNT')



"""
# SELECT MEAN(duration) FROM cdr GROUP BY time(30m) fill(0) WHERE time > now() - 10h
# SELECT mean(duration), mean(billsec), mean(country_id) FROM cdr GROUP BY time(1h) fill(0) WHERE time > now() - 5d

SELECT country_id, count(country_id) as res FROM cdr GROUP BY country_id, time(1h) fill(0) where time > now() - 10h

# WITH DISTINCT
# -------------
SELECT DISTINCT(country_id), COUNT(DISTINCT(country_id)) FROM cdr GROUP BY time(1h) fill(0) where time > now() - 10h


SELECT country_id, count(country_id) FROM cdr GROUP BY country_id, time(1d) fill(0) WHERE time > now() - 5d
SELECT count(country_id) FROM cdr GROUP BY country_id, time(1d) fill(0) WHERE time > now() - 5d

SELECT count(country_id) FROM cdr GROUP BY time(1h) where time > now() - 3h

SELECT country_id as time, count(country_id) from cdr GROUP BY country_id, time(1h) where time > now() - 3h

SELECT country_id, count(country_id) FROM cdr GROUP BY country_id, time(1d) fill(0) WHERE time > now() - 5d
"""