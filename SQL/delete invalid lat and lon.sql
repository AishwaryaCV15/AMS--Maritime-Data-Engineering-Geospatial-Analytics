 DELETE FROM rhein_ais_data
WHERE
    lat < -90 OR lat > 90 OR
    lon < -180 OR lon > 180;