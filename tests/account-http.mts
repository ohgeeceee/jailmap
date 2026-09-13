// Local integration test. Creates uniquely named synthetic accounts and removes
// only those account IDs in finally. Run against a development instance.
import assert from 'node:assert/strict'
import { randomUUID } from 'node:crypto'
import { database, promoteAdmin } from '../src/lib/accounts/store.ts'
const base = process.env.ACCOUNT_TEST_BASE || 'http://127.0.0.1:3107'
const allowedOrigin = process.env.ACCOUNT_TEST_ORIGIN || base
assert.equal(new URL(base).hostname, '127.0.0.1', 'Test runner is local-only')
const ids: string[] = [], suffix = randomUUID(), password = 'Synthetic test passphrase only 2026!'
async function request(path: string, method = 'GET', data?: unknown, cookie = '', origin = allowedOrigin) {
  const response = await fetch(base + path, { method, headers: { origin, cookie, 'content-type': 'application/json' }, body: data ? JSON.stringify(data) : undefined, redirect: 'manual' })
  const text = await response.text()
  let body: Record<string, unknown> = {}; try { body = JSON.parse(text) } catch { /* Page/redirect */ }
  return { response, body, cookie: response.headers.get('set-cookie')?.split(';')[0] || '' }
}
try {
  assert.equal((await request('/dashboard')).response.status, 307)
  assert.equal((await request('/api/account/me')).response.status, 401)
  assert.equal((await request('/api/account/login', 'POST', {}, '', 'https://other.example')).response.status, 403)
  const email = `member-${suffix}@example.test`
  const registered = await request('/api/account/register', 'POST', { name: 'Synthetic Member', email, password, accepted: true, role: 'admin' })
  assert.equal(registered.response.status, 201)
  const user = registered.body.user as { id: string; role: string }; ids.push(user.id)
  assert.equal(user.role, 'member'); assert.match(registered.response.headers.get('set-cookie') || '', /HttpOnly/i)
  if (process.env.NODE_ENV === 'production') {
    assert.match(registered.cookie, /^__Host-jailmap_session=/)
    assert.match(registered.response.headers.get('set-cookie') || '', /Secure/i)
  }
  const cookie = registered.cookie
  assert.equal((await request('/dashboard', 'GET', undefined, cookie)).response.status, 200)
  assert.equal((await request('/api/account/admin/overview', 'GET', undefined, cookie)).response.status, 403)
  assert.equal((await request('/api/admin/records/overview', 'GET', undefined, cookie)).response.status, 403)
  assert.equal((await request('/api/account/searches', 'POST', { label: 'Test search', name: 'Example', state: 'MT', county: '' }, cookie)).response.status, 201)
  const me = await request('/api/account/me', 'GET', undefined, cookie)
  assert.equal((me.body.searches as unknown[]).length, 1)
  assert.equal((await request('/api/account/profile', 'PATCH', { name: 'Updated Test Name' }, cookie)).response.status, 200)
  const adminEmail = `admin-${suffix}@example.test`
  const admin = await request('/api/account/register', 'POST', { name: 'Synthetic Admin', email: adminEmail, password, accepted: true })
  assert.equal(admin.response.status, 201); ids.push((admin.body.user as { id: string }).id)
  promoteAdmin(adminEmail)
  const signedIn = await request('/api/account/login', 'POST', { email: adminEmail, password })
  assert.equal(signedIn.response.status, 200)
  const adminCookie = signedIn.cookie
  assert.equal((await request('/admin', 'GET', undefined, adminCookie)).response.status, 200)
  assert.equal((await request('/api/account/admin/overview', 'GET', undefined, adminCookie)).response.status, 200)
  assert.equal((await request(`/api/account/admin/users/${user.id}`, 'PATCH', { role: 'member', status: 'suspended' }, adminCookie)).response.status, 200)
  assert.equal((await request('/api/account/me', 'GET', undefined, cookie)).response.status, 401)
  assert.equal((await request('/api/account/login', 'POST', { email, password })).response.status, 401)
  assert.equal((await request('/api/account/logout', 'POST', undefined, adminCookie)).response.status, 200)
  assert.equal((await request('/api/account/admin/overview', 'GET', undefined, adminCookie)).response.status, 401)
  console.log('HTTP integration passed: registration, cookies, CSRF, protected pages, role checks, saved searches, profile updates, suspension and logout.')
} finally {
  const db = database()
  for (const id of ids) { db.prepare('DELETE FROM account_audit WHERE actor_id=? OR target_id=?').run(id, id); db.prepare('DELETE FROM accounts WHERE id=?').run(id) }
  db.close()
}
