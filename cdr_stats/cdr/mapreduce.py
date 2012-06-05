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
                        f_Con: this.country_id,
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


def mapreduce_cdr_view():
    """
    Used default map-reduce function

    Result Collection: ``aggregate_result_cdr_view``
    """

    (map, reduce, finalfc, out) = mapreduce_default()

    out = 'aggregate_result_cdr_view'
    return (map, reduce, finalfc, out)


def mapreduce_cdr_dashboard():
    """
    To get the minutly analytic of cdr

       * Total calls per year-month-day-hour-min
       * Total call duration per year-month-day-hour-min
       * Total hangup-cause  per year-month-day-hour-min

    Attributes:

        * ``map`` - Grouping perform on year, month, day, hour & min
        * ``reduce`` - Calculate call count, sum of call duration,
                       hangupcause based on map

    Result Collection: ``aggregate_result_cdr_dashboard_report``
    """
    (map, reduce, finalfc, out) = mapreduce_default()

    # Get cdr graph by hour report
    map = mark_safe(u'''
        function(){
            var year = this.start_uepoch.getFullYear();
            var month = this.start_uepoch.getMonth();
            var day = this.start_uepoch.getDate();
            var hours = this.start_uepoch.getHours();
            var minutes = this.start_uepoch.getMinutes();
            var d = new Date(year, month, day, hours, minutes);
            emit( {
                g_Millisec: d.getTime(),
            },
            {
                calldate__count: 1,
                duration__sum: this.duration,
                hangup_cause_id: this.hangup_cause_id,
            } )
          }''')
    reduce = mark_safe(u'''
        function(key,vals) {
            var ret = {
                calldate__count : 0,
                duration__sum: 0,
                hangup_cause_id: 0,
            };
            for (var i=0; i < vals.length; i++){
                ret.calldate__count += parseInt(vals[i].calldate__count);
                ret.duration__sum += parseInt(vals[i].duration__sum);
                ret.hangup_cause_id = vals[i].hangup_cause_id;
            }
            return ret;
        }''')
    out = 'aggregate_result_cdr_dashboard_report'
    return (map, reduce, False, out)


def mapreduce_cdr_country_report():
    """
    To get the countries call analytic

       * Total calls per day-country
       * Total call duration day-country

    Attributes:

        * ``map`` - Grouping perform on year, month, day, hour, min & country
        * ``reduce`` - Calculate call count, sum of call duration based on map

    Result Collection: ``aggregate_result_cdr_country_report``
    """
    (map, reduce, finalfc, out) = mapreduce_default()

    # Get cdr dashboard report
    map = mark_safe(u'''
        function(){
            var year = this.start_uepoch.getFullYear();
            var month = this.start_uepoch.getMonth();
            var day = this.start_uepoch.getDate();
            var hours = this.start_uepoch.getHours();
            var minutes = this.start_uepoch.getMinutes();
            var d = new Date(year, month, day, hours, minutes);
            emit(
                {
                    f_Con: this.country_id,
                    g_Millisec: d.getTime(),
                },
                {
                    calldate__count: 1,
                    duration__sum: this.duration,
                })
        }''')

    reduce = mark_safe(u'''
        function(key,vals) {
            var ret = {
                        calldate__count : 0,
                        duration__sum: 0,
                      };

            for (var i=0; i < vals.length; i++){
                    ret.calldate__count += parseInt(vals[i].calldate__count);
                    ret.duration__sum += parseInt(vals[i].duration__sum);
            }
            return ret;
        }
        ''')

    out = 'aggregate_result_cdr_country_report'
    return (map, reduce, False, out)


