WITH stage_1 AS (
    SELECT
        ROW_NUMBER() OVER (ORDER BY timestamp) AS index,
        timestamp,
        latitude,
        longitude,
        LAG(timestamp, 1) OVER (ORDER BY timestamp) AS prev_time,
        LAG(latitude, 1) OVER (ORDER BY timestamp) AS prev_lat,
        LAG(longitude, 1) OVER (ORDER BY timestamp) AS prev_long,
        altitude,
        heart_rate,
        cadence,
        lap,
    FROM {table_name}
    ORDER BY timestamp
), stage_2 AS (
    SELECT
        timestamp,
        latitude,
        longitude,
        CASE
            WHEN index == 1
            THEN 0.0::FLOAT
            ELSE haversine(prev_lat, prev_long, latitude, longitude)::FLOAT END AS marginal_distance,
        CASE
            WHEN index == 1
            THEN 0::SMALLINT
            ELSE date_diff('second', prev_time, timestamp)::SMALLINT END AS marginal_time,
        altitude,
        heart_rate,
        cadence,
        lap,
    FROM stage_1
    ORDER BY timestamp
)

SELECT
    timestamp,
    latitude,
    longitude,
    ROUND(SUM(marginal_distance) OVER (ORDER BY timestamp), 2)::FLOAT AS distance, -- in meters
    -- SUM(marginal_time) OVER (ORDER BY timestamp) AS elapsed_time,
    (marginal_distance / marginal_time)::FLOAT AS speed, -- in meters per second
    altitude, -- in meters
    heart_rate,
    cadence, -- strides (2 steps) per minute
    lap,
FROM stage_2
ORDER BY timestamp;
