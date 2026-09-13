BEGIN;
ALTER TABLE records.jurisdictions ADD COLUMN IF NOT EXISTS staging_only boolean NOT NULL DEFAULT false;
CREATE TABLE IF NOT EXISTS records.staged_bookings (
  jurisdiction_id uuid NOT NULL REFERENCES records.jurisdictions(id),
  booking_number text NOT NULL,
  payload jsonb NOT NULL,
  source_snapshot_at timestamptz NOT NULL,
  fetched_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY(jurisdiction_id,booking_number)
);
GRANT SELECT,INSERT,UPDATE,DELETE ON records.staged_bookings TO jailmap_app;
-- Staging does not enter the public inmate table or search outbox.
COMMIT;
