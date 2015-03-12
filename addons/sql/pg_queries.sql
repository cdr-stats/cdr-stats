

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


-- Play ground
SELECT
    starting_date,
    ntile (10) over (order by starting_date asc) as decile
FROM
    voip_cdr
WHERE
    starting_date > current_timestamp - interval '1' day and
    starting_date <= current_timestamp


-- width_bucket
SELECT
     width_bucket((d * interval '1 day' + date '2014-01-01')::date,
                       ARRAY['2014-03-01', '2014-06-01', '2014-09-01', '2014-12-01']::date[]),
     count(*)
FROM generate_series(0,364) d GROUP BY 1 ORDER BY 1;

-- bang
SELECT
    country_id, duration, avg(duration) OVER(PARTITION BY country_id)
FROM
    voip_cdr
WHERE
    starting_date > current_timestamp - interval '1' day and
    starting_date <= current_timestamp;
