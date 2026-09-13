BEGIN;
INSERT INTO records.jurisdictions(state,county,county_id,facility_name,source_url,adapter,authorization_reference,enabled,staging_only,review_status)
SELECT 'GA','Fulton',c.id,'Fulton County public jail roster (facility not specified)',
 'https://sharefulton.fultoncountyga.gov/resource/3vfv-9mmr.json','fulton_public_roster',
 'Official intentionally public named county roster, dataset 3vfv-9mmr, CC BY 4.0. Attribution: Fulton County, Georgia, https://sharefulton.fultoncountyga.gov/d/3vfv-9mmr. Publish source-provided names and dates only; no age assertion or enrichment. Inconsistent dates and redacted/juvenile placeholders withheld. Reviewed 2026-09-07.',
 false,false,'verified'
FROM public."County" c WHERE c."fipsCode"='13121'
ON CONFLICT(state,county,facility_name) DO NOTHING;
COMMIT;
