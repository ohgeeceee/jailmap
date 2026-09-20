import { cookies } from 'next/headers'
import { AccountError, emailValue, getSession, rateLimit, textValue } from '@/lib/accounts/store'
import { readInbox, sendSupportReply, supportEmailConfigured } from '@/lib/support/mailbox'
import { getSupportTicket, listSupportTickets, setSupportTicketStatus } from '@/lib/support/store'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'
const SESSION_COOKIE = process.env.NODE_ENV === 'production' ? '__Host-jailmap_session' : 'jailmap_session'

async function admin() {
  const token = (await cookies()).get(SESSION_COOKIE)?.value
  const account = getSession(token)
  if (!account) throw new AccountError('Please sign in to continue.', 401)
  if (account.role !== 'admin') throw new AccountError('Administrator access required.', 403)
  return account
}

function json(data: unknown, status = 200) {
  return Response.json(data, { status, headers: { 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex' } })
}

async function body(request: Request) {
  if (!request.headers.get('content-type')?.startsWith('application/json')) throw new AccountError('JSON required.', 415)
  const reader = request.body?.getReader()
  const chunks: Uint8Array[] = []
  let size = 0
  if (reader) while (true) {
    const { value, done } = await reader.read()
    if (done) break
    size += value.length
    if (size > 16384) { await reader.cancel(); throw new AccountError('Request too large.', 413) }
    chunks.push(value)
  }
  try {
    const parsed = JSON.parse(Buffer.concat(chunks).toString('utf8'))
    if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') throw new Error()
    return parsed as Record<string, unknown>
  } catch { throw new AccountError('Invalid request.') }
}

export async function GET(request: Request) {
  try {
    await admin()
    const view = new URL(request.url).searchParams.get('view')
    if (view === 'email') {
      if (!supportEmailConfigured()) return json({ configured: false, messages: [] })
      return json({ configured: true, messages: await readInbox() })
    }
    return json({ tickets: listSupportTickets(new URL(request.url).searchParams.get('status') || undefined) })
  } catch (error) {
    if (error instanceof AccountError) return json({ error: error.message }, error.status)
    console.error('Support inbox read failed:', error instanceof Error ? error.name : 'UnknownError')
    return json({ error: 'The support inbox is temporarily unavailable.' }, 503)
  }
}

export async function POST(request: Request) {
  try {
    const account = await admin()
    const origin = process.env.APP_ORIGIN || new URL(request.url).origin
    if (request.headers.get('origin') !== origin) throw new AccountError('Request origin is not allowed.', 403)
    rateLimit(`support-reply:${account.id}`, 30, 3600)
    const input = await body(request)
    const action = input.action
    if (action === 'status') {
      setSupportTicketStatus(textValue(input.ticketId, 'Ticket ID', 1, 100), input.status)
      return json({ ok: true })
    }
    if (action !== 'reply') throw new AccountError('Invalid action.')
    const ticketId = typeof input.ticketId === 'string' ? input.ticketId : ''
    const ticket = ticketId ? getSupportTicket(ticketId) : undefined
    const to = ticket?.email || emailValue(input.to)
    const subject = textValue(input.subject, 'Subject', 1, 200)
    const message = textValue(input.message, 'Reply', 1, 10000)
    await sendSupportReply({ to, subject, message, inReplyTo: typeof input.inReplyTo === 'string' ? input.inReplyTo : undefined })
    if (ticket && input.closeTicket === true) setSupportTicketStatus(ticket.id, 'closed')
    return json({ ok: true })
  } catch (error) {
    if (error instanceof AccountError) return json({ error: error.message }, error.status)
    console.error('Support reply failed:', error instanceof Error ? error.name : 'UnknownError')
    return json({ error: 'The reply could not be sent.' }, 503)
  }
}
