-- Draft migration — facility ↔ jurisdiction bridge
-- Authority: MISSION.md Red tier (schema change). NOT APPLIED.
--
-- Problem this solves: public."Jail".id is a Census TIGERweb landmark key
-- ('census-landmark-<OID>'), while records.jurisdictions is a UUID keyed by
-- (state, county). Nothing links them. A naive (state, normalized county,
-- name-slug) match finds 3 of 3,531. Without this table, "is this facility
-- ingesting?" cannot be answered, which blocks facility pages, per-facility FOIA
-- tracking, and per-facility coverage reporting.
--
-- Additive only: creates one new table. Alters nothing, drops nothing, updates
-- no existing row.

CREATE TABLE IF NOT EXISTS records.facility_jurisdiction_map (
  jail_id          text PRIMARY KEY REFERENCES public."Jail"(id) ON DELETE CASCADE,
  jurisdiction_id  uuid REFERENCES records.jurisdictions(id) ON DELETE SET NULL,
  match_method     text NOT NULL
                     CHECK (match_method IN ('name_exact','name_alias','manual','unmatched')),
  match_confidence numeric(3,2) NOT NULL DEFAULT 0.00,
  reviewed_by      text,
  reviewed_at      timestamptz,
  notes            text,
  created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS facility_jurisdiction_map_jur_idx
  ON records.facility_jurisdiction_map (jurisdiction_id);
CREATE INDEX IF NOT EXISTS facility_jurisdiction_map_method_idx
  ON records.facility_jurisdiction_map (match_method);

GRANT SELECT, INSERT, UPDATE, DELETE ON records.facility_jurisdiction_map TO jailmap_app;


-- ---------------------------------------------------------------------------
-- STEP 1 — seed the automatic matches (expected: 3 rows)
-- Review these before trusting them; they are name collisions until a human says
-- otherwise. `countyKey()` in src/lib/county-slug.ts is mirrored here.
-- ---------------------------------------------------------------------------

INSERT INTO records.facility_jurisdiction_map
  (jail_id, jurisdiction_id, match_method, match_confidence, notes)
SELECT l.jail_id, jur.id, 'name_exact', 1.00,
       'auto-matched on state + normalized county + facility name slug'
FROM (
  SELECT j.id AS jail_id,
         s.abbrev AS st,
         regexp_replace(lower(c.name), '\s+county$', '') AS cty,
         regexp_replace(lower(j.name), '[^a-z0-9]+', '-', 'g') AS name_slug
    FROM public."Jail" j
    JOIN public."County" c ON c.id = j."countyId"
    JOIN public."State"  s ON s.id = j."stateId"
) l
JOIN records.jurisdictions jur
  ON jur.state = l.st
 AND regexp_replace(lower(jur.county), '\s+county$', '') = l.cty
 AND regexp_replace(lower(jur.facility_name), '[^a-z0-9]+', '-', 'g') = l.name_slug
ON CONFLICT (jail_id) DO NOTHING;


-- ---------------------------------------------------------------------------
-- STEP 2 — record the remainder as a VISIBLE work queue (expected: ~3,528 rows)
-- Approve separately from step 1 if you want the table populated in stages.
-- Reason: an unmatched row is information. An absent row is an unknown.
-- ---------------------------------------------------------------------------

INSERT INTO records.facility_jurisdiction_map (jail_id, match_method, match_confidence, notes)
SELECT j.id, 'unmatched', 0.00,
       'no automatic match; requires manual review against an official source'
  FROM public."Jail" j
ON CONFLICT (jail_id) DO NOTHING;


-- ---------------------------------------------------------------------------
-- Verification
-- ---------------------------------------------------------------------------
-- SELECT match_method, count(*) FROM records.facility_jurisdiction_map GROUP BY 1 ORDER BY 2 DESC;
-- Expected: unmatched ~3,528 · name_exact 3
