LOAD DATA LOCAL INFILE 'D:/ovgu/sem3/AMS/Data/Main files/final_merged_vessel_data.csv'
INTO TABLE vessel_data
FIELDS TERMINATED BY ','
ENCLOSED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
    user_id,
    recv_time,
    latitude,
    longitude,
    @datetime_utc_var,
    @datetime_interpolated_var,
    cog,
    call_sign,
    destination,
    message_id,
    name,
    position_accuracy,
    rate_of_turn_rotais,
    sog,
    time_stamp,
    true_heading,
    latitude_min,
    latitude_max,
    longitude_min,
    longitude_max,
    speed_min,
    speed_max,
    call_sign_duplicate,
    ship_type,
    length_m,
    beam_m,
    beam_category
)
SET
    datetime_utc = STR_TO_DATE(@datetime_utc_var, '%Y-%m-%d %H:%i:%s.%f'),
    datetime_interpolated = STR_TO_DATE(@datetime_interpolated_var, '%Y-%m-%d %H:%i:%s');