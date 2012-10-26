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
from django.utils.safestring import mark_safe


def mapreduce_default():
    """
    To get the default analytic of cdr

        * Total calls per year-month-day
        * Total duration per year-month-day
        * Avereage duration per year-month-day

    Attributes:

        * ``map`` - Grouping perform on year, month & day
        * ``reduce`` - Calculate call count, sum of call duration based on map
        * ``finalfc`` - To get avg of call duration
                        (sum_call_duration / sum_call_count)

    Result Collection: ``aggregate_result_dashboard``
    """
    map = mark_safe(u'''
        function(){
            emit( {
                        a_Year: this.start_uepoch.getFullYear(),
                        b_Month: this.start_uepoch.getMonth() + 1,
                        c_Day: this.start_uepoch.getDate(),
                    },
                    {
                        calldate__count: 1,
                        calldate: this.start_uepoch,
                        duration__sum: this.duration,
                        duration__avg: 0
                    } )
        }''')

    reduce = mark_safe(u'''
        function(key,vals) {
            var ret = {
                            calldate__count : 0,
                            duration__sum: 0,
                            duration__avg: 0
                       };

            for (var i=0; i < vals.length; i++){
                ret.calldate__count += parseInt(vals[i].calldate__count);
                ret.duration__sum += parseInt(vals[i].duration__sum);
            }
            return ret;
        }
        ''')

    finalfc = mark_safe(u'''
        function(key, value) {
                    if (parseInt(value.calldate__count) > 0)
                        value.duration__avg = parseFloat( parseFloat(value.duration__sum) / parseInt(value.calldate__count) );
                    return value;
        }''')

    out = 'aggregate_result_dashboard'

    return (map, reduce, finalfc, out)


def mapreduce_cdr_mail_report():
    """
    To get the previous day's analytic of cdr

       * Total calls per day-hour-min-country
       * Total duration per day-hour-min-country
       * Avereage duration per day-hour-min-country
       * Hangupcause per day-hour-min-country

    Attributes:

        * ``map`` - Grouping perform on day, hour, min & country_id
        * ``reduce`` - Calculate call count, sum of call duration,
                       hangup-causes based on map
        * ``finalfc`` - To get avg of call duration
                        (sum_call_duration / sum_call_count)

    Result Collection: ``aggregate_result_cdr_mail_report``
    """
    (map, reduce, finalfc, out) = mapreduce_default()
    map = mark_safe(u'''
        function(){
            emit( {
                        c_Day: this.start_uepoch.getDate(),
                        d_Hour: this.start_uepoch.getHours(),
                        e_Min: this.start_uepoch.getMinutes(),
                        f_Country: this.country_id,
                    },
                    {
                        calldate__count: 1,
                        duration__sum: this.duration,
                        duration__avg: 0,
                        hangup_cause_id: this.hangup_cause_id
                    } )
        }''')

    reduce = mark_safe(u'''
        function(key,vals) {
            var ret = {
                            calldate__count : 0,
                            duration__sum: 0,
                            duration__avg: 0,
                            hangup_cause_id: 0,
                       };

            for (var i=0; i < vals.length; i++){
                ret.calldate__count += parseInt(vals[i].calldate__count);
                ret.duration__sum += parseInt(vals[i].duration__sum);
                ret.hangup_cause_id = vals[i].hangup_cause_id;
            }
            return ret;
        }
        ''')

    finalfc = mark_safe(u'''
        function(key, value) {
                    if (parseInt(value.calldate__count) > 0)
                        value.duration__avg = parseFloat( parseFloat(value.duration__sum) / parseInt(value.calldate__count) );
                    return value;
        }''')

    out = 'aggregate_result_cdr_mail_report'
    return (map, reduce, finalfc, out)


