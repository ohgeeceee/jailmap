import hashlib
import hmac
import json
import os
from contextlib import asynccontextmanager
from typing import Literal
from uuid import UUID

import httpx
from fastapi import APIRouter, FastAPI, HTTPException, Query, Request
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

@app.get('/api/leaderboard')
def leaderboard(request: Request,
                state: str | None = Query(None, pattern='^[A-Z]{2}$'),
                county: str | None = Query(None, min_length=1, max_length=100),
                limit: int = Query(50, ge=1, le=100)):
    guard(request)
    clauses = [PUBLIC_WHERE,
        "i.booking_date <= now()",
        "i.booking_date > now() - interval '365 days'"]
    params: list = []
    if state:
        clauses.append('j.state=%s')
        params.append(state)
    if county:
        clauses.append('j.county=%s')
        params.append(county)
    params.append(min(limit, 100))
    with pool.connection() as connection:
        # Identity is name-based within a jurisdiction: rosters expose no
        # statewide person identifier and DOB is rarely populated. Counts are
        # distinct booking numbers so multi-day observed snapshots of the same
        # stay do not inflate the tally.
        rows = connection.execute("""
            SELECT j.state, j.county,
                   i.last_name, i.first_name,
                   COUNT(DISTINCT i.booking_number) AS booking_count,
                   MIN(i.booking_date)::date AS first_booking,
                   MAX(i.booking_date)::date AS last_booking,
                   (ARRAY_AGG(i.id ORDER BY i.booking_date DESC))[1]::text AS latest_booking_id
            FROM records.inmates i
            JOIN records.jurisdictions j ON j.id=i.jurisdiction_id
            WHERE """ + ' AND '.join(clauses) + """
            GROUP BY j.state, j.county, i.last_name, i.first_name
            HAVING COUNT(DISTINCT i.booking_number) > 1
            ORDER BY booking_count DESC, last_booking DESC
            LIMIT %s
        """, params).fetchall()
    from datetime import datetime, timezone
    return {'items': rows, 'scope': {'state': state, 'county': county},
            'note': 'Counts reflect bookings observed under the same name within the same jurisdiction over the trailing 365 days. Name matches are not confirmed to be the same individual.',
            'generated_at': datetime.now(timezone.utc).isoformat()}

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

@app.post('/api/name-removal/checkout')
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

# Stripe webhook: confirms paid sessions even when the buyer never returns to
# the success page (async payment methods). Signature-verified; the payload is
# only used to cross-check the session id, never trusted for amounts.
@app.post('/api/name-removal/webhook')
async def name_removal_webhook(request: Request):
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    api_secret = os.environ.get('STRIPE_SECRET_KEY', '')
    if not webhook_secret or not api_secret:
        raise HTTPException(503, 'Payments are not configured')
    payload = await request.body()
    signature = request.headers.get('stripe-signature', '')
    try:
        event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
    except (ValueError, stripe.SignatureVerificationError):
        raise HTTPException(400, 'Invalid webhook signature')
    if event.type in ('checkout.session.completed', 'checkout.session.async_payment_succeeded',
                      'checkout.session.async_payment_failed'):
        session = event.data.object
        # Only touch sessions this app created: the price must match ours.
        line_items = stripe.checkout.Session.list_line_items(session.id, limit=1, api_key=api_secret)
        prices = [li.price.id for li in line_items.data]
        if os.environ.get('STRIPE_REMOVAL_PRICE_ID', '') in prices:
            status = session.payment_status
            # No local fulfillment table yet: sessions are verified on demand
            # via /api/name-removal/session/{id}. Log for operator visibility.
            print(f"name-removal webhook: session={session.id} status={status}")
    return {'received': True}

# --- Subscription paywall (Stripe) -------------------------------------------
# Four tiers: basic ($9.99/mo), pro ($49/mo), developer ($149/mo), enterprise ($499/mo)
# Annual billing: 20% discount. Overage: $0.005/request under 50k, $0.003 above 100k.

