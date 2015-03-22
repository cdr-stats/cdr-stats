

-- Group by country
SELECT country_id, count(*) from voip_cdr GROUP BY country_id;

-- Group by country / Last 24 hours
SELECT
    country_id, count(*), SUM(duration) as duration, SUM(billsec) as billsec
FROM
    voip_cdr
WHERE
    starting_date > current_timestamp - interval '1' day and
    starting_date <= current_timestamp
GROUP BY country_id;

-- Group by hangup_status / Last 24 hours
SELECT
    hangup_cause_id, count(*), SUM(duration) as duration, SUM(billsec) as billsec
FROM
    voip_cdr
WHERE
    starting_date > current_timestamp - interval '1' day and
    starting_date <= current_timestamp
GROUP BY hangup_cause_id;

-- Group by date hours
SELECT
    to_char(starting_date, 'YYYY-MM-DD HH24'), country_id, avg(duration)
FROM
    voip_cdr
WHERE
    starting_date > current_timestamp - interval '1' day and
    starting_date <= current_timestamp
GROUP BY
    to_char(starting_date, 'YYYY-MM-DD HH24'), country_id;


-- Convert timestamp to date + hour: http://www.postgresql.org/docs/9.4/static/functions-formatting.html
SELECT to_char(current_timestamp, 'YYYY-MM-DD HH24');

SELECT date_trunc('minute', current_timestamp);


-- Play ground
SELECT
    starting_date,
    ntile (10) over (order by starting_date asc) as decile
FROM
    voip_cdr
WHERE
    starting_date > current_timestamp - interval '1' day and
    starting_date <= current_timestamp

 -- SELECT
 --     CASE width_bucket((d * interval '1 day' + date '2014-01-01')::date, ARRAY['2014-03-01', '2014-06-01', '2014-09-01', '2014-12-01']::date[])
 --         WHEN 1 THEN 'Spring'
 --         WHEN 2 THEN 'Summer'
 --         WHEN 3 THEN 'Autumn'
 --         ELSE 'Winter' END season,
 --     count(*)
 -- FROM generate_series(0,364) d GROUP BY 1 ORDER BY 1;

-- width_bucket on duration time / for histogram on duration repartition
SELECT
    width_bucket(duration, 0, 120, 6), sum(duration), avg(duration), count(*)
FROM
    voip_cdr
WHERE
    starting_date > current_timestamp - interval '1' day and
    starting_date <= current_timestamp
GROUP BY 1 ORDER BY 1;


-- width_bucket on duration time / for histogram on start_time repartition

SELECT
    width_bucket(
                extract(epoch FROM starting_date),
                extract(epoch FROM current_timestamp) - 86400,
                extract(epoch FROM current_timestamp) + 86400 * 30,
                10
    ),
    to_char(starting_date, 'YYYY-MM-DD HH24') as mydate,
    sum(duration), avg(duration), count(*)
FROM
    voip_cdr
WHERE
    starting_date > current_timestamp - interval '1' day and
    starting_date <= current_timestamp + interval '30' day
GROUP BY 1, 2 ORDER BY 1, 2;

-- version without width_bucket
SELECT
    to_char(starting_date, 'YYYY-MM-DD HH24') as mydate,
    sum(duration), avg(duration), count(*)
FROM
    voip_cdr
WHERE
    starting_date > current_timestamp - interval '1' day and
    starting_date <= current_timestamp + interval '30' day
GROUP BY 1 ORDER BY 1;



-- Count calls
SELECT count(*)
FROM
    voip_cdr
WHERE
    starting_date > current_timestamp - interval '1' day and
    starting_date <= current_timestamp + interval '30' day;

--
SELECT
     width_bucket((d * interval '1 day' + date '2014-01-01')::date,
                       ARRAY['2014-03-01', '2014-06-01', '2014-09-01', '2014-12-01']::date[]),
     count(*)
FROM
    generate_series(0,364) d GROUP BY 1 ORDER BY 1;

-- bang
SELECT
    country_id, duration, avg(duration) OVER(PARTITION BY country_id)
FROM
    voip_cdr
WHERE
    starting_date > current_timestamp - interval '1' day and
    starting_date <= current_timestamp;

