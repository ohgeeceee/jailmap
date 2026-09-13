import hashlib
import hmac
import json
import os
from contextlib import asynccontextmanager
from typing import Literal
from uuid import UUID

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field
from redis import Redis, RedisError
from backend.db import pool, PUBLIC_SELECT, PUBLIC_WHERE
from backend.search import call

@asynccontextmanager
async def lifespan(app):
    pool.open()
    yield
    pool.close()

app = FastAPI(title='JailMap authorized records API', lifespan=lifespan,
              docs_url=None, redoc_url=None, openapi_url=None)
redis = Redis.from_url(os.environ['REDIS_URL'], socket_timeout=2, socket_connect_timeout=2)

@app.get('/healthz')
def health():
    try:
        with pool.connection() as connection:
            connection.execute('SELECT 1 FROM records.jurisdictions LIMIT 1')
        redis.ping()
        call('GET', '/health')
        return {'status': 'ok'}
    except Exception:
        raise HTTPException(503, 'Service unavailable')

RATE_SCRIPT = """
local n = redis.call('INCR', KEYS[1])
if n == 1 then redis.call('EXPIRE', KEYS[1], 60) end
return n
"""

@app.middleware('http')
async def private_responses(request, call_next):
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Robots-Tag'] = 'noindex, noarchive'
    return response

def guard(request: Request, limit=60):
    # Only the private Next.js gateway may supply client identity.
    expected = os.environ['RECORDS_API_TOKEN']
    if len(expected) < 32 or not hmac.compare_digest(request.headers.get('x-gateway-token', ''), expected):
        raise HTTPException(401, 'Unauthorized gateway')
    client = request.headers.get('x-records-client', 'shared')
    key = hashlib.sha256(client.encode()).hexdigest()
    bucket = 'corrections' if request.method == 'POST' else 'read'
    try:
        count = redis.eval(RATE_SCRIPT, 1, f'rate:{bucket}:{key}')
    except RedisError:
        raise HTTPException(503, 'Rate limiter unavailable')
    if count > limit:
        raise HTTPException(429, 'Too many requests', headers={'Retry-After': '60'})

@app.get('/api/search')
def search(request: Request, name: str = Query(min_length=2, max_length=100),
           state: str | None = Query(None, pattern='^[A-Z]{2}$'),
           county: str | None = Query(None, min_length=1, max_length=100),
           page: int = Query(1, ge=1, le=40)):
    guard(request)
    if len(name.strip()) < 2:
        raise HTTPException(422, 'Enter at least two characters')
    filters = [f'{field} = {json.dumps(value)}' for field, value in [('state', state), ('county', county)] if value]
    try:
        result = call('POST', '/indexes/bookings/search', {'q': name.strip(),
            'filter': filters, 'limit': 25, 'offset': (page-1)*25,
            'matchingStrategy': 'all', 'attributesToRetrieve': ['id']})
    except (httpx.HTTPError, ValueError):
        raise HTTPException(503, 'Search temporarily unavailable')
    ids = [UUID(hit['id']) for hit in result['hits']]
    with pool.connection() as connection:
        # Never trust stale index content for disclosure or current filters.
        rows = connection.execute(PUBLIC_SELECT + ' WHERE ' + PUBLIC_WHERE +
            ' AND i.id = ANY(%s) AND (%s::text IS NULL OR j.state=%s)'
            ' AND (%s::text IS NULL OR j.county=%s)', (ids, state, state, county, county)).fetchall()
    order = {str(id): position for position, id in enumerate(ids)}
    rows.sort(key=lambda row: order[row['id']])
    return {'items': rows, 'page': page, 'has_more': len(ids) == 25 and page < 40}

@app.get('/api/new-bookings')
def new_bookings(request: Request, limit: int = Query(50, ge=1, le=100)):
    guard(request)
    with pool.connection() as connection:
        rows = connection.execute("""
            SELECT i.id::text AS id, i.first_name, i.last_name,
                   i.booking_date, j.state, j.county, j.facility_name
            FROM records.inmates i
            JOIN records.jurisdictions j ON j.id=i.jurisdiction_id
            WHERE """ + PUBLIC_WHERE + """
              AND i.booking_date <= now()
              AND i.booking_date > now() - interval '48 hours'
            ORDER BY i.booking_date DESC
            LIMIT %s
        """, (limit,)).fetchall()
    from datetime import datetime, timezone
    return {'items': rows, 'generated_at': datetime.now(timezone.utc).isoformat()}


@app.get('/api/inmate/{booking_id}')
def inmate(booking_id: UUID, request: Request):
    guard(request)
    with pool.connection() as connection:
        row = connection.execute(PUBLIC_SELECT + ' WHERE ' + PUBLIC_WHERE + ' AND i.id=%s', (booking_id,)).fetchone()
    if not row:
        raise HTTPException(404, 'Booking unavailable')
    return row

@app.get('/api/jurisdictions')
def jurisdictions(request: Request):
    guard(request)
    with pool.connection() as connection:
        return connection.execute('''SELECT id::text, state, county, facility_name,
            source_url, last_success_at FROM records.jurisdictions
            WHERE enabled AND review_status='verified' ORDER BY state, county, facility_name''').fetchall()

