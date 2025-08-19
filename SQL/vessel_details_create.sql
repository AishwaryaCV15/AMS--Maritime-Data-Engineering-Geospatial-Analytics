CREATE TABLE IF NOT EXISTS ais_ship_details (
    mmsi         BIGINT          NOT NULL,
    name            VARCHAR(255)    NULL,
    destination     VARCHAR(255)    NULL,
    eta             BIGINT          NULL, -- Assuming ETA is a numerical representation of time
    max_draught     DOUBLE PRECISION NULL,
    ship_type       INT             NULL,
    imo_number      BIGINT          NULL,
    call_sign       VARCHAR(10)     NULL,
    length_m        DOUBLE PRECISION NULL, -- Using DOUBLE PRECISION for length as some values might be decimal
    beam_m          DOUBLE PRECISION NULL, -- Using DOUBLE PRECISION for beam as some values might be decimal
    beam_category   VARCHAR(255)    NULL,
    dimension_a     INT             NULL,
    dimension_b     INT             NULL,
    dimension_c     INT             NULL,
    dimension_d     INT             NULL
);
