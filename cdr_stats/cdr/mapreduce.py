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
        * ``finalize_fun`` - To get avg of call duration (sum_call_duration / sum_call_count)

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

    finalize_fun = mark_safe(u'''
        function(key, value) {
                    if (parseInt(value.calldate__count) > 0)
                        value.duration__avg = parseFloat( parseFloat(value.duration__sum) / parseInt(value.calldate__count) );
                    return value;
        }''')

    out = 'aggregate_result_dashboard'

    return (map, reduce, finalize_fun, out)


def mapreduce_cdr_mail_report():
    """
    To get the previous day's analytic of cdr

       * Total calls per day-hour-min-country
       * Total duration per day-hour-min-country
       * Avereage duration per day-hour-min-country
       * Hangupcause per day-hour-min-country

    Attributes:

        * ``map`` - Grouping perform on day, hour, min & country_id
        * ``reduce`` - Calculate call count, sum of call duration, hangup-causes based on map
        * ``finalize_fun`` - To get avg of call duration (sum_call_duration / sum_call_count)

    Result Collection: ``aggregate_result_cdr_mail_report``
    """
    (map, reduce, finalize_fun, out) = mapreduce_default()
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

    finalize_fun = mark_safe(u'''
        function(key, value) {
                    if (parseInt(value.calldate__count) > 0)
                        value.duration__avg = parseFloat( parseFloat(value.duration__sum) / parseInt(value.calldate__count) );
                    return value;
        }''')

    out = 'aggregate_result_cdr_mail_report'
    return (map, reduce, finalize_fun, out)


def mapreduce_cdr_view():
    """
    Used default map-reduce function

    Result Collection: ``aggregate_result_cdr_view``
    """

    (map, reduce, finalize_fun, out) = mapreduce_default()

    out = 'aggregate_result_cdr_view'
    return (map, reduce, finalize_fun, out)


def mapreduce_cdr_hour_report():
    """
    To get the hourly analytic of cdr

       * Total calls per year-month-day-hour-min
       * Total call duration per year-month-day-hour-min

    Attributes:

        * ``map`` - Grouping perform on year, month, day, hour & min
        * ``reduce`` - Calculate call count, sum of call duration based on map

    Result Collection: ``aggregate_result_cdr_hour_report``
    """
    (map, reduce, finalize_fun, out) = mapreduce_default()

    # Get cdr graph by hour report
    map = mark_safe(u'''
        function(){
            emit( {
                a_Year: this.start_uepoch.getFullYear(),
                b_Month: this.start_uepoch.getMonth() + 1,
                c_Day: this.start_uepoch.getDate(),
                d_Hour: this.start_uepoch.getHours(),
                e_Min: this.start_uepoch.getMinutes(),
            },
            {
                calldate__count: 1, calldate:this.start_uepoch,
                duration__sum: this.duration
            } )
          }''')
    reduce = mark_safe(u'''
        function(key,vals) {
            var ret = {
                calldate__count : 0,
                duration__sum: 0,
                calldate: '',
            };
            for (var i=0; i < vals.length; i++){
                ret.calldate__count += parseInt(vals[i].calldate__count);
                ret.duration__sum += parseInt(vals[i].duration__sum);
                ret.calldate = vals[i].calldate;
            }
            return ret;
        }''')
    out = 'aggregate_result_cdr_hour_report'
    return (map, reduce, False, out)


def mapreduce_cdr_hourly_overview():
    """
    To get the overview analytic of cdr

       * Total calls per year-month-day-hour-switch
       * Total call duration per year-month-day-hour-switch

    Attributes:

        * ``map`` - Grouping perform on year, month, day, hour & switch
        * ``reduce`` - Calculate call count, sum of call duration based on map

    Result Collection: ``aggregate_result_cdr_hourly_overview``
    """
    (map, reduce, finalize_fun, out) = mapreduce_default()

    # Get cdr graph by overview report
    map = mark_safe(u'''
        function(){
            emit( {
                a_Year: this.start_uepoch.getFullYear(),
                b_Month: this.start_uepoch.getMonth() + 1,
                c_Day: this.start_uepoch.getDate(),
                d_Hour: this.start_uepoch.getHours(),
                f_Switch: this.switch_id
            },
            {
                calldate__count: 1,
                duration__sum: this.duration
            } )
          }''')

    out = 'aggregate_result_cdr_hourly_overview'
    return (map, reduce, False, out)


def mapreduce_cdr_monthly_overview():
    """
    To get the overview analytic of cdr

       * Total calls per year-month-switch
       * Total call duration per year-month-switch

    Attributes:

        * ``map`` - Grouping perform on year, month & switch
        * ``reduce`` - Calculate call count, sum of call duration based on map

    Result Collection: ``aggregate_result_cdr_monthly_overview``
    """
    (map, reduce, finalize_fun, out) = mapreduce_default()

    # Get cdr graph by overview report
    map = mark_safe(u'''
        function(){
            emit( {
                a_Year: this.start_uepoch.getFullYear(),
                b_Month: this.start_uepoch.getMonth() + 1,
                f_Switch: this.switch_id
            },
            {
                calldate__count: 1,
                duration__sum: this.duration
            } )
          }''')

    out = 'aggregate_result_cdr_monthly_overview'
    return (map, reduce, False, out)


def mapreduce_cdr_daily_overview():
    """
    To get the daily analytic of cdr

       * Total calls per year-month-day-switch
       * Total call duration per year-month-day-switch

    Attributes:

        * ``map`` - Grouping perform on year, month, day & switch
        * ``reduce`` - Calculate call count based on map

    Result Collection: ``aggregate_result_cdr_daily_overview``
    """
    (map, reduce, finalize_fun, out) = mapreduce_default()

    # Get cdr graph by day report
    map = mark_safe(u'''
        function(){
            emit( {
                    a_Year: this.start_uepoch.getFullYear(),
                    b_Month: this.start_uepoch.getMonth() + 1,
                    c_Day: this.start_uepoch.getDate(),
                    f_Switch: this.switch_id
                  },
                  {calldate__count: 1, duration__sum: this.duration} )
        }''')

    out = 'aggregate_result_cdr_daily_overview'
    return (map, reduce, False, out)


def mapreduce_cdr_dashboard():
    """
    To get the minutly analytic of cdr

       * Total calls per year-month-day-hour-min
       * Total call duration per year-month-day-hour-min
       * Total hangup-cause  per year-month-day-hour-min

    Attributes:

        * ``map`` - Grouping perform on year, month, day, hour & min
        * ``reduce`` - Calculate call count, sum of call duration, hangupcause based on map

    Result Collection: ``aggregate_result_cdr_dashboard_report``
    """
    (map, reduce, finalize_fun, out) = mapreduce_default()

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
    (map, reduce, finalize_fun, out) = mapreduce_default()

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
    (map, reduce, finalize_fun, out) = mapreduce_default()

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
    (map, reduce, finalize_fun, out) = mapreduce_default()

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
    return (map, reduce, finalize_fun, out)

