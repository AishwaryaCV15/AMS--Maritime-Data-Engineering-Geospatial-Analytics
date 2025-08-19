-- Step 1: Drop the existing table (if it exists)
-- This will delete all data in the table. Make sure you are okay with this.
DROP TABLE IF EXISTS ais_ship_data;

CREATE TABLE IF NOT EXISTS ais_ship_data (
    mmsi                     BIGINT          NOT NULL,
    datetime_utc                TIMESTAMP       NOT NULL, -- Stored as UTC (kept NOT NULL as per previous definition)
    datetime_interpolated       TIMESTAMP       NOT NULL, -- (kept NOT NULL as per previous definition)
    recv_time                   BIGINT          NOT NULL,
    latitude                    DOUBLE PRECISION NOT NULL, -- (kept NOT NULL as per previous definition)
    longitude                   DOUBLE PRECISION not NULL, -- (kept NOT NULL as per previous definition)
    sog                         DOUBLE PRECISION  NULL, -- Speed Over Ground (kept NOT NULL as per previous definition)
    cog                         DOUBLE PRECISION  NULL, -- Course Over Ground (kept NOT NULL as per previous definition)
    true_heading                INT              NULL, -- (kept NOT NULL as per previous definition)
    navigational_status         INT             NOT NULL,
    message_id                  INT             NOT NULL,
    raim_flag                   INT             NULL, -- Renamed from 'RAIM-flag'
    special_manoeuvre_indicator INT              NULL,
    rate_of_turn_rotais         INT              NULL, -- (kept NOT NULL as per previous definition)
    timestamp_ais               INT             NOT NULL, -- Renamed from 'Timestamp' to avoid keyword conflict (kept NOT NULL as per previous definition)
    position_accuracy           INT              NULL -- (kept NOT NULL as per previous definition)
);
