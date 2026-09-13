BEGIN;
ALTER TABLE records.jurisdictions ADD COLUMN IF NOT EXISTS county_id text REFERENCES public."County"(id);
UPDATE records.jurisdictions j SET county_id=c.id
FROM public."County" c JOIN public."State" s ON s.id=c."stateId"
WHERE j.county_id IS NULL AND j.state=s.abbrev
 AND (lower(j.county)=lower(c.name) OR lower(j.county || ' County')=lower(c.name));
CREATE UNIQUE INDEX IF NOT EXISTS "County_id_stateId_key" ON public."County"(id,"stateId");
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='Jail_county_state_consistent') THEN
  ALTER TABLE public."Jail" ADD CONSTRAINT "Jail_county_state_consistent"
   FOREIGN KEY ("countyId","stateId") REFERENCES public."County"(id,"stateId");
 END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='jurisdiction_staging_not_public') THEN
  ALTER TABLE records.jurisdictions ADD CONSTRAINT jurisdiction_staging_not_public CHECK (NOT (enabled AND staging_only));
 END IF;
END $$;
CREATE OR REPLACE FUNCTION records.check_source_geography() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE facility_county text; county_state text;
BEGIN
 IF NEW.jail_id IS NOT NULL THEN
  SELECT "countyId" INTO facility_county FROM public."Jail" WHERE id=NEW.jail_id;
  IF NEW.county_id IS NULL THEN NEW.county_id=facility_county; END IF;
  IF NEW.county_id IS DISTINCT FROM facility_county THEN RAISE EXCEPTION 'Source county does not match facility county'; END IF;
 END IF;
 IF NEW.county_id IS NOT NULL THEN
  SELECT s.abbrev INTO county_state FROM public."County" c JOIN public."State" s ON s.id=c."stateId" WHERE c.id=NEW.county_id;
  IF NEW.state IS DISTINCT FROM county_state THEN RAISE EXCEPTION 'Source state does not match county state'; END IF;
 END IF;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS check_source_geography ON records.jurisdictions;
CREATE TRIGGER check_source_geography BEFORE INSERT OR UPDATE ON records.jurisdictions
FOR EACH ROW EXECUTE FUNCTION records.check_source_geography();
CREATE OR REPLACE VIEW records.state_ingestion_status AS
 SELECT s.abbrev,s.name,
  (SELECT count(*) FROM public."County" c WHERE c."stateId"=s.id) AS counties,
  (SELECT count(*) FROM public."Jail" j WHERE j."stateId"=s.id) AS facilities,
  (SELECT count(*) FROM records.jurisdictions r WHERE r.state=s.abbrev AND r.enabled AND r.review_status='verified') AS enabled_sources,
  (SELECT count(*) FROM records.county_ingestion_queue q JOIN public."County" c ON c.id=q.county_id
   WHERE c."stateId"=s.id AND q.status='source_discovery') AS counties_needing_discovery,
  (SELECT count(*) FROM public."Jail" j WHERE j."stateId"=s.id AND j."isActive") AS public_directory_facilities,
  (SELECT count(*) FROM records.jurisdictions r WHERE r.state=s.abbrev AND r.staging_only) AS staging_sources,
  (SELECT count(*) FROM records.staged_bookings b JOIN records.jurisdictions r ON r.id=b.jurisdiction_id
   WHERE r.state=s.abbrev) AS staged_bookings
 FROM public."State" s;
COMMIT;