-- fill date | select per country id the number call | duration | billsec
with filled_dates as (
  select day, 0 as blank_count from
    generate_series(
                    date_trunc('day', current_timestamp - interval '1' day),
                    date_trunc('day', current_timestamp + interval '30' day),
                    '1 day')
        as day
),
call_counts as (
  select
    country_id,
    date_trunc('day', starting_date) as day,
    count(*) as nbcalls, SUM(duration) as duration, SUM(billsec) as billsec
    from voip_cdr
  where
    starting_date > date_trunc('day', current_timestamp - interval '1' day) and
    starting_date <= date_trunc('day', current_timestamp + interval '31' day)
    -- and country_id = 11
  group by date_trunc('day', starting_date), country_id
)
select country_id,
        filled_dates.day,
        coalesce(call_counts.nbcalls, filled_dates.blank_count) as nbcalls,
        coalesce(call_counts.duration, filled_dates.blank_count) as duration,
        coalesce(call_counts.billsec, filled_dates.blank_count) as billsec
from
    filled_dates
left outer join
    call_counts on call_counts.day = filled_dates.day
order by
    country_id, filled_dates.day;


-- without with
SELECT
    dateday,
    coalesce(nbcalls,0) AS nbcalls,
    coalesce(duration,0) AS duration,
    coalesce(billsec,0) AS billsec
FROM
    generate_series(
                    date_trunc('day', current_timestamp - interval '1' day),
                    date_trunc('day', current_timestamp + interval '30' day),
                    '1 day')
    as dateday
LEFT OUTER JOIN (
    SELECT
        date_trunc('day', voip_cdr.starting_date) as day,
        count(*) as nbcalls, SUM(duration) as duration, SUM(billsec) as billsec
    FROM voip_cdr
    WHERE
        starting_date > date_trunc('day', current_timestamp - interval '1' day) and
        starting_date <= date_trunc('day', current_timestamp + interval '31' day)
    GROUP BY day
    ) results
ON (dateday = results.day);



-- Drop Materialized View
DROP MATERIALIZED VIEW matv_voip_cdr_aggr_hour;

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

-- Refresh Materialized View
REFRESH MATERIALIZED VIEW matv_voip_cdr_aggr_hour;

#Create index on Materialized view
CREATE UNIQUE INDEX matv_voip_cdr_aggr_hour_date
  ON matv_voip_cdr_aggr_hour (starting_date, country_id, switch_id, cdr_source_type, hangup_cause_id);

# Refresh without lock
REFRESH MATERIALIZED VIEW CONCURRENTLY matv_voip_cdr_aggr_hour;

-- Drop Materialized View
DROP MATERIALIZED VIEW matv_voip_cdr_aggr_min;

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

#Create index on Materialized view
CREATE UNIQUE INDEX matv_voip_cdr_aggr_min_date
  ON matv_voip_cdr_aggr_min (starting_date, country_id, switch_id, cdr_source_type, hangup_cause_id);

# Refresh without lock
REFRESH MATERIALIZED VIEW CONCURRENTLY matv_voip_cdr_aggr_min;

-- Check size
SELECT pg_relation_size('voip_cdr') AS tab_size, pg_relation_size('matv_voip_cdr_aggr_min') AS matview_size_min, pg_relation_size('matv_voip_cdr_aggr_hour') AS matview_size_hour;

-- CREATE MATERIALIZED VIEW per user_id


-- Select the top 5 country on materialized view
SELECT
    country_id, SUM(duration) as sumduration
FROM
    matv_voip_cdr_aggr_hour
WHERE
    starting_date > date_trunc('day', current_timestamp - interval '1' day) and
    starting_date <= date_trunc('day', current_timestamp + interval '31' day)
GROUP BY
    country_id
ORDER BY
    sumduration DESC
LIMIT 5;



-- Interogate materialized view 'matv_voip_cdr_aggr_hour' to obtain fast day to day
-- reporting for the last 30 days
--
SELECT
    dateday,
    coalesce(nbcalls,0) AS nbcalls,
    coalesce(duration,0) AS duration,
    coalesce(billsec,0) AS billsec,
    coalesce(buy_cost,0) AS buy_cost,
    coalesce(sell_cost,0) AS sell_cost
FROM
    generate_series(
                    date_trunc('day', current_timestamp - interval '1' day),
                    date_trunc('day', current_timestamp + interval '30' day),
                    '1 day')
    as dateday
LEFT OUTER JOIN (
    SELECT
        date_trunc('day', starting_date) as day,
        SUM(nbcalls) as nbcalls,
        SUM(duration) as duration,
        SUM(billsec) as billsec,
        SUM(buy_cost) as buy_cost,
        SUM(sell_cost) as sell_cost
    FROM matv_voip_cdr_aggr_hour
    WHERE
        starting_date > date_trunc('day', current_timestamp - interval '1' day) and
        starting_date <= date_trunc('day', current_timestamp + interval '31' day)
    GROUP BY day
    ) results
ON (dateday = results.day);

