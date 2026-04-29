WITH bounds AS (
    SELECT
        MIN(timestamp) AS min_val,
        MAX(timestamp) AS max_val
    FROM {table_name}
), binned_data AS (
    SELECT
        FLOOR(
            (date_part('epoch', timestamp) - date_part('epoch', min_val)) /
            ((date_part('epoch', max_val) - date_part('epoch', min_val)) / {n_bins})
        )::UTINYINT AS bin_id,
        MIN(timestamp) AS start_time,
        MAX(timestamp) AS end_time,
        MAX(distance) AS max_distance,
        AVG(altitude)::FLOAT AS avg_altitude,
        ROUND(AVG(heart_rate))::UTINYINT AS avg_hr,
        ROUND(AVG(cadence))::UTINYINT AS avg_cadence,
    FROM {table_name}, bounds
    GROUP BY bin_id
    ORDER BY bin_id
), binned_data_2 AS (
    SELECT
        bin_id,
        start_time,
        end_time,
        LAG(end_time, 1) OVER (ORDER BY bin_id) AS bin_start_time,
        LAG(max_distance, 1) OVER (ORDER BY bin_id) AS bin_start_distance,
        max_distance,
        avg_altitude,
        avg_hr,
        avg_cadence,
    FROM binned_data
    ORDER BY bin_id
), binned_data_3 AS (
    SELECT
        bin_id,
        CASE
            WHEN bin_id > 0
            THEN date_diff('second', bin_start_time , end_time)
            ELSE date_diff('second', start_time, end_time) END AS time_diff,
        CASE
            WHEN bin_id > 0
            THEN max_distance - bin_start_distance
            ELSE max_distance END AS distance_km,
        avg_altitude,
        avg_hr,
        avg_cadence,
    FROM binned_data_2
    ORDER BY bin_id
)

SELECT
    bin_id,
    (SUM(time_diff) OVER (ORDER BY bin_id))::UINTEGER AS elapsed_time,
    avg_altitude AS altitude,
    CASE
        WHEN time_diff == 0
        THEN 0
        ELSE (distance_km / time_diff * 3600) END AS speed,
    avg_hr AS heart_rate,
    avg_cadence AS cadence,
FROM binned_data_3
ORDER BY bin_id;