def mapreduce_task_cdr_alert():
    """
    To get

       * xxxx

    Result Collection: ``aggregate_result_alert``
    """
    (map, reduce, finalfc, out) = mapreduce_default()

    map = mark_safe(u'''
        function(){
            emit( {
                        a_Year: this.start_uepoch.getFullYear(),
                        b_Month: this.start_uepoch.getMonth() + 1,
                   },
                   {
                        calldate__count: 1,
                        calldate: this.start_uepoch,
                        duration__sum: this.duration,
                        duration__avg: 0
                    } )
            }''')

    out = 'aggregate_result_alert'
    return (map, reduce, finalfc, out)


def mapreduce_cdr_hourly_report():
    """
    To get the hourly report of cdr

       * Total calls per year-month-day-hour-min
       * Total call duration per year-month-day

    Attributes:

        * ``map`` - Grouping perform on year, month & day
        * ``reduce`` - Calculate call count, sum of call duration,
                       based on map

    Result Collection: ``aggregate_cdr_hourly_report``
    """
    (map, reduce, finalfc, out) = mapreduce_default()

    # Get cdr graph by hour report
    map = mark_safe(u'''
        function(){
            emit(
                {
                    a_Year: this.metadata.date.getFullYear(),
                    b_Month: this.metadata.date.getMonth() + 1,
                    c_Day: this.metadata.date.getDate(),
                },
                {
                    calldate__count: this.call_hourly,
                    duration__sum: this.duration_hourly,
                }
            )
          }''')

    reduce = mark_safe(u'''
        function(key,vals) {
            var ret = {
                calldate__count : [],
                duration__sum: [],
            };
            for(var k=0; k < 24; k++){
                ret.calldate__count[k]=0;
                ret.duration__sum[k]=0;
            }
            for (var i=0; i < vals.length; i++) {
                for (var k=0; k < 24; k++) {
                    if (vals[i].calldate__count[k]) {
                        ret.calldate__count[k] += vals[i].calldate__count[k];
                        ret.duration__sum[k] += vals[i].duration__sum[k];
                    }
                }
            }
            return ret;
        }''')

    out = 'aggregate_cdr_hourly_report'
    return (map, reduce, False, out)


def mapreduce_hourly_overview():
    """
    To get the overview analytic of cdr

       * Total calls per year-month-day-switch
       * Total call duration per year-month-day-switch

    Attributes:

        * ``map`` - Grouping perform on year, month, day & switch
        * ``reduce`` - Calculate call count, sum of call duration based on map

    Result Collection: ``aggregate_hourly_overview``
    """
    (map, reduce, finalfc, out) = mapreduce_cdr_hourly_report()

    map = mark_safe(u'''
        function(){
            emit(
                {
                    a_Year: this.metadata.date.getFullYear(),
                    b_Month: this.metadata.date.getMonth() + 1,
                    c_Day: this.metadata.date.getDate(),
                    f_Switch: this.metadata.switch_id,
                },
                {
                    calldate__count: this.call_hourly,
                    duration__sum: this.duration_hourly,
                }
            )
          }''')

    out = 'aggregate_hourly_overview'
    return (map, reduce, False, out)


def mapreduce_hourly_country_report():
    """
    To get the overview analytic of cdr

       * Total calls per year-month-day-country
       * Total call duration per year-month-day-country

    Attributes:

        * ``map`` - Grouping perform on year, month, day & country
        * ``reduce`` - Calculate call count, sum of call duration based on map

    Result Collection: ``aggregate_hourly_country_report``
    """
    (map, reduce, finalfc, out) = mapreduce_cdr_hourly_report()

    map = mark_safe(u'''
        function(){
            emit(
                {
                    a_Year: this.metadata.date.getFullYear(),
                    b_Month: this.metadata.date.getMonth() + 1,
                    c_Day: this.metadata.date.getDate(),
                    f_Country: this.metadata.country_id,
                },
                {
                    calldate__count: this.call_hourly,
                    duration__sum: this.duration_hourly,
                }
            )
          }''')

    out = 'aggregate_hourly_country_report'
    return (map, reduce, False, out)
