BEGIN;
INSERT INTO public."Jail"(id,name,address,city,"zipCode",website,"countyId","stateId","isActive","updatedAt")
SELECT 'jail-ga-fulton-main','Fulton County Jail - Main Jail','901 Rice Street NW','Atlanta','30318',
 'https://gdc.georgia.gov/locations/fulton-county-jail',c.id,c."stateId",true,now()
 FROM public."County" c WHERE c."fipsCode"='13121'
ON CONFLICT(id) DO NOTHING;
INSERT INTO records.jurisdictions(state,county,facility_name,source_url,adapter,authorization_reference,enabled,staging_only,review_status)
VALUES ('GA','Fulton','Fulton County detention facilities (facility not specified)',
 'https://sharefulton.fultoncountyga.gov/resource/3vfv-9mmr.json','fulton_socrata_staging',
 'Fulton County public open data, dataset 3vfv-9mmr, CC BY 4.0; verified 2026-09-07; staging only pending adult eligibility. Attribution: Fulton County, Georgia, https://sharefulton.fultoncountyga.gov/d/3vfv-9mmr',false,true,'verified')
ON CONFLICT(state,county,facility_name) DO UPDATE SET adapter=EXCLUDED.adapter,
 source_url=EXCLUDED.source_url,authorization_reference=EXCLUDED.authorization_reference,
 enabled=false,staging_only=true,review_status='verified';
UPDATE records.county_ingestion_queue SET status='testing',
 source_url='https://sharefulton.fultoncountyga.gov/d/3vfv-9mmr',adapter='fulton_socrata_staging',
 notes='Live nightly public roster staged privately. Feed has no age/adult eligibility or precise facility, and provides date-only booking dates. Charges/bonds unavailable. Do not publish until eligibility is resolved.',updated_at=now()
 WHERE county_id=(SELECT id FROM public."County" WHERE "fipsCode"='13121');
UPDATE records.jurisdictions j SET review_status='invalid_county'
 WHERE state='MT' AND NOT enabled AND authorization_reference='pending'
 AND NOT EXISTS (SELECT 1 FROM public."County" c JOIN public."State" s ON s.id=c."stateId"
 WHERE s.abbrev='MT' AND lower(c.name)=lower(j.county || ' County'));
COMMIT;
