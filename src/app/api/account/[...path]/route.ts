import { cookies } from 'next/headers'
import { SESSION_COOKIE } from '@/lib/accounts/session'
import { AccountError, adminOverview, changePassword, createSession, deleteSearch, emailValue, getDashboard, getSession, login, logout, rateLimit, register, revokeOtherSessions, saveSearch, updateAccount, updateProfile } from '@/lib/accounts/store'
export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'
const options = { httpOnly: true, secure: process.env.NODE_ENV === 'production', sameSite: 'lax' as const, path: '/', maxAge: 60 * 60 * 24 * 7 }
function json(data: unknown, status = 200) { return Response.json(data, { status, headers: { 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex', ...(status === 429 ? { 'Retry-After': '900' } : {}) } }) }
async function body(request: Request): Promise<Record<string, unknown>> {
  if (!request.headers.get('content-type')?.startsWith('application/json')) throw new AccountError('JSON required.', 415)
  const reader = request.body?.getReader(); const chunks: Uint8Array[] = []; let size = 0
  if (reader) while (true) { const { value, done } = await reader.read(); if (done) break; size += value.length; if (size > 8192) { await reader.cancel(); throw new AccountError('Request too large.', 413) } chunks.push(value) }
  try { const value = JSON.parse(Buffer.concat(chunks).toString('utf8')); if (!value || Array.isArray(value) || typeof value !== 'object') throw new Error(); return value } catch { throw new AccountError('Invalid JSON.') }
}
async function handle(request: Request, context: { params: Promise<{ path: string[] }> }) {
  try {
    const path = (await context.params).path.join('/')
    const method = request.method
    if (method !== 'GET') {
      const origin = process.env.APP_ORIGIN || `${new URL(request.url).protocol}//${request.headers.get('host')}`
      if (process.env.NODE_ENV === 'production' && !process.env.APP_ORIGIN) throw new Error('APP_ORIGIN required')
      if (request.headers.get('origin') !== origin) throw new AccountError('Request origin is not allowed.', 403)
    }
    const jar = await cookies(), token = jar.get(SESSION_COOKIE)?.value
    const account = getSession(token)
    if (method === 'POST' && ['register', 'login'].includes(path)) {
      const trusted = process.env.AUTH_TRUSTED_CLIENT_HEADER
      const client = trusted ? request.headers.get(trusted) || 'shared' : 'shared'
      rateLimit(`auth-client:${client}`, 30)
      const input = await body(request)
      rateLimit(`auth-email:${emailValue(input.email)}`, 10)
      const id = path === 'register' ? await register(input) : await login(input)
      logout(token)
      const nextToken = createSession(id); jar.set(SESSION_COOKIE, nextToken, options)
      return json({ user: getSession(nextToken) }, path === 'register' ? 201 : 200)
    }
    if (method === 'POST' && path === 'logout') { logout(token); jar.set(SESSION_COOKIE, '', { ...options, maxAge: 0 }); return json({ ok: true }) }
    if (!account) throw new AccountError('Please sign in to continue.', 401)
    if (path.startsWith('admin/') && account.role !== 'admin') throw new AccountError('Administrator access required.', 403)
    if (method !== 'GET') rateLimit(`account:${account.id}`, 60)
    if (method === 'GET' && path === 'me') return json({ user: account, ...getDashboard(account.id) })
    if (method === 'PATCH' && path === 'profile') { updateProfile(account.id, await body(request)); return json({ ok: true }) }
    if (method === 'POST' && path === 'password') {
      rateLimit(`password:${account.id}`, 5)
      await changePassword(account.id, await body(request)); jar.set(SESSION_COOKIE, createSession(account.id), options); return json({ ok: true })
    }
    if (method === 'POST' && path === 'sessions/revoke') { revokeOtherSessions(account.id, token!); return json({ ok: true }) }
    if (method === 'POST' && path === 'searches') { saveSearch(account.id, await body(request)); return json({ ok: true }, 201) }
    if (method === 'DELETE' && /^searches\/[^/]+$/.test(path)) { deleteSearch(account.id, path.split('/')[1]); return json({ ok: true }) }
    if (method === 'GET' && path === 'admin/overview') {
      const page = Number(new URL(request.url).searchParams.get('page') || 1)
      if (!Number.isInteger(page) || page < 1 || page > 10000) throw new AccountError('Invalid page.')
      return json(adminOverview(page))
    }
    if (method === 'PATCH' && /^admin\/users\/[^/]+$/.test(path)) { updateAccount(account.id, path.split('/')[2], await body(request)); return json({ ok: true }) }
    throw new AccountError('Endpoint not found.', 404)
  } catch (error) {
    if (error instanceof AccountError) return json({ error: error.message }, error.status)
    // Never log request payloads, passwords, cookies or email addresses.
    console.error('Account service request failed:', error instanceof Error ? error.name : 'UnknownError')
    return json({ error: 'Account service is temporarily unavailable.' }, 503)
  }
}
export { handle as GET, handle as POST, handle as PATCH, handle as DELETE }
