-- Additive, staging-only schema for the modular adapter framework.
CREATE SCHEMA IF NOT EXISTS records;

CREATE TABLE IF NOT EXISTS records.adapter_bookings_staging (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    facility_id TEXT NOT NULL REFERENCES public."Jail"(id),
    booking_number TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    middle_name TEXT,
    date_of_birth DATE,
    age INTEGER CHECK (age BETWEEN 0 AND 125),
    booking_date TIMESTAMPTZ,
    release_date TIMESTAMPTZ,
    charges JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(charges) = 'array'),
    total_bond_amount NUMERIC(14, 2) CHECK (total_bond_amount >= 0),
    mugshot_url TEXT,
    raw_data JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(raw_data) = 'object'),
    scraped_at TIMESTAMPTZ NOT NULL,
    publication_state TEXT NOT NULL DEFAULT 'staged'
        CHECK (publication_state IN ('staged', 'approved', 'suppressed', 'rejected')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (facility_id, booking_number)
);

CREATE INDEX IF NOT EXISTS adapter_bookings_review_idx
    ON records.adapter_bookings_staging (publication_state, scraped_at DESC);

CREATE TABLE IF NOT EXISTS records.adapter_failures (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    facility_id TEXT REFERENCES public."Jail"(id),
    adapter_driver TEXT NOT NULL,
    failure_stage TEXT NOT NULL CHECK (failure_stage IN ('fetch', 'parse', 'normalize', 'export', 'database')),
    error_type TEXT NOT NULL,
    safe_message TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ
);

COMMENT ON TABLE records.adapter_bookings_staging IS
    'Restricted ingestion staging. Not a public projection; approval is required before publication.';
COMMENT ON COLUMN records.adapter_bookings_staging.raw_data IS
    'Restricted source fallback; must never be emitted by public APIs.';

GRANT SELECT, INSERT, UPDATE ON records.adapter_bookings_staging TO jailmap_app;
GRANT SELECT, INSERT, UPDATE ON records.adapter_failures TO jailmap_app;
GRANT USAGE, SELECT ON SEQUENCE records.adapter_failures_id_seq TO jailmap_app;