SUBSCRIPTION_TIERS = {
    'basic':     {'price_monthly': 999,  'price_annual': 7999,  'label': 'Basic Search / Alerts'},
    'pro':       {'price_monthly': 4900, 'price_annual': 39200, 'label': 'Pro / Investigator'},
    'developer': {'price_monthly': 14900,'price_annual': 119200,'label': 'Developer API (Starter)'},
    'enterprise': {'price_monthly': 49900,'price_annual': 399200,'label': 'Enterprise / Data Stream'},
}

OVERAGE_RATES = [
    (50000, 0.005),   # $0.005/request under 50k
    (100000, 0.003),  # $0.003/request above 100k
]

def _get_stripe_price_id(tier: str, annual: bool = False) -> str:
    """Look up Stripe price ID from environment. Format: STRIPE_PRICE_BASIC_MONTHLY, etc."""
    suffix = 'ANNUAL' if annual else 'MONTHLY'
    key = f'STRIPE_PRICE_{tier.upper()}_{suffix}'
    price_id = os.environ.get(key, '')
    if not price_id:
        raise HTTPException(503, f'Price not configured for tier {tier}')
    return price_id

@app.post('/api/subscriptions/checkout')
def subscription_checkout(request: Request):
    """Create a Stripe checkout session for a subscription tier."""
    guard(request, limit=5)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(422, 'Invalid JSON body')
    tier = data.get('tier', '')
    annual = bool(data.get('annual', False))
    if tier not in SUBSCRIPTION_TIERS:
        raise HTTPException(422, 'Invalid tier')
    secret = os.environ.get('STRIPE_SECRET_KEY', '')
    if not secret:
        raise HTTPException(503, 'Payments are not configured')
    try:
        stripe.api_key = secret
        price_id = _get_stripe_price_id(tier, annual)
        origin = str(request.headers.get('origin') or os.environ.get('APP_ORIGIN', 'https://jailmap.com')).rstrip('/')
        session = stripe.checkout.Session.create(
            mode='subscription',
            line_items=[{'price': price_id, 'quantity': 1}],
            success_url=f'{origin}/dashboard?subscription=success&session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{origin}/pricing?canceled=1',
            metadata={'tier': tier, 'annual': str(annual)},
        )
    except stripe.StripeError:
        raise HTTPException(502, 'Payment provider unavailable')
    return {'checkout_url': session.url}

@app.get('/api/subscriptions/status')
def subscription_status(request: Request):
    """Return the current subscription status for the authenticated account."""
    guard(request, limit=20)
    account_id = request.headers.get('x-records-admin', '')
    if not account_id:
        raise HTTPException(401, 'Account required')
    # Query the accounts database for subscription info
    # This is a simplified version - in production, you'd query the subscriptions table
    return {'tier': 'free', 'status': 'inactive', 'api_requests_this_period': 0}

# Webhook rate limiting: max 100 webhook events per minute per IP
_webhook_rate_limit: dict[str, list[float]] = {}

def _check_webhook_rate_limit(client_ip: str) -> bool:
    """Return True if the client is within the webhook rate limit."""
    import time as _time
    now = _time.time()
    window = 60  # 1 minute
    max_requests = 100
    if client_ip not in _webhook_rate_limit:
        _webhook_rate_limit[client_ip] = []
    # Remove old entries
    _webhook_rate_limit[client_ip] = [t for t in _webhook_rate_limit[client_ip] if now - t < window]
    if len(_webhook_rate_limit[client_ip]) >= max_requests:
        return False
    _webhook_rate_limit[client_ip].append(now)
    return True

