BEGIN;
ALTER TABLE records.inmates ADD COLUMN IF NOT EXISTS booking_date_precision text NOT NULL DEFAULT 'timestamp'
 CHECK (booking_date_precision IN ('date','timestamp'));
ALTER TABLE records.inmates ADD COLUMN IF NOT EXISTS booking_timezone text NOT NULL DEFAULT 'UTC';
ALTER TABLE records.inmates DROP CONSTRAINT IF EXISTS inmates_visibility_check;
ALTER TABLE records.inmates ADD CONSTRAINT inmates_visibility_check
 CHECK (visibility IN ('public','suppressed','released','unlisted'));
COMMIT;
