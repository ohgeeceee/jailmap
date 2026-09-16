import os
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

pool = ConnectionPool(os.environ['DATABASE_URL'], min_size=2, max_size=20,
                      kwargs={'row_factory': dict_row}, open=False)

# Public projection is explicit: DOB, image URL and request details stay private.
PUBLIC_SELECT = """
SELECT i.id::text AS id, i.first_name, i.last_name, i.booking_number,
       i.booking_date, i.booking_date_precision, i.booking_timezone, i.observed_at, j.state, j.county, j.facility_name,
       CASE WHEN j.adapter='fulton_public_roster' THEN 'Approximate county roster snapshot from the previous evening. Booking dates do not include a time; age and specific facility are not provided.' ELSE NULL END AS source_note,
       j.source_url,
       COALESCE((SELECT jsonb_agg(jsonb_build_object('statute',c.statute,
           'description',c.description,'severity',c.severity) ORDER BY c.id)
           FROM records.charges c WHERE c.inmate_id=i.id),'[]') AS charges,
       COALESCE((SELECT jsonb_agg(jsonb_build_object('amount',b.amount,
           'type',b.type,'status',b.status,'currency',b.currency) ORDER BY b.id)
           FROM records.bonds b WHERE b.inmate_id=i.id),'[]') AS bonds
FROM records.inmates i JOIN records.jurisdictions j ON j.id=i.jurisdiction_id
"""
PUBLIC_WHERE = """i.visibility='public' AND j.enabled AND j.review_status='verified'
 AND i.observed_at > now() - interval '48 hours'"""
