import { cookies } from 'next/headers'
import { AccountError, rateLimit } from '@/lib/accounts/store'
import { createRouteChallenge, routeCheckCookie, routeClient, solveRouteChallenge } from '@/lib/search/route-check'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

function response(data: unknown, status = 200) {
  return Response.json(data, { status, headers: { 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex, noarchive' } })
}

async function body(request: Request) {
  if (!request.headers.get('content-type')?.startsWith('application/json')) throw new AccountError('JSON required.', 415)
  const reader = request.body?.getReader(); const chunks: Uint8Array[] = []; let size = 0
  if (reader) while (true) { const { value, done } = await reader.read(); if (done) break; size += value.length; if (size > 2048) { await reader.cancel(); throw new AccountError('Request too large.', 413) } chunks.push(value) }
  try { const parsed = JSON.parse(Buffer.concat(chunks).toString('utf8')); if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') throw new Error(); return parsed as Record<string, unknown> }
  catch { throw new AccountError('Invalid request.') }
}

export async function GET(request: Request) {
  try {
    const client = routeClient(request.headers)
    rateLimit(`route-check-create:${client}`, 30, 3600)
    return response(createRouteChallenge(client))
  } catch (error) {
    if (error instanceof AccountError) return response({ error: error.message }, error.status)
    console.error('Seal Check creation failed:', error instanceof Error ? error.name : 'UnknownError')
    return response({ error: 'Seal Check is temporarily unavailable.' }, 503)
  }
}

export async function POST(request: Request) {
  try {
    const origin = process.env.APP_ORIGIN || new URL(request.url).origin
    if (request.headers.get('origin') !== origin) throw new AccountError('Request origin is not allowed.', 403)
    const client = routeClient(request.headers)
    rateLimit(`route-check-solve:${client}`, 12, 15 * 60)
    const input = await body(request)
    const permit = solveRouteChallenge(input.id, input.answer, client)
    if (!permit) return response({ error: 'That mark did not match. Try a new seal.' }, 400)
    const jar = await cookies()
    jar.set(routeCheckCookie, permit, { httpOnly: true, secure: process.env.NODE_ENV === 'production', sameSite: 'strict', path: '/', maxAge: 15 * 60 })
    return response({ ok: true })
  } catch (error) {
    if (error instanceof AccountError) return response({ error: error.message }, error.status)
    console.error('Seal Check verification failed:', error instanceof Error ? error.name : 'UnknownError')
    return response({ error: 'Seal Check is temporarily unavailable.' }, 503)
  }
}
