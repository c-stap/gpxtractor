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
        (cadence * 2)::UTINYINT AS cadence,
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
    CASE 
        WHEN speed == 0 OR isnan(speed)
        THEN NULL
        ELSE printf(
            '%02d:%02d',
            CAST(FLOOR(60 / speed) AS INT),
            CAST(((60 / speed - FLOOR(60 / speed)) * 60) AS INT))
    END AS pace,
    heart_rate,
    cadence, -- in steps per minute
    lap,
FROM stage_2
ORDER BY index;
