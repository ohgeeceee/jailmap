import { AccountError, rateLimit } from '@/lib/accounts/store'
import { createSupportTicket } from '@/lib/support/store'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

async function body(request: Request) {
  if (!request.headers.get('content-type')?.startsWith('application/json')) throw new AccountError('JSON required.', 415)
  const reader = request.body?.getReader()
  const chunks: Uint8Array[] = []
  let size = 0
  if (reader) while (true) {
    const { value, done } = await reader.read()
    if (done) break
    size += value.length
    if (size > 8192) { await reader.cancel(); throw new AccountError('Request too large.', 413) }
    chunks.push(value)
  }
  try {
    const parsed = JSON.parse(Buffer.concat(chunks).toString('utf8'))
    if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') throw new Error()
    return parsed as Record<string, unknown>
  } catch { throw new AccountError('Invalid request.') }
}

export async function POST(request: Request) {
  try {
    const origin = process.env.APP_ORIGIN || new URL(request.url).origin
    if (request.headers.get('origin') !== origin) return Response.json({ error: 'Request origin is not allowed.' }, { status: 403 })
    const clientHeader = process.env.AUTH_TRUSTED_CLIENT_HEADER
    const client = clientHeader ? request.headers.get(clientHeader) || 'shared' : 'shared'
    rateLimit(`support:${client}`, 5, 3600)
    createSupportTicket(await body(request))
    return Response.json({ ok: true }, { status: 201, headers: { 'Cache-Control': 'no-store' } })
  } catch (error) {
    if (error instanceof AccountError) return Response.json({ error: error.message }, { status: error.status })
    return Response.json({ error: 'Your message could not be submitted. Please try again.' }, { status: 400 })
  }
}
