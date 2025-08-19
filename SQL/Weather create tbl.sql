DROP TABLE IF EXISTS weather_data;
CREATE TABLE IF NOT EXISTS weather_data (
    date_time                       TIMESTAMP           NOT NULL,
    latitude                    DOUBLE PRECISION    NOT NULL,
    longitude                   DOUBLE PRECISION    NOT NULL,
    temperature_2m              DOUBLE PRECISION    NOT NULL,
    wind_speed_10m             DOUBLE PRECISION    NOT NULL,
    visibility                 DOUBLE PRECISION    NOT NULL,
    wind_speed_80m              DOUBLE PRECISION    NOT NULL,
    wind_speed_120m              DOUBLE PRECISION    NOT NULL,
    wind_speed_180m              DOUBLE PRECISION    NOT NULL,
    wind_direction_10m             DOUBLE PRECISION    NOT NULL,
    wind_direction_80m             DOUBLE PRECISION    NOT NULL,
    wind_direction_120m          DOUBLE PRECISION    NOT NULL,
    wind_direction_180m          DOUBLE PRECISION    NOT NULL,
    wind_gusts_10m         DOUBLE PRECISION    NOT NULL,
    temperature_80m         DOUBLE PRECISION    NOT NULL
);