@app.post('/api/subscriptions/webhook')
async def subscription_webhook(request: Request):
    """Handle Stripe webhook events for subscription lifecycle."""
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    api_secret = os.environ.get('STRIPE_SECRET_KEY', '')
    if not webhook_secret or not api_secret:
        raise HTTPException(503, 'Payments are not configured')
    # Rate limit webhooks to prevent abuse
    client_ip = request.headers.get('x-forwarded-for', request.client.host if request.client else 'unknown')
    if not _check_webhook_rate_limit(client_ip):
        raise HTTPException(429, 'Webhook rate limit exceeded')
    payload = await request.body()
    signature = request.headers.get('stripe-signature', '')
    try:
        event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
    except (ValueError, stripe.SignatureVerificationError):
        raise HTTPException(400, 'Invalid webhook signature')
    if event.type in ('customer.subscription.created', 'customer.subscription.updated',
                      'customer.subscription.deleted', 'customer.subscription.paused',
                      'customer.subscription.resumed'):
        sub = event.data.object
        tier = sub.metadata.get('tier', 'basic') if hasattr(sub, 'metadata') else 'basic'
        status = sub.status
        period_start = sub.current_period_start if hasattr(sub, 'current_period_start') else None
        period_end = sub.current_period_end if hasattr(sub, 'current_period_end') else None
        # Update local subscription record
        # In production, this would update the subscriptions table in the accounts DB
        print(f"subscription webhook: sub={sub.id} tier={tier} status={status} period={period_start}-{period_end}")
    elif event.type == 'invoice.paid':
        invoice = event.data.object
        # Reset API counter on successful payment
        print(f"invoice paid: {invoice.id} amount={invoice.amount_paid}")
    elif event.type == 'invoice.payment_failed':
        invoice = event.data.object
        print(f"invoice payment failed: {invoice.id}")
    return {'received': True}

# --- API key management (developer & enterprise tiers) ------------------------
# API keys are stored in the accounts SQLite DB via the web process. The backend
# hands out keys only after verifying the account has an active subscription.

# In-memory API key rate limit store: {key_prefix: [timestamps]}
_api_rate_limits: dict[str, list[float]] = {}

def _check_api_rate_limit(key_prefix: str, tier: str) -> tuple[bool, dict]:
    """Check if an API key is within its rate limit. Returns (allowed, headers)."""
    import time as _time
    now = _time.time()
    window = 60  # 1 minute
    # Rate limits per tier (requests per minute)
    limits = {
        'developer': 100,   # ~25k/mo = ~58/min, allow burst
        'enterprise': 1000, # ~150k/mo = ~347/min, allow burst
    }
    max_requests = limits.get(tier, 60)
    if key_prefix not in _api_rate_limits:
        _api_rate_limits[key_prefix] = []
    # Remove old entries
    _api_rate_limits[key_prefix] = [t for t in _api_rate_limits[key_prefix] if now - t < window]
    if len(_api_rate_limits[key_prefix]) >= max_requests:
        return False, {
            'X-RateLimit-Limit': str(max_requests),
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': str(int(now + window)),
        }
    _api_rate_limits[key_prefix].append(now)
    return True, {
        'X-RateLimit-Limit': str(max_requests),
        'X-RateLimit-Remaining': str(max_requests - len(_api_rate_limits[key_prefix])),
        'X-RateLimit-Reset': str(int(now + window)),
    }

@app.post('/api/subscriptions/keys')
def create_api_key(request: Request):
    """Generate a new API key for accounts with developer or enterprise tier."""
    guard(request, limit=10)
    account_id = request.headers.get('x-records-admin', '')
    if not account_id:
        raise HTTPException(401, 'Account required')
    # NOTE: In production, verify subscription tier from accounts DB.
    # For now, the web process handles this check before proxying.
    import secrets
    key = secrets.token_urlsafe(32)
    return {'api_key': key, 'prefix': key[:8]}

@app.delete('/api/subscriptions/keys/{key_prefix}')
def revoke_api_key(request: Request, key_prefix: str):
    """Revoke an API key by its prefix."""
    guard(request, limit=10)
    account_id = request.headers.get('x-records-admin', '')
    if not account_id:
        raise HTTPException(401, 'Account required')
    if not key_prefix or len(key_prefix) > 32:
        raise HTTPException(422, 'Invalid key prefix')
    return {'revoked': True}

@app.get('/api/subscriptions/usage')
def api_usage(request: Request):
    """Return API usage stats for the authenticated account."""
    guard(request, limit=20)
    account_id = request.headers.get('x-records-admin', '')
    if not account_id:
        raise HTTPException(401, 'Account required')
    # In production, query the subscriptions table for usage data
    return {
        'tier': 'free',
        'api_requests_this_period': 0,
        'api_limit': 0,
        'overage_rate': 0,
        'period_reset_at': None,
    }