-- Interogate materialized view 'matv_voip_cdr_aggr_hour' to obtain fast hour to hour
-- reporting for the last 24 hours
--
SELECT
    dateday,
    coalesce(nbcalls,0) AS nbcalls,
    coalesce(duration,0) AS duration,
    coalesce(billsec,0) AS billsec,
    coalesce(buy_cost,0) AS buy_cost,
    coalesce(sell_cost,0) AS sell_cost
FROM
    generate_series(
                    date_trunc('hour', current_timestamp - interval '24' hour),
                    date_trunc('hour', current_timestamp),
                    '1 hour')
    as dateday
LEFT OUTER JOIN (
    SELECT
        date_trunc('hour', starting_date) as dayhour,
        SUM(nbcalls) as nbcalls,
        SUM(duration) as duration,
        SUM(billsec) as billsec,
        SUM(buy_cost) as buy_cost,
        SUM(sell_cost) as sell_cost
    FROM matv_voip_cdr_aggr_hour
    WHERE
        starting_date > date_trunc('hour', current_timestamp - interval '24' hour) and
        starting_date <= date_trunc('hour', current_timestamp)
    GROUP BY dayhour
    ) results
ON (dateday = results.dayhour);


-- Select the top 5 country
SELECT
    country_id, SUM(duration) as duration, SUM(nbcalls) as nbcalls
FROM
    matv_voip_cdr_aggr_hour
WHERE
    starting_date > date_trunc('hour', current_timestamp - interval '24' hour) and
    starting_date <= date_trunc('hour', current_timestamp)
GROUP BY
    country_id
ORDER BY
    duration DESC
LIMIT 5;


-- Select the top 10 country
SELECT
    hangup_cause_id, SUM(duration) as duration, SUM(nbcalls) as nbcalls
FROM
    matv_voip_cdr_aggr_hour
WHERE
    starting_date > date_trunc('hour', current_timestamp - interval '24' hour) and
    starting_date <= date_trunc('hour', current_timestamp)
GROUP BY
    hangup_cause_id
ORDER BY
    duration DESC
LIMIT 10;

-- hours reporting with switches
-- extract(hour from dateday) as dateday,
SELECT
    dateday as dateday,
    switch_id,
    coalesce(nbcalls,0) AS nbcalls,
    coalesce(duration,0) AS duration,
    coalesce(billsec,0) AS billsec,
    coalesce(buy_cost,0) AS buy_cost,
    coalesce(sell_cost,0) AS sell_cost
FROM
    generate_series(
                    date_trunc('hour', current_timestamp - interval '72' hour),
                    date_trunc('hour', current_timestamp + interval '2' hour),
                    '1 hour')
    as dateday
LEFT OUTER JOIN (
    SELECT
        date_trunc('hour', starting_date) as dayhour,
        switch_id as switch_id,
        SUM(nbcalls) as nbcalls,
        SUM(duration) as duration,
        SUM(billsec) as billsec,
        SUM(buy_cost) as buy_cost,
        SUM(sell_cost) as sell_cost
    FROM matv_voip_cdr_aggr_hour
    WHERE
        starting_date > date_trunc('hour', current_timestamp - interval '72' hour) and
        starting_date <= date_trunc('hour', current_timestamp + interval '2' hour)
    GROUP BY dayhour, switch_id
    ) results
ON (dateday = results.dayhour);


-- days reporting with switches
-- time_interval could be hour / day / week / month
SELECT
    dateday,
    switch_id,
    coalesce(nbcalls,0) AS nbcalls,
    coalesce(duration,0) AS duration,
    coalesce(billsec,0) AS billsec,
    coalesce(buy_cost,0) AS buy_cost,
    coalesce(sell_cost,0) AS sell_cost
FROM
    generate_series(
                    date_trunc('day', current_timestamp - interval '24' hour),
                    date_trunc('day', current_timestamp + interval '2' hour),
                    '1 day')
    as dateday
LEFT OUTER JOIN (
    SELECT
        date_trunc('day', starting_date) as time_interval,
        switch_id as switch_id,
        SUM(nbcalls) as nbcalls,
        SUM(duration) as duration,
        SUM(billsec) as billsec,
        SUM(buy_cost) as buy_cost,
        SUM(sell_cost) as sell_cost
    FROM matv_voip_cdr_aggr_hour
    WHERE
        starting_date > date_trunc('day', current_timestamp - interval '24' hour) and
        starting_date <= date_trunc('day', current_timestamp + interval '2' hour)
    GROUP BY time_interval, switch_id
    ) results
ON (dateday = results.time_interval);

