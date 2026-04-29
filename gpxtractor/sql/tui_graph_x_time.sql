WITH bounds AS (
    SELECT
        MIN(timestamp) AS min_val,
        MAX(timestamp) AS max_val
    FROM {table_name}
), binned_data AS (
    SELECT
        FLOOR((time - min_val) / ((max_val - min_val) / {n_bins})) AS bin_id,
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
    FROM {table_name}, bounds
    GROUP BY bin_id
    ORDER BY bin_id
), binned_data_2 AS (
    SELECT
        bin_id,
        start_time,
        end_time,
        LAG(end_time, 1) OVER (ORDER BY lap) AS bin_start_time,
        LAG(max_distance, 1) OVER (ORDER BY lap) AS bin_start_distance,
        max_distance,
        avg_hr,
        avg_cadence,
    FROM binned_data
    ORDER BY bin_id
), binned_data_3 AS (
    SELECT
        bin_id,
        CASE
            WHEN bin_id > 1
            THEN date_diff('second', lap_start_time , end_time)
            ELSE date_diff('second', start_time, end_time) END AS elapsed_time,
        CASE
            WHEN bin_id > 1
            THEN max_distance - lap_start_distance 
            ELSE max_distance END AS distance_km,
        avg_hr,
        avg_cadence,
    FROM binned_data_2
    ORDER BY bin_id
)

SELECT
    bin_id,
    distance_km AS distance,
    CASE
        WHEN elapsed_time == 0
        THEN 0
        ELSE (distance_km / elapsed_time * 3600) END AS avg_speed,
    avg_hr,
    avg_cadence,
FROM binned_data_3
ORDER BY bin_id;
