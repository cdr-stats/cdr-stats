
CREATE EXTENSION "uuid-ossp";

-- HANGUP_CAUSE = ['NORMAL_CLEARING', 'USER_BUSY', 'NO_ANSWER']
-- HANGUP_CAUSE_Q850 = ['16', '17', '19']


-- Generate 1.000.000 random calls in next the 60 days
INSERT INTO voip_cdr (user_id, switch_id, cdr_source_type, callid, caller_id_number, caller_id_name,
    destination_number, starting_date, duration, billsec, hangup_cause_id, direction, country_id,
    authorized, buy_rate, buy_cost, sell_rate, sell_cost, data) (
    SELECT
        1 AS user_id,
        cast(random() * 1 as int) + 1 AS switch_id,
        cast(random() * 4 as int) + 1 AS cdr_source_type,
        cast(uuid_generate_v4() AS text) AS callid,
        '+' || cast(30 + cast(trunc(random() * 20 + 1) as int) as text) || 800000000 + cast(trunc(random() * 5000000 + 1) as int) AS caller_id_number,
        '' AS caller_id_name,
        '+' || cast(30 + cast(trunc(random() * 20 + 1) as int) as text) || 800000000 + cast(trunc(random() * 5000000 + 1) as int) AS destination_number,
        current_timestamp - ( cast(trunc(random() * 30) as int) || ' days')::interval
             + ( cast(trunc(random() * 1440) as int) || ' minutes')::interval
             AS starting_date,
        cast(trunc(random() * 150 + 1) as int) AS duration,
        cast(trunc(random() * 120 + 1) as int) AS billsec,
        16 + cast(trunc(random() * 4 + 0) as int) AS hangup_cause_id,
        cast(random() * 2 as int) AS direction,
        cast(trunc(random() * 30 + 1) as int) as country_id,
        TRUE AS authorized,
        cast(random()::numeric / 5 AS numeric(10,5)) AS buy_rate,
        cast(random()::numeric AS numeric(12,5)) AS buy_cost,
        cast(random()::numeric / 5 AS numeric(10,5)) / 5 AS sell_rate,
        cast(random()::numeric AS numeric(12,5)) AS sell_cost,
        '{"mos": 3}'::jsonb AS data
        FROM generate_series(1, 500000) AS n
);
