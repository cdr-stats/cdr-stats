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

def pipeline_cdr_view_daily_report(query_var):
    """
    To get the day vise analytic of cdr

    Attributes:

        * ``query_var`` - filter variable for collection
    """
    pipeline = [
        {'$match': query_var},
        {'$group': {
            '_id': {'$substr': ["$_id", 0, 8]},
            'callperday': {'$sum': '$call_daily'},
            'durationperday': {'$sum': '$duration_daily'}
        }
        },
        {'$project': {
            'callperday': 1,
            'durationperday': 1,
            'avgdurationperday': {'$divide': ["$durationperday", "$callperday"]}
        }
        },
        {'$sort': {
            '_id': 1
        }
        }
    ]
    return pipeline


def pipeline_country_report(query_var):
    """
    To get all calls and their duration for all countries

    Attributes:

        * ``query_var`` - filter variable for collection
    """
    pipeline = [
        {'$match': query_var},
        {'$group': {
            '_id': '$metadata.country_id', # grouping on country id
            'call_per_day': {'$sum': '$call_daily'},
            'duration_per_day': {'$sum': '$duration_daily'}
        }
        },
        {'$project': {
            'call_per_day': 1,
            'duration_per_day': 1,
            }
        },
        {'$sort': {
            'call_per_day': -1,
            'duration_per_day': -1,
            }
        }
    ]
    return pipeline


def pipeline_daily_overview(query_var):
    """
    To get daily overview of calls and their duration

    Attributes:

        * ``query_var`` - filter variable for collection
    """
    pipeline = [
        {'$match': query_var},
        {'$group': {
            '_id': {'$substr': ["$_id", 0, 8]},
            'switch_id': {'$addToSet' :'$metadata.switch_id'},
            'call_per_day': {'$sum': '$call_daily'},
            'duration_per_day': {'$sum': '$duration_daily'}
        }
        },
        {'$project': {
            'switch_id': 1,
            'call_per_day': 1,
            'duration_per_day': 1,
            'avg_duration_per_day': {'$divide': ["$duration_per_day", "$call_per_day"]}
            }
        },
        {'$unwind': '$switch_id'},
        {'$sort': {
            '_id': -1,
            'switch_id': 1,
            }
        }
    ]
    return pipeline


def pipeline_monthly_overview(query_var):
    """
    To get monthly overview of calls and their duration

    Attributes:

        * ``query_var`` - filter variable for collection
    """
    pipeline = [
        {'$match': query_var},
        {'$group': {
            '_id': {'$substr': ['$_id', 0, 6]},
            'switch_id': {'$addToSet' :'$metadata.switch_id'},
            'call_per_month': {'$sum': '$call_monthly'},
            'duration_per_month': {'$sum': '$duration_monthly'}
        }
        },
        {'$project': {
            'switch_id': 1,
            'call_per_month': 1,
            'duration_per_month': 1,
            #'avg_duration_per_month': {'$divide': ['$duration_per_month',
            #                                       '$call_per_month']},
            }
        },
        {'$unwind': '$switch_id'},
        {'$sort': {
            '_id': -1,
            'switch_id': 1,
            }
        }
    ]
    return pipeline
