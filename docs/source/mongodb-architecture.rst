.. _postgresql_mat_view:

PostgreSQL
==========

:Web: http://www.postgresql.org/

--


PostgreSQL is an object-relational database management system (ORDBMS) with an emphasis on
extensibility and standards-compliance.

PostgreSQL provides few interesting features that make a perfect pick for CDR-Stats:

- Materialized view (http://www.postgresql.org/docs/9.4/static/rules-materializedviews.html),
those views contains the results of queries, it's very ideal for aggregation view, they also
can be refreshed since PG 9.4 without locking.

- Json Types (http://www.postgresql.org/docs/9.4/static/datatype-json.html), are for storing
JSON (JavaScript Object Notation) data, this field is ideal to store none structured data.
CDR-Stats aggregate data from several type of telco switches in which the type of data received
can vary drastically.

.. contents::
    :local:
    :depth: 1


.. _materialized_view:

Materialized views
------------------

We created 2 Materizlied views to help on our reporting job, here is the schema structure of those 2 views:

    -- Materialized View
    CREATE MATERIALIZED VIEW matv_voip_cdr_aggr_hour AS
        SELECT
            date_trunc('hour', starting_date) as starting_date,
            country_id,
            switch_id,
            cdr_source_type,
            hangup_cause_id,
            user_id,
            count(*) AS nbcalls,
            sum(duration) AS duration,
            sum(billsec) AS billsec,
            sum(buy_cost) AS buy_cost,
            sum(sell_cost) AS sell_cost
        FROM
            voip_cdr
        GROUP BY
            date_trunc('hour', starting_date), country_id, switch_id, cdr_source_type, hangup_cause_id, user_id;

    -- Create index on Materialized view
    CREATE UNIQUE INDEX matv_voip_cdr_aggr_hour_date
      ON matv_voip_cdr_aggr_hour (starting_date, country_id, switch_id, cdr_source_type, hangup_cause_id);

    -- Materialized View
    CREATE MATERIALIZED VIEW matv_voip_cdr_aggr_min AS
        SELECT
            date_trunc('minute', starting_date) as starting_date,
            country_id,
            switch_id,
            cdr_source_type,
            hangup_cause_id,
            user_id,
            count(*) AS nbcalls,
            sum(duration) AS duration,
            sum(billsec) AS billsec,
            sum(buy_cost) AS buy_cost,
            sum(sell_cost) AS sell_cost
        FROM
            voip_cdr
        GROUP BY
            date_trunc('minute', starting_date), country_id, switch_id, cdr_source_type, hangup_cause_id, user_id;

    -- Create index on Materialized view
    CREATE UNIQUE INDEX matv_voip_cdr_aggr_min_date
      ON matv_voip_cdr_aggr_min (starting_date, country_id, switch_id, cdr_source_type, hangup_cause_id);


You can drop those views with::

    -- Drop Materialized View
    DROP MATERIALIZED VIEW matv_voip_cdr_aggr_hour;

    -- Drop Materialized View
    DROP MATERIALIZED VIEW matv_voip_cdr_aggr_min;


You can refresh the view as follow, using concurrently we ensure to not lock the view::

    # Refresh without lock
    REFRESH MATERIALIZED VIEW CONCURRENTLY matv_voip_cdr_aggr_hour;

    # Refresh without lock
    REFRESH MATERIALIZED VIEW CONCURRENTLY matv_voip_cdr_aggr_min;


The update of the Materialized view is done periodically by a celery task using the above commands "REFRESH MATERIALIZED VIEW".