def mapreduce_cdr_world_report():
    """
    To get the all countries call analytic

       * Total calls per country
       * Total call duration per country

    Attributes:

        * ``map`` - Grouping perform on country
        * ``reduce`` - Calculate call count, sum of call duration based on map

    Result Collection: ``aggregate_result_cdr_world_report``
    """
    (map, reduce, finalfc, out) = mapreduce_default()

    # Get cdr world report
    map = mark_safe(u'''
        function(){
            emit(
                {
                    f_Con: this.country_id,
                },
                {
                    calldate__count: 1,
                    duration__sum: this.duration,
                })
        }''')

    reduce = mark_safe(u'''
        function(key,vals) {
            var ret = {
                        calldate__count : 0,
                        duration__sum: 0,
                    };

            for (var i=0; i < vals.length; i++){
                    ret.calldate__count += parseInt(vals[i].calldate__count);
                    ret.duration__sum += parseInt(vals[i].duration__sum);
            }
            return ret;
        }
        ''')

    out = 'aggregate_result_cdr_world_report'
    return (map, reduce, False, out)


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
                    call__count: this.call_hourly,
                    duration__sum: this.duration_hourly,
                }
            )
          }''')

    reduce = mark_safe(u'''
        function(key,vals) {
            var ret = {
                call__count : [],
                duration__sum: [],
            };
            for(var k=0; k < 24; k++){
                ret.call__count[k]=0;
                ret.duration__sum[k]=0;
            }
            for (var i=0; i < vals.length; i++) {
                for (var k=0; k < 24; k++) {
                    if (vals[i].call__count[k]) {
                        ret.call__count[k] += vals[i].call__count[k];
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

       * Total calls per year-month-day-hour-switch
       * Total call duration per year-month-day-hour-switch

    Attributes:

        * ``map`` - Grouping perform on year, month, day, hour & switch
        * ``reduce`` - Calculate call count, sum of call duration based on map

    Result Collection: ``aggregate_hourly_overview``
    """
    (map, reduce, finalfc, out) = mapreduce_default()

    # Get cdr graph by overview report
    map = mark_safe(u'''
        function(){
            emit( {
                    a_Year: this.metadata.date.getFullYear(),
                    b_Month: this.metadata.date.getMonth() + 1,
                    c_Day: this.metadata.date.getDate(),
                    f_Switch: this.metadata.switch_id,
            },
            {
                    call__count: this.call_minute,
                    duration__sum: this.duration_minute,
            } )
        }''')

    reduce = mark_safe(u'''
        function(key,vals) {
            var result = new Object();

            for(var k=0; k < 24; k++){
                for(var l=0; l < 60; l++){
                    if (k < 10) {
                        rkey = '0' + k + ':';
                    } else {
                        rkey = k + ':';
                    }
                    if (l < 10) {
                        rkey = rkey + '0' + l;
                    } else {
                        rkey = rkey + l;
                    }
                    result['c/'+rkey] = 0;
                    result['d/'+rkey] = 0;
                }
            }
            for (var i=0; i < vals.length; i++) {
                for (var k=0; k < 24; k++) {
                    for(var l=0; l < 60; l++){
                        if (k < 10) {
                            rkey = '0' + k + ':';
                        } else {
                            rkey = k + ':';
                        }
                        if (l < 10) {
                            rkey = rkey + '0' + l;
                        } else {
                            rkey = rkey + l;
                        }

                        if (vals[i].call__count[k] && vals[i].call__count[k][l] && parseInt(vals[i].call__count[k][l]) != 0) {
                            result['c/'+rkey] += parseInt(vals[i].call__count[k][l]);
                            if (vals[i].duration__sum[k] && vals[i].duration__sum[k][l]) {
                                result['d/'+rkey] += parseInt(vals[i].duration__sum[k][l]);
                            }
                        }
                    }
                }
            }

            return result;
        }''')

    out = 'aggregate_hourly_overview'
    return (map, reduce, False, out)


def mapreduce_daily_overview():
    """
    To get the daily analytic of cdr

       * Total calls per year-month-day-switch
       * Total call duration per year-month-day-switch

    Attributes:

        * ``map`` - Grouping perform on year, month, day & switch
        * ``reduce`` - Calculate call count based on map

    Result Collection: ``aggregate_daily_overview``
    """
    (map, reduce, finalfc, out) = mapreduce_default()

    # Get cdr graph by day report
    map = mark_safe(u'''
        function(){
            var year = this.metadata.date.getFullYear();
            var month = this.metadata.date.getMonth();
            var day = this.metadata.date.getDate();

            var d = new Date(year, month, day);
            emit( {
                    f_Switch: this.metadata.switch_id,
                    g_Millisec: d.getTime(),
                  },
                  {
                    calldate__count: this.call_daily,
                    duration__sum: this.duration_daily
                  } );
        }''')

    out = 'aggregate_daily_overview'
    return (map, reduce, False, out)


def mapreduce_monthly_overview():
    """
    To get the overview analytic of cdr

       * Total calls per year-month-switch
       * Total call duration per year-month-switch

    Attributes:

        * ``map`` - Grouping perform on year, month & switch
        * ``reduce`` - Calculate call count, sum of call duration based on map

    Result Collection: ``aggregate_monthly_overview``
    """
    (map, reduce, finalfc, out) = mapreduce_default()

    # Get cdr graph by overview report
    map = mark_safe(u'''
        function(){
            var year = this.metadata.date.getFullYear();
            var month = this.metadata.date.getMonth();

            var d = new Date(year, month);
            emit( {
                f_Switch: this.metadata.switch_id,
                g_Millisec: d.getTime(),
            },
            {
                calldate__count: this.call_monthly,
                duration__sum: this.duration_monthly
            } )
          }''')

    out = 'aggregate_monthly_overview'
    return (map, reduce, False, out)


def mapreduce_country_report():
    """
    To get the countries call report

       * Total calls per day-country-switch_id
       * Total call duration day-country-switch_id

    Attributes:

        * ``map`` - Grouping perform on year, month, day, switch_id & country_id
        * ``reduce`` - Calculate call count, sum of call duration based on map

    Result Collection: ``aggregate_country_report``
    """
    (map, reduce, finalfc, out) = mapreduce_hourly_overview()

    # Get cdr country report
    map = mark_safe(u'''
        function(){
            emit( {
                    a_Year: this.metadata.date.getFullYear(),
                    b_Month: this.metadata.date.getMonth() + 1,
                    c_Day: this.metadata.date.getDate(),
                    f_Switch: this.metadata.switch_id,
                    country_id : this.metadata.country_id,
            },
            {
                    calldate__count: this.call_minute,
                    duration__sum: this.duration_minute,
            } )
        }''')

    out = 'aggregate_country_report'
    return (map, reduce, False, out)


def mapreduce_world_report():
    """
    To get the world map report of cdr

       * Total calls per country_id
       * Total call duration country_id

    Attributes:

        * ``map`` - Grouping perform on country_id
        * ``reduce`` - Calculate call count based on map

    Result Collection: ``aggregate_world_report``
    """
    (map, reduce, finalfc, out) = mapreduce_default()

    # Get cdr graph by day report
    map = mark_safe(u'''
        function(){

            emit( {
                    f_Con: this.metadata.country_id,
                  },
                  {
                    calldate__count: this.call_daily,
                    duration__sum: this.duration_daily
                  } );
        }''')

    out = 'aggregate_world_report'
    return (map, reduce, False, out)

