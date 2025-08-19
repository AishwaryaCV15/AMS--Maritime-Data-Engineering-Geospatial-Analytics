LOAD DATA LOCAL INFILE 'C:/Users/cvais/Documents/GitHub/AMS_ShipTraj/marine_weather_2025-03.csv'
INTO TABLE marine_data
FIELDS TERMINATED BY ','
ENCLOSED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 LINES -- Skips the header row
(
    @date_var,                     -- Read date into a user variable
    latitude,           
    longitude ,          
    wave_height_m          ,  
    wave_period_s          ,  
    wave_direction_deg     ,  
    wind_wave_height_m     ,  
    wind_wave_direction_deg,  
    current_velocity_mps   ,  
    current_direction_deg       
)
SET
    date_time = STR_TO_DATE(@date_var, '%Y-%m-%d %H:%i:%s');

