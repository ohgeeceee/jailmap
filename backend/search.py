import os
import time
import httpx

SETTINGS = {
    'searchableAttributes': ['first_name', 'last_name'],
    'displayedAttributes': ['id'],
    'filterableAttributes': ['state', 'county'],
    'sortableAttributes': ['booking_date'],
    'typoTolerance': {'enabled': True, 'minWordSizeForTypos': {'oneTypo': 5, 'twoTypos': 9}},
    'pagination': {'maxTotalHits': 1000},
}

def call(method, path, payload=None):
    response = httpx.request(method, os.environ['MEILI_URL'].rstrip('/') + path,
        headers={'Authorization': 'Bearer ' + os.environ['MEILI_KEY']}, json=payload, timeout=15)
    response.raise_for_status()
    return response.json()

def wait(task):
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        status = call('GET', f"/tasks/{task['taskUid']}")
        if status['status'] == 'succeeded':
            return
        if status['status'] in ('failed', 'canceled'):
            raise RuntimeError('Search indexing task failed')
        time.sleep(0.25)
    raise TimeoutError('Search indexing task timed out; outbox retained')

def configure():
    try:
        call('GET', '/indexes/bookings')
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code != 404:
            raise
        wait(call('POST', '/indexes', {'uid': 'bookings', 'primaryKey': 'id'}))
    wait(call('PATCH', '/indexes/bookings/settings', SETTINGS))

def drain(connection):
    # Serialize dispatchers to avoid an older task overwriting a newer document.
    with connection.transaction():
        connection.execute("SELECT pg_advisory_xact_lock(472913)")
        events = connection.execute('SELECT * FROM records.search_outbox ORDER BY queued_at LIMIT 100').fetchall()
        visible=[]
        hidden=[]
        for event in events:
            row = connection.execute("""SELECT i.id::text, i.first_name, i.last_name,
                j.state, j.county, extract(epoch FROM i.booking_date)::bigint AS booking_date,
                i.visibility='public' AND j.enabled AND j.review_status='verified' AND
                i.observed_at > now()-interval '48 hours' AS visible
                FROM records.inmates i JOIN records.jurisdictions j ON j.id=i.jurisdiction_id
                WHERE i.id=%s""", (event['inmate_id'],)).fetchone()
            if row['visible']:
                del row['visible']
                visible.append(row)
            else:
                hidden.append(event['inmate_id'])
        if visible:
            wait(call('POST', '/indexes/bookings/documents', visible))
        for id in hidden:
            wait(call('DELETE', f"/indexes/bookings/documents/{id}"))
        for event in events:
            connection.execute('DELETE FROM records.search_outbox WHERE inmate_id=%s AND version=%s',
                               (event['inmate_id'], event['version']))

if __name__ == '__main__':
    import sys
    from backend.db import pool
    if '--configure' in sys.argv:
        configure()
    else:
        with pool:
            with pool.connection() as connection:
                drain(connection)
