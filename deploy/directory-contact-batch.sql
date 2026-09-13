BEGIN;
CREATE TABLE IF NOT EXISTS records.facility_contact_details (
 jail_id text PRIMARY KEY REFERENCES public."Jail"(id),
 source_url text NOT NULL CHECK(source_url LIKE 'https://%'),
 contact_url text,
 department_phones jsonb NOT NULL DEFAULT '{}'::jsonb,
 verified_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS records.directory_enrichment_queue (
 county_id text PRIMARY KEY REFERENCES public."County"(id),
 status text NOT NULL DEFAULT 'needs_research' CHECK(status IN ('needs_research','in_progress','reviewed','blocked')),
 notes text,
 updated_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO records.directory_enrichment_queue(county_id)
SELECT id FROM public."County" ON CONFLICT DO NOTHING;

UPDATE public."Jail" j SET address=v.address,city=v.city,"zipCode"=v.zip,
 phone=v.phone,website=v.url,"isActive"=true,"updatedAt"=now()
FROM (VALUES
 ('census-landmark-1104493008840','402 Simpson Road','Kissimmee','34744','407-742-4444','https://www.osceola.org/Services/Corrections-and-Jail-Services'),
 ('census-landmark-1104490197861','27745 West 159th Street','New Century','66031','913-715-5900','https://www.jocogov.org/johnson-county-sheriff/detention-bureau'),
 ('census-landmark-1104490197348','101 North Kansas Avenue','Olathe','66061','913-715-5100','https://www.jocogov.org/johnson-county-sheriff/detention-bureau')
) v(id,address,city,zip,phone,url) WHERE j.id=v.id;

INSERT INTO records.facility_contact_details(jail_id,source_url,contact_url,department_phones)
VALUES
 ('census-landmark-1104493008840','https://www.osceola.org/Services/Corrections-and-Jail-Services',
 'https://www.osceola.org/Government/Agencies-and-Departments-Directory/Corrections-Department/Corrections-Department-Contact-Information',
 '{"records":"407-742-4411","visitation_appointments":"407-742-4400","visitation_front_desk":"407-742-4403","bonds_and_dockets":"407-742-4404"}'),
 ('census-landmark-1104490197861','https://www.jocogov.org/johnson-county-sheriff/detention-bureau','https://www.jocogov.org/johnson-county-sheriff/contact-us','{}'),
 ('census-landmark-1104490197348','https://www.jocogov.org/johnson-county-sheriff/detention-bureau','https://www.jocogov.org/johnson-county-sheriff/contact-us','{}')
ON CONFLICT(jail_id) DO UPDATE SET source_url=EXCLUDED.source_url,contact_url=EXCLUDED.contact_url,
 department_phones=EXCLUDED.department_phones,verified_at=now();

UPDATE records.directory_enrichment_queue SET status='in_progress',
 notes='Initial facility contacts verified from official operator pages; county-wide completeness still requires review.',updated_at=now()
WHERE county_id IN (SELECT id FROM public."County" WHERE "fipsCode" IN ('12097','20091'));

CREATE TABLE IF NOT EXISTS records.aggregate_jail_statistics (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 state_id text NOT NULL REFERENCES public."State"(id),
 county_id text REFERENCES public."County"(id),
 jail_id text REFERENCES public."Jail"(id),
 metric text NOT NULL CHECK(metric IN ('average_daily_population','point_in_time_population','rated_capacity')),
 value numeric NOT NULL CHECK(value>=0),
 period_start date NOT NULL,
 period_end date NOT NULL CHECK(period_end>=period_start),
 geographic_scope text NOT NULL,
 source_url text NOT NULL CHECK(source_url LIKE 'https://%'),
 source_notes text NOT NULL,
 retrieved_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(source_url,geographic_scope,metric,period_start,period_end)
);
COMMIT;
