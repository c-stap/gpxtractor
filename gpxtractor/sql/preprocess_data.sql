WITH stage_1 AS (
    SELECT
        timestamp,
        latitude,
        longitude,
        altitude,
        LAG(altitude, 1) OVER (ORDER BY timestamp) AS prev_alt,
        distance,
        LAG(distance, 1) OVER (ORDER BY timestamp) AS prev_dist,
        speed,
        heart_rate::UTINYINT AS heart_rate,
        cadence::UTINYINT AS cadence,
        lap::USMALLINT as lap,
    FROM {table_name}
    ORDER BY timestamp
), stage_2 AS (
    SELECT
        ROW_NUMBER() OVER (ORDER BY timestamp) AS index,
        timestamp,
        latitude,
        longitude,
        altitude,
        altitude - prev_alt AS diff_alt,
        distance,
        distance - prev_dist AS diff_dist,
        speed AS speed_mps,
        heart_rate,
        cadence,
        lap,
    FROM stage_1
    ORDER BY index
)

SELECT
    timestamp,
    latitude,
    longitude,
    ROUND(altitude, 2)::FLOAT AS altitude, -- in meters
    diff_alt,
    CASE
        WHEN index > 1
        THEN ROUND((diff_alt / diff_dist) * 100, 2)::FLOAT
        ELSE 'NaN'::FLOAT END AS gradient, -- as percentage
    (distance / 1000)::FLOAT AS distance, -- in km
    ROUND(speed_mps * 3.6, 2)::FLOAT AS speed, -- in kph
    heart_rate,
    cadence, -- in revolutions per minute (unmodified)
    lap,
FROM stage_2
ORDER BY index;