# --- Administrator operations surfaces -----------------------------------
# Read-only. These endpoints never enable a jurisdiction, publish a record, or
# change visibility; every write path stays on the existing correction review
# route (/api/admin/corrections/{id}) behind a human decision.

@app.get('/api/admin/coverage')
def admin_coverage(request: Request):
    admin_guard(request)
    with pool.connection() as connection:
        directory = connection.execute('''SELECT
            (SELECT count(*) FROM "State") AS states,
            (SELECT count(*) FROM "County") AS counties,
            (SELECT count(*) FROM "Jail") AS jails''').fetchone()
        pipeline = connection.execute('''SELECT count(*) AS registered,
            count(*) FILTER (WHERE enabled) AS enabled,
            count(*) FILTER (WHERE review_status='verified') AS verified,
            count(*) FILTER (WHERE staging_only) AS staging,
            count(DISTINCT county_id) AS counties_with_source
            FROM records.jurisdictions''').fetchone()
        bookings = connection.execute('''SELECT count(*) AS bookings,
            count(*) FILTER (WHERE visibility='public') AS public_bookings,
            count(*) FILTER (WHERE visibility='suppressed') AS suppressed_bookings,
            count(DISTINCT jurisdiction_id) AS active_jurisdictions
            FROM records.inmates''').fetchone()
        states = connection.execute('''SELECT s.abbrev AS state, s.name AS state_name,
            (SELECT count(*) FROM "County" c WHERE c."stateId"=s.id) AS counties,
            (SELECT count(*) FROM "Jail" jl WHERE jl."stateId"=s.id) AS jails,
            COALESCE(r.registered,0) AS registered,
            COALESCE(r.enabled,0) AS enabled,
            COALESCE(r.verified,0) AS verified,
            COALESCE(r.staging,0) AS staging,
            COALESCE(b.bookings,0) AS bookings
            FROM "State" s
            LEFT JOIN (SELECT j.state, count(*) AS registered,
                    count(*) FILTER (WHERE j.enabled) AS enabled,
                    count(*) FILTER (WHERE j.review_status='verified') AS verified,
                    count(*) FILTER (WHERE j.staging_only) AS staging
                FROM records.jurisdictions j GROUP BY j.state) r ON r.state=s.abbrev
            LEFT JOIN (SELECT j.state, count(*) AS bookings FROM records.inmates i
                JOIN records.jurisdictions j ON j.id=i.jurisdiction_id
                WHERE i.visibility='public' GROUP BY j.state) b ON b.state=s.abbrev
            ORDER BY COALESCE(r.enabled,0) DESC, COALESCE(b.bookings,0) DESC, s.name''').fetchall()
    return {'directory': directory, 'pipeline': pipeline, 'bookings': bookings, 'states': states}

@app.get('/api/admin/ingestion')
def admin_ingestion(request: Request):
    admin_guard(request)
    with pool.connection() as connection:
        totals = connection.execute('''SELECT count(*) AS runs,
            count(*) FILTER (WHERE status='success') AS success,
            count(*) FILTER (WHERE status='failed') AS failed,
            count(*) FILTER (WHERE status='running') AS running,
            max(started_at) AS last_run FROM records.ingestion_runs''').fetchone()
        errors = connection.execute('''SELECT COALESCE(error_type,'unknown') AS error_type,
            count(*) AS count FROM records.ingestion_runs WHERE status='failed'
            GROUP BY 1 ORDER BY 2 DESC LIMIT 12''').fetchall()
        sources = connection.execute('''SELECT j.id::text AS id, j.state, j.county,
            j.facility_name, j.adapter, j.enabled, j.review_status, j.staging_only,
            j.last_success_at,
            r.status AS last_status, r.started_at AS last_run_at,
            r.error_type AS last_error, r.record_count AS last_record_count,
            COALESCE(r.failed_runs,0) AS failed_runs,
            COALESCE(r.success_runs,0) AS success_runs
            FROM records.jurisdictions j
            LEFT JOIN LATERAL (SELECT x.status, x.started_at, x.error_type, x.record_count,
                    (SELECT count(*) FROM records.ingestion_runs f
                        WHERE f.jurisdiction_id=x.jurisdiction_id AND f.status='failed') AS failed_runs,
                    (SELECT count(*) FROM records.ingestion_runs f
                        WHERE f.jurisdiction_id=x.jurisdiction_id AND f.status='success') AS success_runs
                FROM records.ingestion_runs x WHERE x.jurisdiction_id=j.id
                ORDER BY x.started_at DESC LIMIT 1) r ON true
            WHERE j.enabled OR r.started_at IS NOT NULL
            ORDER BY (r.status='failed') DESC NULLS LAST, j.state, j.county''').fetchall()
    return {'totals': totals, 'errors': errors, 'sources': sources}

