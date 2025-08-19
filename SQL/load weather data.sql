LOAD DATA LOCAL INFILE 'C:/Users/cvais/Documents/GitHub/AMS_ShipTraj/weather_2025-03.csv'
INTO TABLE weather_data
FIELDS TERMINATED BY ','
ENCLOSED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
    @date_var,
    latitude,
    longitude,
    temperature_2m,
    wind_speed_10m,
    visibility,
    wind_speed_80m,
    wind_speed_120m,
    wind_speed_180m,
    wind_direction_10m,
    wind_direction_80m,
    wind_direction_120m,
    wind_direction_180m,
    wind_gusts_10m,
    temperature_80m
)
SET
    date_time = STR_TO_DATE(REPLACE(@date_var, '+00:00', ''), '%Y-%m-%d %H:%i:%s') -- Rheinhaven
    --  date_time = STR_TO_DATE(@date_var, '%Y-%m-%d %H:%i:%s') -- cuxhaven;
    ;

