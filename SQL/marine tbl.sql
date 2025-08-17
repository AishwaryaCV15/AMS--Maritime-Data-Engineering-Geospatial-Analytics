DROP TABLE IF EXISTS marine_data;
CREATE TABLE IF NOT EXISTS marine_data (
    date_time                       TIMESTAMP           NOT NULL,
    latitude                    DOUBLE PRECISION    NOT NULL,
    longitude                   DOUBLE PRECISION    NOT NULL,
    wave_height_m              DOUBLE PRECISION    NOT NULL,
    wave_period_s             DOUBLE PRECISION    NOT NULL,
    wave_direction_deg                 DOUBLE PRECISION    NOT NULL,
    wind_wave_height_m              DOUBLE PRECISION    NOT NULL,
    wind_wave_direction_deg              DOUBLE PRECISION    NOT NULL,
    current_velocity_mps              DOUBLE PRECISION    NOT NULL,
    current_direction_deg             DOUBLE PRECISION    NOT NULL
);