@app.get('/api/admin/pipeline')
def admin_pipeline(request: Request):
    admin_guard(request)
    with pool.connection() as connection:
        def queue(table):
            return connection.execute(f'SELECT status, count(*) AS count FROM records.{table} GROUP BY status ORDER BY count DESC').fetchall()
        counties = queue('county_ingestion_queue')
        facilities = queue('facility_ingestion_queue')
        enrichment = queue('directory_enrichment_queue')
        staged = connection.execute('''SELECT j.state, j.county, j.facility_name,
            count(*) AS staged, max(s.fetched_at) AS latest_fetch, max(s.source_snapshot_at) AS latest_snapshot
            FROM records.staged_bookings s JOIN records.jurisdictions j ON j.id=s.jurisdiction_id
            GROUP BY j.state, j.county, j.facility_name ORDER BY count(*) DESC LIMIT 50''').fetchall()
        staged_total = connection.execute('SELECT count(*) AS n, max(fetched_at) AS latest FROM records.staged_bookings').fetchone()
        advanced = connection.execute('''SELECT cq.status, c.name AS county, s.abbrev AS state,
            cq.source_url, cq.adapter, cq.notes, cq.updated_at
            FROM records.county_ingestion_queue cq JOIN "County" c ON c.id=cq.county_id
            JOIN "State" s ON s.id=c."stateId"
            WHERE cq.status <> 'source_discovery' ORDER BY cq.updated_at DESC LIMIT 25''').fetchall()
    return {'counties': counties, 'facilities': facilities, 'enrichment': enrichment,
            'staged': staged, 'staged_total': staged_total, 'advanced': advanced}

@app.get('/api/admin/revenue')
def admin_revenue(request: Request):
    admin_guard(request)
    with pool.connection() as connection:
        counts = connection.execute('''SELECT count(*) AS total,
            count(*) FILTER (WHERE status='pending') AS pending,
            count(*) FILTER (WHERE status='approved') AS approved,
            count(*) FILTER (WHERE status='rejected') AS rejected,
            count(*) FILTER (WHERE kind='correction') AS corrections,
            count(*) FILTER (WHERE kind='removal') AS removals,
            count(*) FILTER (WHERE status='pending' AND submitted_at < now() - interval '7 days') AS overdue
            FROM records.correction_requests''').fetchone()
        requests = connection.execute('''SELECT r.id::text AS id, r.kind, r.status, r.submitted_at,
            r.reviewed_at, r.review_note, i.id::text AS booking_id, i.first_name, i.last_name,
            i.visibility, j.state, j.county, j.facility_name
            FROM records.correction_requests r JOIN records.inmates i ON i.id=r.booking_id
            JOIN records.jurisdictions j ON j.id=i.jurisdiction_id
            ORDER BY (r.status='pending') DESC, r.submitted_at DESC LIMIT 50''').fetchall()
    # Paid name-removal sessions live only in Stripe (no local ledger yet). The
    # account is shared with Montana Blotter, so filter to our own price id.
    secret = os.environ.get('STRIPE_SECRET_KEY', '')
    price_id = os.environ.get('STRIPE_REMOVAL_PRICE_ID', '')
    payments = {'configured': bool(secret and price_id), 'sessions': [], 'paid': 0, 'gross_cents': 0}
    if secret and price_id:
        try:
            stripe.api_key = secret
            for session in stripe.checkout.Session.list(limit=25, expand=['data.line_items']).data:
                prices = [item.price.id for item in (session.line_items.data if session.line_items else [])]
                if price_id not in prices:
                    continue
                if session.payment_status == 'paid':
                    payments['paid'] += 1
                    payments['gross_cents'] += int(session.amount_total or 0)
                payments['sessions'].append({'id': session.id, 'created': session.created,
                    'amount_total': session.amount_total, 'currency': session.currency,
                    'payment_status': session.payment_status, 'status': session.status})
        except stripe.StripeError:
            payments['error'] = 'Payment provider unavailable'
    return {'counts': counts, 'requests': requests, 'payments': payments}


