-- Verification queries for the Day-3 prep draft: agent-queue/jailmap-ops-captain/2026-09-14-index-and-facility-prep/
-- All read-only. Run against the records/postgres container:
--   docker compose exec -T postgres psql -U jailmap_owner -d jailmap -f - < sql/verify.sql


-- A1 — SEED NEXT: the sitemap must announce county pages.
--     before: 0      after: == count of content-eligible counties (A2)
--     (curl https://jailmap.com/sitemap.xml | grep -c 'county/')  -- cannot be run in psql
SELECT 'sitemap county URLs — check with curl, not SQL' AS note;


-- A2 — how many counties ARE content-eligible right now (enabled ingestion OR verified contact)
SELECT count(*) AS eligible_counties FROM (
  SELECT state, lower(county) FROM records.jurisdictions WHERE enabled
  UNION
  SELECT s.abbrev, regexp_replace(lower(c.name), '\s+county$', '')
    FROM public."Jail" j
    JOIN public."County" c ON c.id = j."countyId"
    JOIN public."State"  s ON s.id = j."stateId"
    JOIN records.facility_contact_details f ON f.jail_id = j.id
   WHERE f.verified_at IS NOT NULL
) t;


-- B1 — the join gap, stated as a number. Expected: matched 3 of 3531.
WITH jails AS (
  SELECT s.abbrev AS st,
         regexp_replace(lower(c.name), '\s+county$', '') AS cty,
         regexp_replace(lower(j.name), '[^a-z0-9]+', '-', 'g') AS name_slug,
         j.id AS jail_id
    FROM public."Jail" j
    JOIN public."County" c ON c.id = j."countyId"
    JOIN public."State"  s ON s.id = j."stateId"
)
SELECT count(*) FILTER (WHERE jur.id IS NOT NULL) AS matched, count(*) AS total_jails
  FROM jails l
  LEFT JOIN records.jurisdictions jur
    ON jur.state = l.st
   AND regexp_replace(lower(jur.county), '\s+county$', '') = l.cty
   AND regexp_replace(lower(jur.facility_name), '[^a-z0-9]+', '-', 'g') = l.name_slug;


-- B2 — after the migration: the bridge state
-- SELECT match_method, count(*) FROM records.facility_jurisdiction_map GROUP BY 1 ORDER BY 2 DESC;


-- C1 — enrichment reality. Expected now: address 7, phone 3, contact rows 3.
SELECT count(*) AS jails,
       count(address) AS has_addr,
       count(phone)   AS has_phone,
       count(latitude) AS has_geo,
       count(DISTINCT "countyId") AS counties
  FROM public."Jail";

SELECT count(*) AS contact_rows,
       count(*) FILTER (WHERE verified_at IS NOT NULL) AS verified
  FROM records.facility_contact_details;

SELECT count(*) AS unworked_enrichment_rows FROM records.directory_enrichment_queue;


-- C2 — slug collisions that will break /jail/... routes (duplicate names, distinct landmark ids)
SELECT lower(name) AS name_lower, count(*) AS n
  FROM public."Jail"
 GROUP BY 1 HAVING count(*) > 1
 ORDER BY n DESC, name_lower
 LIMIT 15;
