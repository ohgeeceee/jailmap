-- Independent schema: does not alter the existing Prisma map models.
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE SCHEMA IF NOT EXISTS records;
CREATE TABLE records.jurisdictions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  state char(2) NOT NULL CHECK (state ~ '^[A-Z]{2}$'),
  county text NOT NULL,
  facility_name text NOT NULL,
  source_url text NOT NULL CHECK (source_url LIKE 'https://%'),
  adapter text NOT NULL DEFAULT 'standard_json',
  authorization_reference text NOT NULL,
  enabled boolean NOT NULL DEFAULT false,
  last_success_at timestamptz,
  UNIQUE (state, county, facility_name)
);
-- One row per booking, not a cross-jurisdiction identity registry.
CREATE TABLE records.inmates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  jurisdiction_id uuid NOT NULL REFERENCES records.jurisdictions(id),
  booking_number text NOT NULL,
  first_name text NOT NULL,
  last_name text NOT NULL,
  dob date, -- restricted; never returned by public API or search index
  booking_date timestamptz NOT NULL,
  booking_date_precision text NOT NULL DEFAULT 'timestamp' CHECK (booking_date_precision IN ('date','timestamp')),
  booking_timezone text NOT NULL DEFAULT 'UTC',
  mugshot_url text, -- restricted by default
  source_updated_at timestamptz NOT NULL,
  observed_at timestamptz NOT NULL DEFAULT now(),
  visibility text NOT NULL DEFAULT 'public' CHECK (visibility IN ('public','suppressed','released','unlisted')),
  version bigint NOT NULL DEFAULT 1,
  UNIQUE (jurisdiction_id, booking_number)
);
CREATE INDEX inmate_name_trgm ON records.inmates USING gin ((lower(first_name || ' ' || last_name)) gin_trgm_ops);
CREATE INDEX inmate_last_first ON records.inmates (lower(last_name), lower(first_name));
CREATE INDEX inmate_jurisdiction_booking ON records.inmates (jurisdiction_id, booking_date DESC);
CREATE INDEX jurisdiction_location ON records.jurisdictions (state, county) WHERE enabled;
CREATE TABLE records.charges (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  inmate_id uuid NOT NULL REFERENCES records.inmates(id) ON DELETE CASCADE,
  source_id text NOT NULL,
  statute text,
  description text NOT NULL,
  severity text,
  UNIQUE (inmate_id, source_id)
);
CREATE TABLE records.bonds (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  inmate_id uuid NOT NULL REFERENCES records.inmates(id) ON DELETE CASCADE,
  source_id text NOT NULL,
  amount numeric(14,2) CHECK (amount >= 0),
  currency char(3) NOT NULL DEFAULT 'USD',
  type text NOT NULL,
  status text NOT NULL,
  UNIQUE (inmate_id, source_id)
);
CREATE TABLE records.search_outbox (
  inmate_id uuid PRIMARY KEY REFERENCES records.inmates(id) ON DELETE CASCADE,
  version bigint NOT NULL,
  queued_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE records.correction_requests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  booking_id uuid NOT NULL REFERENCES records.inmates(id),
  email text NOT NULL,
  kind text NOT NULL CHECK (kind IN ('correction','removal')),
  reason text NOT NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected')),
  submitted_at timestamptz NOT NULL DEFAULT now(),
  reviewed_at timestamptz,
  reviewer text,
  review_note text
);
CREATE INDEX corrections_pending ON records.correction_requests (submitted_at) WHERE status = 'pending';
