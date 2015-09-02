
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
  ON matv_voip_cdr_aggr_hour (starting_date, country_id, switch_id, cdr_source_type, hangup_cause_id, user_id);

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
  ON matv_voip_cdr_aggr_min (starting_date, country_id, switch_id, cdr_source_type, hangup_cause_id, user_id);