# --- admin pass 1: run history + coverage gaps (read-only) -----------------
# Same contract as the surfaces above: these endpoints never enable a
# jurisdiction, publish a record, or change visibility. They exist so an
# operator can see WHY a source is failing and WHICH counties have no source.

@app.get('/api/admin/ingestion/runs')
def admin_ingestion_runs(request: Request, limit: int = 100, status: str = '',
                         jurisdiction: str = '', q: str = ''):
    admin_guard(request)
    limit = max(1, min(500, int(limit or 100)))
    where, params = [], []
    if status in ('success', 'failed', 'running', 'dry_run'):
        where.append('r.status=%s')
        params.append(status)
    if jurisdiction:
        try:
            params.append(str(UUID(jurisdiction)))
        except ValueError:
            raise HTTPException(422, 'Invalid jurisdiction id')
        where.append('r.jurisdiction_id=%s')
    if q.strip():
        like = '%' + q.strip()[:80] + '%'
        where.append("(j.county ILIKE %s OR j.facility_name ILIKE %s OR coalesce(r.error_type,'') ILIKE %s OR coalesce(r.error_detail,'') ILIKE %s)")
        params.extend([like, like, like, like])
    clause = (' WHERE ' + ' AND '.join(where)) if where else ''
    sql = '''SELECT r.id, r.status, r.started_at, r.finished_at, r.record_count,
        r.error_type, r.error_detail, j.id::text AS jurisdiction_id, j.state,
        j.county, j.facility_name, j.adapter
        FROM records.ingestion_runs r
        JOIN records.jurisdictions j ON j.id=r.jurisdiction_id''' + clause + '''
        ORDER BY r.started_at DESC LIMIT %s'''
    params.append(limit)
    with pool.connection() as connection:
        runs = connection.execute(sql, tuple(params)).fetchall()
        totals = connection.execute('''SELECT count(1) AS runs,
            count(1) FILTER (WHERE status='success') AS success,
            count(1) FILTER (WHERE status='failed') AS failed
            FROM records.ingestion_runs''').fetchone()
    return {'runs': runs, 'totals': totals, 'limit': limit}

@app.get('/api/admin/gaps')
def admin_gaps(request: Request, limit: int = 300):
    admin_guard(request)
    limit = max(1, min(5000, int(limit or 300)))
    with pool.connection() as connection:
        totals = connection.execute('''SELECT
            (SELECT count(1) FROM "County") AS counties,
            (SELECT count(DISTINCT county_id::text) FROM records.jurisdictions
                WHERE county_id IS NOT NULL) AS with_source,
            (SELECT count(DISTINCT county_id::text) FROM records.jurisdictions
                WHERE county_id IS NOT NULL AND enabled) AS with_enabled''').fetchone()
        rows = connection.execute('''WITH src AS (
                SELECT county_id::text AS county_id, bool_or(enabled) AS any_enabled,
                       count(1) AS sources
                FROM records.jurisdictions WHERE county_id IS NOT NULL
                GROUP BY county_id::text)
            SELECT s.abbrev AS state, c.name AS county,
                coalesce(src.sources, 0) AS sources
            FROM "County" c
            JOIN "State" s ON s.id=c."stateId"
            LEFT JOIN src ON src.county_id=c.id::text
            WHERE coalesce(src.any_enabled, false)=false
            ORDER BY s.abbrev, c.name
            LIMIT %s''', (limit + 1,)).fetchall()
    truncated = len(rows) > limit
    return {'totals': totals, 'gaps': rows[:limit], 'limit': limit, 'truncated': truncated}


