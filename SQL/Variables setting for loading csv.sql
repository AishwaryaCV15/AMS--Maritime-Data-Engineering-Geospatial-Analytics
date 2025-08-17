-- Check current status (optional)
SHOW GLOBAL VARIABLES LIKE 'local_infile';

-- Enable local_infile
SET GLOBAL local_infile = 'ON';

-- Confirm it's enabled (optional)
SHOW GLOBAL VARIABLES LIKE 'local_infile';