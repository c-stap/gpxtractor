WITH data_with_unit_col AS (
    SELECT 
        *,
        TRUNC(distance) + 1 AS unit
    FROM {table_name}
    ORDER BY timestamp
), unit_data AS (
    SELECT
        unit::SMALLINT AS unit,
        MIN(timestamp) AS start_time,
        MAX(timestamp) AS end_time,
        MAX(distance) AS max_distance,
        ROUND(SUM(CASE
            WHEN diff_altitude > 0
            THEN diff_altitude
            ELSE 0 END))::USMALLINT AS elevation_gain,
        ABS(ROUND(SUM(CASE
            WHEN diff_altitude < 0
            THEN diff_altitude
            ELSE 0 END)))::USMALLINT AS elevation_loss,
        ROUND(AVG(heart_rate))::UTINYINT AS avg_heart_rate,
        MAX(heart_rate)::UTINYINT AS max_heart_rate,
        ROUND(AVG(cadence))::UTINYINT AS avg_cadence,
        MAX(cadence)::UTINYINT AS max_cadence
    FROM data_with_unit_col
    GROUP BY unit
    ORDER BY unit
), unit_data_stage_2 AS (
    SELECT
        unit,
        start_time,
        end_time,
        LAG(end_time, 1) OVER (ORDER BY unit) AS unit_start_time,
        LAG(max_distance, 1) OVER (ORDER BY unit) AS unit_start_distance,
        max_distance,
        elevation_gain,
        elevation_loss,
        avg_heart_rate,
        max_heart_rate,
        avg_cadence,
        max_cadence
    FROM unit_data
    ORDER BY unit
), unit_data_stage_3 AS (
    SELECT
        unit,
        CASE
            WHEN unit > 1
            THEN date_diff('second', unit_start_time , end_time)
            ELSE date_diff('second', start_time, end_time) END AS elapsed_time,
        CASE
            WHEN unit > 1
            THEN max_distance - unit_start_distance 
            ELSE max_distance END AS distance_unit,
        CASE
            WHEN unit > 1
            THEN (unit_start_distance + distance_unit / 2)
            ELSE (distance_unit / 2) END AS midpoint,
        elevation_gain,
        elevation_loss,
        avg_heart_rate,
        max_heart_rate,
        avg_cadence,
        max_cadence
    FROM unit_data_stage_2
    ORDER BY unit
)

SELECT
    unit AS {unit},
    distance_unit AS distance,
    CASE
        WHEN elapsed_time == 0
        THEN 0
        ELSE (distance_unit / elapsed_time * 3600) END AS avg_speed,
    CASE 
        WHEN avg_speed == 0
        THEN NULL
        ELSE printf(
            '%02d:%02d',
            CAST(FLOOR(60 / avg_speed) AS INT),
            CAST(((60 / avg_speed - FLOOR(60 / avg_speed)) * 60) AS INT)
        ) END AS avg_pace,
    midpoint AS midpoint,
    elevation_gain,
    elevation_loss,
    avg_heart_rate,
    max_heart_rate,
    avg_cadence,
    max_cadence
FROM unit_data_stage_3
ORDER BY unit;
