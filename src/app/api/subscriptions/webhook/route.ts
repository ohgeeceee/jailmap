import { recordsGateway } from '@/lib/records-gateway'
export async function POST(request: Request) {
  const base = process.env.RECORDS_API_URL
  const token = process.env.RECORDS_API_TOKEN
  if (!base || !token || token.length < 32) return Response.json({ detail: 'Records service is not configured' }, { status: 503 })
  const body = await request.text()
  const response = await fetch(new URL('/api/subscriptions/webhook', base), {
    method: 'POST', cache: 'no-store', body,
    headers: { 'content-type': 'application/json', 'x-gateway-token': token,
      'stripe-signature': request.headers.get('stripe-signature') ?? '' },
  })
  return new Response(await response.text(), { status: response.status, headers: { 'content-type': 'application/json' } })
}
