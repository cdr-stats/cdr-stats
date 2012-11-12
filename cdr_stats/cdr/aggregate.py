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
from django.conf import settings


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
            'call_per_day': {'$sum': '$call_daily'},
            'duration_per_day': {'$sum': '$duration_daily'}
            }
        },
        {'$project': {
            'call_per_day': 1,
            'duration_per_day': 1,
            'avg_duration_per_day': {'$divide': ["$duration_per_day", "$call_per_day"]}
            }
        },
        {'$sort': {
            '_id': -1
            }
        }
    ]
    return pipeline


def pipeline_country_hourly_report(query_var):
    """
    To get country vise hourly report of calls and their duration

    Attributes:

        * ``query_var`` - filter variable for collection
    """
    pipeline = [
        {'$match': query_var},
        {'$group': {
            '_id': {'country_id': '$metadata.country_id',
                    'date': {'$substr': ['$metadata.date', 0, 10]}},
            'call_per_hour': {'$push': '$call_hourly'},
            'duration_per_hour': {'$push': '$duration_hourly'},
            }
        },
        {'$project': {
            'call_per_hour': 1,
            'duration_per_hour': 1,
            }
        },
        {'$sort': {
            '_id.date': -1,
            '_id.country_id': 1,
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
            '_id': '$metadata.country_id',  # grouping on country id
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
        },
        {'$limit': settings.NUM_COUNTRY}
    ]
    return pipeline


def pipeline_hourly_overview(query_var):
    """
    To get hourly overview of calls and their duration

    Attributes:

        * ``query_var`` - filter variable for collection
    """
    pipeline = [
        {'$match': query_var},
        {'$group': {
            '_id': {'$substr': ["$_id", 0, 8]},
            'switch_id': {'$addToSet': '$metadata.switch_id'},
            'call_per_hour': {'$push': '$call_hourly'},
            'duration_per_hour': {'$push': '$duration_hourly'}
            }
        },
        {'$project': {
            'switch_id': 1,
            'call_per_hour': 1,
            'duration_per_hour': 1,
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
            'switch_id': {'$addToSet': '$metadata.switch_id'},
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
            'switch_id': {'$addToSet': '$metadata.switch_id'},
            'call_per_month': {'$sum': '$call_monthly'},
            'duration_per_month': {'$sum': '$duration_monthly'}
        }
        },
        {'$project': {
            'switch_id': 1,
            'call_per_month': 1,
            'duration_per_month': 1,
            'avg_duration_per_month': {'$divide': ['$duration_per_month',
                                                   '$call_per_month']},
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


def pipeline_hourly_report(query_var):
    """
    To get monthly overview of calls and their duration

    Attributes:

        * ``query_var`` - filter variable for collection
    """
    pipeline = [
        {'$match': query_var},
        {'$group': {
            '_id': {'$substr': ['$_id', 0, 8]},
            'call_per_hour': {'$push': '$call_hourly'},
            'duration_per_hour': {'$push': '$duration_hourly'},
            }
        },
        {'$project': {
            'call_per_hour': 1,
            'duration_per_hour': 1,
            }
        },
        {'$sort': {
            '_id': -1,
            }
        }
    ]
    return pipeline


def pipeline_mail_report(query_var):
    """
    To get monthly overview of calls and their duration

    Attributes:

        * ``query_var`` - filter variable for collection
    """
    pipeline = [
        {'$match': query_var},
        {'$group': {
            '_id': {'country_id': '$country_id',
                    'hangup_cause_id': '$hangup_cause_id'
            },
            'duration_sum': {'$sum': '$duration'},
            'call_count': {'$sum': 1},
            }
        },
        {'$project': {
            'call_count': 1,
            'duration_sum': 1,
            #'avg_duration': {'$divide': ['$duration_sum',
            #                             '$call_count']},
            }
        },
        {'$sort': {
            '_id.country_id': 1,
            #'_id.hangup_cause_id': 1,
            }
        },
    ]
    return pipeline
