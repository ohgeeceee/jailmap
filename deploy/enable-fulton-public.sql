-- Apply only after the roster-publication migration and the matching API/web release.
BEGIN;
UPDATE records.jurisdictions SET enabled=true
 WHERE adapter='fulton_public_roster' AND review_status='verified' AND NOT staging_only;
UPDATE records.county_ingestion_queue SET status='active',adapter='fulton_public_roster',
 notes='Official public named roster enabled. Only source-provided names and date-only bookings; no age assertion, charges/bonds or precise facility assignment. Inconsistent dates and redacted placeholders withheld. Complete-snapshot omissions become unlisted, never assumed released.',updated_at=now()
 WHERE county_id=(SELECT id FROM public."County" WHERE "fipsCode"='13121');
COMMIT;