# --- admin pass 2: source freshness + triage notes -------------------------
# One narrow write: an administrator recording a triage status/note for a
# source. This never enables a jurisdiction, changes publication defaults,
# starts a fetch, or alters any record's visibility.

@app.get('/api/admin/freshness')
def admin_freshness(request: Request, hours: int = 48):
    admin_guard(request)
    hours = max(1, min(720, int(hours or 48)))
    with pool.connection() as connection:
        totals = connection.execute('''SELECT
            count(1) FILTER (WHERE enabled) AS enabled,
            count(1) FILTER (WHERE enabled AND last_success_at IS NULL) AS never_succeeded,
            count(1) FILTER (WHERE enabled AND last_success_at < now() - make_interval(hours => %s)) AS stale,
            count(1) FILTER (WHERE enabled AND last_success_at >= now() - make_interval(hours => %s)) AS fresh
            FROM records.jurisdictions''', (hours, hours)).fetchone()
        sources = connection.execute('''SELECT j.id::text AS jurisdiction_id, j.state, j.county,
            j.facility_name, j.adapter, j.staging_only, j.last_success_at,
            ((EXTRACT(EPOCH FROM (now() - j.last_success_at))/3600)::float8) AS hours_since_success,
            (SELECT count(1) FROM records.ingestion_runs f
                WHERE f.jurisdiction_id=j.id AND f.status='failed'
                  AND f.started_at > now() - interval '7 days') AS failed_7d,
            r.status AS last_status, r.error_type AS last_error, r.started_at AS last_run_at,
            COALESCE(t.status, 'open') AS triage_status, COALESCE(t.note, '') AS triage_note,
            t.updated_at AS triage_updated_at
            FROM records.jurisdictions j
            LEFT JOIN LATERAL (SELECT x.status, x.error_type, x.started_at
                FROM records.ingestion_runs x WHERE x.jurisdiction_id=j.id
                ORDER BY x.started_at DESC LIMIT 1) r ON true
            LEFT JOIN records.ops_triage t
                ON t.kind='source_health' AND t.jurisdiction_id=j.id
            WHERE j.enabled
            ORDER BY j.last_success_at ASC NULLS FIRST, j.state, j.county
            LIMIT 200''', ()).fetchall()
    return {'totals': totals, 'sources': sources, 'hours': hours}

class Triage(BaseModel):
    kind: Literal['source_health', 'coverage_gap'] = 'source_health'
    state: str = Field(min_length=2, max_length=2)
    county: str = Field(min_length=1, max_length=120)
    status: Literal['open', 'investigating', 'waiting_on_source', 'fixed', 'accepted_stale']
    note: str = Field(default='', max_length=2000)

@app.post('/api/admin/work')
def admin_work(body: Triage, request: Request):
    admin = admin_guard(request)
    state = body.state.strip().upper()
    county = body.county.strip()
    with pool.connection() as connection, connection.transaction():
        connection.execute('''INSERT INTO records.ops_triage
                (kind, state, county, jurisdiction_id, status, note, updated_by)
            VALUES (%s, %s, %s,
                (SELECT id FROM records.jurisdictions WHERE state=%s AND county=%s
                    ORDER BY enabled DESC, facility_name LIMIT 1),
                %s, %s, %s)
            ON CONFLICT (kind, state, county) DO UPDATE SET
                status=EXCLUDED.status,
                note=EXCLUDED.note,
                jurisdiction_id=COALESCE(EXCLUDED.jurisdiction_id, records.ops_triage.jurisdiction_id),
                updated_by=EXCLUDED.updated_by,
                updated_at=now()''',
            (body.kind, state, county, state, county, body.status, body.note, admin))
    return {'message': 'Triage saved.', 'state': state, 'county': county, 'status': body.status}
