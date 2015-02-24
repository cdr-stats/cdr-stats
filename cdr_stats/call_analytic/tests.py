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

# Usage:
# Run test: python manage.py test --settings=cdr_stats.settings_test call_analytic --with-xtraceback --with-color --verbosity=1
#

from django.test import TestCase
from call_analytic.cdr import InfluxCDR
from django.conf import settings
from influxdb.client import InfluxDBClientError
# import random


class TestInfluxCDR(TestCase):
    """Test TestInfluxCDR"""

    def setUp(self):
        self.testdbname = 'cdrstats'
        self.influxcdr = InfluxCDR(
            settings.INFLUXDB_HOST, settings.INFLUXDB_PORT,
            settings.INFLUXDB_USER, settings.INFLUXDB_PASSWORD,
            self.testdbname)
        try:
            self.influxcdr.create_database()
        except InfluxDBClientError:
            print "create_database failed: DB already created..."
            pass

    def test_delete_series(self):
        self.influxcdr.delete_series()

    def test_add_points(self):
        self.influxcdr.set_columns(
            ["time", "duration", "billsec", "country_id", "hangup_id", "switch_id", "user_id"])
        self.influxcdr.add_points([1413460800, 10, 8, 55, 16, 1, 1])
        self.influxcdr.add_points([1413460802, 25, 20, 55, 16, 1, 1])
        self.influxcdr.commit()

    def test_generate_points_lastdays(self):
        import datetime
        import random

        self.influxcdr.set_columns(
            ["time", "duration", "billsec", "country_id", "hangup_id", "switch_id", "user_id"])

        nb_day = 3  # number of day to generate time series
        timeinterval_min = 10  # create an event every x minutes
        total_minutes = 1440 * nb_day
        total_records = int(total_minutes / timeinterval_min)
        now = datetime.datetime.today()

        # generate data for 2 switches
        for switch_id in range(1, 2):
            # loop on the totalrecords to create
            for i in range(0, total_records):
                past_date = now - datetime.timedelta(minutes=i * timeinterval_min)
                billsec = random.randint(10, 50)
                duration = billsec + random.randint(5, 10)
                country_id = 10 + random.randint(10, 40)
                hangup_id = 1 + random.randint(10, 16)
                user_id = 1
                # add points
                self.influxcdr.add_points([
                    int(past_date.strftime('%s')),
                    duration,
                    billsec,
                    country_id,
                    hangup_id, switch_id, user_id])

        self.influxcdr.commit()
        # assert False

    def test_query_cdr_last_two_week(self):
        result = self.influxcdr.query_column_aggr_time(
            column='duration', time_bucket='1h', past='15d', aggr='MEAN')
        self.assertEqual(len(result['points']), 361)

    def test_query_country_aggr_time(self):

        result = self.influxcdr.query_country(past='1d')
        val = len(result['points'])
        result = {}
        self.assertEqual(val, 775)

    # def tearDown(self):
    #     """Delete created object"""
    #     self.influxcdr.empty_points()
    #     self.influxcdr.delete_database()
