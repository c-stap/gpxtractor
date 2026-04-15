CREATE OR REPLACE FUNCTION haversine(lat1 DOUBLE, lon1 DOUBLE, lat2 DOUBLE, lon2 DOUBLE) AS
    2 * 6371000 * ASIN(
        SQRT(
            POW(SIN(RADIANS(lat2 - lat1) / 2), 2) +
            COS(RADIANS(lat1)) * COS(RADIANS(lat2)) *
            POW(SIN(RADIANS(lon2 - lon1) / 2), 2)
        )
    );
