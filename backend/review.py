"""Restricted operator CLI: approve a request by suppressing pending verification.
Run with request UUID, reviewer identity and an audit note; no public admin route.
"""
import argparse
from uuid import UUID
from backend.db import pool

def approve(request_id, reviewer, note):
    with pool, pool.connection() as connection, connection.transaction():
        request = connection.execute('SELECT * FROM records.correction_requests WHERE id=%s FOR UPDATE', (request_id,)).fetchone()
        if not request or request['status'] != 'pending':
            raise ValueError('Pending request not found')
        row = connection.execute("""UPDATE records.inmates SET visibility='suppressed',version=version+1
            WHERE id=%s RETURNING id,version""", (request['booking_id'],)).fetchone()
        connection.execute('''INSERT INTO records.search_outbox(inmate_id,version) VALUES (%s,%s)
            ON CONFLICT(inmate_id) DO UPDATE SET version=EXCLUDED.version,queued_at=now()''', (row['id'],row['version']))
        connection.execute("""UPDATE records.correction_requests SET status='approved',reviewed_at=now(),
            reviewer=%s,review_note=%s WHERE id=%s""", (reviewer,note,request_id))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('request_id', type=UUID)
    parser.add_argument('--reviewer', required=True)
    parser.add_argument('--note', required=True)
    args = parser.parse_args()
    approve(args.request_id, args.reviewer, args.note)
