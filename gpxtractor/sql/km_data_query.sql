WITH data_with_km_col AS (
    SELECT 
        *,
        TRUNC(distance) + 1 AS km
    FROM {table_name}
    ORDER BY timestamp
), km_data AS (
    SELECT
        km::SMALLINT AS km,
        MIN(timestamp) AS start_time,
        MAX(timestamp) AS end_time,
        MAX(distance) AS max_distance,
        ROUND(SUM(CASE
            WHEN diff_alt > 0
            THEN diff_alt
            ELSE 0 END))::USMALLINT AS elevation_gain,
        ABS(ROUND(SUM(CASE
            WHEN diff_alt < 0
            THEN diff_alt
            ELSE 0 END)))::USMALLINT AS elevation_loss,
        ROUND(AVG(heart_rate))::UTINYINT AS avg_hr,
        MAX(heart_rate)::UTINYINT AS max_hr,
        ROUND(AVG(cadence))::UTINYINT AS avg_cadence,
        MAX(cadence)::UTINYINT AS max_cadence
    FROM data_with_km_col
    GROUP BY km
    ORDER BY km
), km_data_stage_2 AS (
    SELECT
        km,
        start_time,
        end_time,
        LAG(end_time, 1) OVER (ORDER BY km) AS km_start_time,
        LAG(max_distance, 1) OVER (ORDER BY km) AS km_start_distance,
        max_distance,
        elevation_gain,
        elevation_loss,
        avg_hr,
        max_hr,
        avg_cadence,
        max_cadence
    FROM km_data
    ORDER BY km
), km_data_stage_3 AS (
    SELECT
        km,
        CASE
            WHEN km > 1
            THEN date_diff('second', km_start_time , end_time)
            ELSE date_diff('second', start_time, end_time) END AS elapsed_time,
        CASE
            WHEN km > 1
            THEN max_distance - km_start_distance 
            ELSE max_distance END AS distance_km,
        CASE
            WHEN km > 1
            THEN (km_start_distance + distance_km / 2)
            ELSE (distance_km / 2) END AS midpoint,
        elevation_gain,
        elevation_loss,
        avg_hr,
        max_hr,
        avg_cadence,
        max_cadence
    FROM km_data_stage_2
    ORDER BY km
)

SELECT
    km,
    distance_km AS distance,
    CASE
        WHEN elapsed_time == 0
        THEN 0
        ELSE (distance_km / elapsed_time * 3600) END AS avg_speed_kph,
    CASE 
        WHEN avg_speed_kph == 0
        THEN NULL
        ELSE printf(
            '%02d:%02d',
            CAST(FLOOR(60 / avg_speed_kph) AS INT),
            CAST(((60 / avg_speed_kph - FLOOR(60 / avg_speed_kph)) * 60) AS INT)
        ) END AS avg_pace,
    midpoint AS midpoint,
    elevation_gain,
    elevation_loss,
    avg_hr,
    max_hr,
    avg_cadence,
    max_cadence
FROM km_data_stage_3
ORDER BY km;