class Correction(BaseModel):
    booking_id: UUID
    email: str = Field(min_length=3, max_length=254, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    kind: Literal['correction', 'removal']
    reason: str = Field(min_length=20, max_length=4000)

@app.post('/api/corrections', status_code=202)
def correction(body: Correction, request: Request):
    guard(request, limit=5)
    with pool.connection() as connection:
        # Identical response for unknown IDs avoids a private-booking oracle.
        connection.execute('''INSERT INTO records.correction_requests(booking_id,email,kind,reason)
            SELECT id,%s,%s,%s FROM records.inmates WHERE id=%s''',
            (body.email, body.kind, body.reason, body.booking_id))
    return {'message': 'Request received for review. Submission does not automatically change a record.'}

def admin_guard(request: Request):
    guard(request)
    # Only the authenticated private Next.js gateway sets this after a live role check.
    try:
        return str(UUID(request.headers.get('x-records-admin', '')))
    except ValueError:
        raise HTTPException(403, 'Administrator access required')

@app.get('/api/admin/overview')
def admin_overview(request: Request):
    admin_guard(request)
    with pool.connection() as connection:
        sources = connection.execute('''SELECT id::text,state,county,facility_name,source_url,
            enabled,last_success_at FROM records.jurisdictions ORDER BY state,county LIMIT 100''').fetchall()
        pending = connection.execute("""SELECT id::text,booking_id::text,kind,reason,submitted_at
            FROM records.correction_requests WHERE status='pending' ORDER BY submitted_at LIMIT 50""").fetchall()
        counts = connection.execute("""SELECT
            (SELECT count(*) FROM records.search_outbox) AS outbox,
            (SELECT count(*) FROM records.correction_requests WHERE status='pending') AS pending,
            (SELECT count(*) FROM records.jurisdictions) AS sources""").fetchone()
    return {'sources': sources, 'requests': pending, 'counts': counts}

class Review(BaseModel):
    decision: Literal['approve', 'reject']
    note: str = Field(min_length=20, max_length=2000)

@app.post('/api/admin/corrections/{request_id}')
def review_request(request_id: UUID, body: Review, request: Request):
    reviewer = admin_guard(request)
    with pool.connection() as connection, connection.transaction():
        record = connection.execute('SELECT * FROM records.correction_requests WHERE id=%s FOR UPDATE', (request_id,)).fetchone()
        if not record or record['status'] != 'pending':
            raise HTTPException(409, 'Request was already reviewed or is unavailable')
        if body.decision == 'approve':
            row = connection.execute("""UPDATE records.inmates SET visibility='suppressed',version=version+1
                WHERE id=%s RETURNING id,version""", (record['booking_id'],)).fetchone()
            connection.execute('''INSERT INTO records.search_outbox(inmate_id,version) VALUES (%s,%s)
                ON CONFLICT(inmate_id) DO UPDATE SET version=EXCLUDED.version,queued_at=now()''', (row['id'], row['version']))
        connection.execute('''UPDATE records.correction_requests SET status=%s,reviewed_at=now(),
            reviewer=%s,review_note=%s WHERE id=%s''',
            ('approved' if body.decision == 'approve' else 'rejected', reviewer, body.note, request_id))
    return {'message': 'Review saved. Approved records are withheld pending source verification.'}

# --- Paid name-removal requests ($99 one-time Stripe checkout) ---
# Model mirrors Montana Blotter's paid privacy flow: payment never auto-applies
# suppression. A paid request is marked 'paid' and still requires an admin
# review (the existing /api/admin/corrections/{id} approve path) before the
# record's visibility flips to 'suppressed'.
import stripe

REMOVAL_FEE_LABEL = '$99'

@app.post('/api/name-removal/checkout', status_code=303)
def name_removal_checkout(request: Request):
    guard(request, limit=5)
    secret = os.environ.get('STRIPE_SECRET_KEY', '')
    price_id = os.environ.get('STRIPE_REMOVAL_PRICE_ID', '')
    if not secret or not price_id:
        raise HTTPException(503, 'Payments are not configured')
    try:
        stripe.api_key = secret
        origin = str(request.headers.get('origin') or os.environ.get('APP_ORIGIN', 'https://jailmap.com')).rstrip('/')
        session = stripe.checkout.Session.create(
            mode='payment',
            line_items=[{'price': price_id, 'quantity': 1}],
            success_url=f'{origin}/name-removal/success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{origin}/name-removal?canceled=1',
        )
    except stripe.StripeError:
        raise HTTPException(502, 'Payment provider unavailable')
    return {'checkout_url': session.url}

@app.get('/api/name-removal/session/{session_id}')
def name_removal_session(session_id: str, request: Request):
    guard(request, limit=20)
    secret = os.environ.get('STRIPE_SECRET_KEY', '')
    if not secret:
        raise HTTPException(503, 'Payments are not configured')
    if not session_id.startswith('cs_') or len(session_id) > 300 or not session_id.replace('_', '').isalnum():
        raise HTTPException(422, 'Invalid session id')
    try:
        stripe.api_key = secret
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.StripeError:
        raise HTTPException(404, 'Session not found')
    return {'payment_status': session.payment_status, 'amount_total': session.amount_total,
            'currency': session.currency}
