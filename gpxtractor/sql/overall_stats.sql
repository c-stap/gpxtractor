WITH overall_stats_stage1 AS (
    SELECT
        MIN(timestamp) AS start_time,
        MAX(timestamp) AS end_time,
        date_diff('second', start_time, end_time)::INT as elapsed_time,
        ROUND(MAX(distance), 2)::FLOAT AS total_distance,
        ROUND((total_distance / elapsed_time) * 3600, 2)::FLOAT AS avg_speed,
        MAX(speed)::FLOAT AS max_speed,
        printf(
            '%02d:%02d',
            CAST(FLOOR(60 / avg_speed) AS INT),
            CAST(((60 / avg_speed - FLOOR(60 / avg_speed)) * 60) AS INT)
        ) AS avg_pace,
        ROUND(SUM(CASE
            WHEN diff_alt > 0
            THEN diff_alt
            ELSE 0 END))::INTEGER AS elevation_gain,
        ABS(ROUND(SUM(CASE
            WHEN diff_alt < 0
            THEN diff_alt
            ELSE 0 END)))::INTEGER AS elevation_loss,
        ROUND(AVG(heart_rate))::UTINYINT as avg_heart_rate,
        MAX(heart_rate) as max_heart_rate,
        ROUND(AVG(cadence))::UTINYINT AS avg_cadence,
        MAX(cadence) AS max_cadence,
    FROM {table_name}
)

SELECT
    start_time,
    elapsed_time,
    total_distance AS distance,
    avg_speed,
    max_speed,
    avg_pace,
    elevation_gain,
    elevation_loss,
    avg_heart_rate,
    max_heart_rate,
    avg_cadence,
    max_cadence,
FROM overall_stats_stage1;
