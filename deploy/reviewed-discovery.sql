BEGIN;
UPDATE records.county_ingestion_queue q SET source_url=v.url,status='blocked',notes=v.note,updated_at=now()
FROM (VALUES
 ('30063','https://webapps.missoulacounty.us/jailroster/inmates.aspx',
  'Official Missoula County roster. VPS GET returned HTTP 403 on 2026-09-07. Requires a permitted feed/access arrangement; no bypass attempted.'),
 ('30029','https://apps.flathead.mt.gov/jailroster/',
  'Official Flathead County roster. VPS GET returned HTTP 403 on 2026-09-07. Source also uses person PINs; stable booking-episode identity needs verification.'),
 ('30111','https://www.yellowstonecountymt.gov/Sheriff/Detention/dcsearch.asp',
  'Official Yellowstone County search requires a human verification question. No unattended adapter enabled.'),
 ('53033','https://data.kingcounty.gov/resource/j56h-zgnm.json',
  'Verified official monthly adult booking dataset; as of September 2 it covers September 2025 through August 2026. Unsuitable for claiming current custody. The earlier configured 43nn-2689 endpoint returns 404.'),
 ('01089','https://www.madisoncountysheriffal.org/inmate-roster',
  'Official Madison County AL roster. VPS GET returned HTTP 403 on 2026-09-07. Requires permitted feed/access arrangement.')
) AS v(fips,url,note),public."County" c
WHERE c."fipsCode"=v.fips AND q.county_id=c.id;
UPDATE records.county_ingestion_queue q SET notes=
 'Connecticut uses state-operated jail/prison facilities and nine Census planning regions. The reviewed daily Socrata datasets b674-jy6w and um73-fxm4 have identifiers but no names; they cannot populate the current named-booking contract. Plan a separate aggregate-population adapter.',updated_at=now()
FROM public."County" c JOIN public."State" s ON s.id=c."stateId"
WHERE q.county_id=c.id AND s.abbrev='CT' AND q.source_url IS NULL;
COMMIT;
