import { recordsGateway } from '@/lib/records-gateway'

export async function POST(request: Request) {
  // Stripe webhooks POST raw bytes with no origin header; pass the body
  // through untouched so signature verification sees identical bytes.
  const base = process.env.RECORDS_API_URL
  const token = process.env.RECORDS_API_TOKEN
  if (!base || !token || token.length < 32) return Response.json({ detail: 'Records service is not configured' }, { status: 503 })
  const body = await request.text()
  const response = await fetch(new URL('/api/name-removal/webhook', base), {
    method: 'POST', cache: 'no-store', body,
    headers: { 'content-type': 'application/json', 'x-gateway-token': token,
      'stripe-signature': request.headers.get('stripe-signature') ?? '' },
  })
  return new Response(await response.text(), { status: response.status, headers: { 'content-type': 'application/json' } })
}
