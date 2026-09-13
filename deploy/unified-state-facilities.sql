BEGIN;
INSERT INTO public."Jail"(id,name,address,city,website,"countyId","stateId","isActive","updatedAt")
SELECT v.id,v.name,v.address,v.city,v.url,c.id,c."stateId",true,now()
FROM (VALUES
 ('jail-hi-occc','Oahu Community Correctional Center','2199 Kamehameha Highway','Honolulu','15003',
  'https://dcr.hawaii.gov/about/divisions/corrections/occc/'),
 ('jail-vt-crcf','Chittenden Regional Correctional Facility','7 Farrell Street','South Burlington','50007',
  'https://doc.vermont.gov/correctional-facilities/crcf-south-burlington'),
 ('jail-de-hryci','Howard R. Young Correctional Institution','1301 East 12th Street','Wilmington','10003',
  'https://www.doc.delaware.gov/views/hryci.blade.shtml')
) AS v(id,name,address,city,fips,url)
JOIN public."County" c ON c."fipsCode"=v.fips
ON CONFLICT(id) DO NOTHING;
INSERT INTO records.facility_sources(jail_id,source_id,source_url,source_vintage,verification_note)
SELECT id,id,website,'Official state facility directory, checked 2026-09-07',
 'State-operated detention/correctional facility. Source is a directory, not a live booking feed. Contacts corroborated by state government sources.'
FROM public."Jail" WHERE id IN ('jail-hi-occc','jail-vt-crcf','jail-de-hryci')
ON CONFLICT(jail_id) DO NOTHING;
INSERT INTO records.facility_ingestion_queue(jail_id)
SELECT id FROM public."Jail" WHERE id IN ('jail-hi-occc','jail-vt-crcf','jail-de-hryci')
ON CONFLICT DO NOTHING;
COMMIT;
