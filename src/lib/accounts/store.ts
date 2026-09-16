import { DatabaseSync } from 'node:sqlite'
import { mkdirSync } from 'node:fs'
import { dirname, isAbsolute, resolve } from 'node:path'
import { createHash, randomBytes, randomUUID, scrypt, timingSafeEqual } from 'node:crypto'

export type Account = { id: string; email: string; name: string; role: 'member' | 'admin'; status: 'active' | 'suspended'; created_at: number }
type Credential = Account & { password_hash: string }
export type SavedSearch = { id: string; label: string; name: string; state: string; county: string; created_at: number }
export class AccountError extends Error {
  status: number
  constructor(message: string, status = 400) { super(message); this.status = status }
}
let connection: DatabaseSync | undefined
export function database() {
  if (connection) return connection
  const path = process.env.AUTH_DATABASE_PATH || resolve('.data/accounts.sqlite')
  if (process.env.NODE_ENV === 'production' && (!process.env.AUTH_DATABASE_PATH || !isAbsolute(path) || process.env.AUTH_SINGLE_INSTANCE !== 'true')) {
    throw new Error('Configure absolute AUTH_DATABASE_PATH and AUTH_SINGLE_INSTANCE=true on a persistent single-host deployment')
  }
  mkdirSync(dirname(path), { recursive: true, mode: 0o700 })
  connection = new DatabaseSync(path)
  connection.exec(`PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON; PRAGMA busy_timeout=5000;
    CREATE TABLE IF NOT EXISTS accounts (
      id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
      password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'member' CHECK(role IN ('member','admin')),
      status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','suspended')), created_at INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS sessions (
      token_hash TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
      created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL);
    CREATE INDEX IF NOT EXISTS session_user ON sessions(account_id);
    CREATE TABLE IF NOT EXISTS saved_searches (
      id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
      label TEXT NOT NULL, name TEXT NOT NULL, state TEXT NOT NULL, county TEXT NOT NULL, created_at INTEGER NOT NULL);
    CREATE INDEX IF NOT EXISTS search_user ON saved_searches(account_id);
    CREATE TABLE IF NOT EXISTS rate_limits (key TEXT PRIMARY KEY, count INTEGER NOT NULL, expires_at INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS account_audit (
      id TEXT PRIMARY KEY, actor_id TEXT, action TEXT NOT NULL, target_id TEXT, created_at INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS password_resets (
      id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
      token_hash TEXT NOT NULL UNIQUE, created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL, used_at INTEGER);
  `)
  return connection
}
const now = () => Math.floor(Date.now() / 1000)
const digest = (value: string) => createHash('sha256').update(value).digest('hex')
const publicColumns = 'id,email,name,role,status,created_at'
function transaction<T>(operation: () => T): T {
  const db = database(); db.exec('BEGIN IMMEDIATE')
  try { const result = operation(); db.exec('COMMIT'); return result } catch (error) { db.exec('ROLLBACK'); throw error }
}
function audit(actor: string | null, action: string, target: string | null) {
  database().prepare('INSERT INTO account_audit VALUES (?,?,?,?,?)').run(randomUUID(), actor, action, target, now())
}
export function rateLimit(key: string, limit: number, seconds = 900) {
  const db = database()
  db.prepare('DELETE FROM rate_limits WHERE expires_at<=?').run(now())
  const row = db.prepare(`INSERT INTO rate_limits VALUES (?,1,?) ON CONFLICT(key) DO UPDATE SET count=count+1 RETURNING count`).get(digest(key), now() + seconds)
  if (Number(row?.count) > limit) throw new AccountError('Too many attempts. Please try again in 15 minutes.', 429)
}
export function emailValue(input: unknown) {
  if (typeof input !== 'string' || input.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.trim())) throw new AccountError('Enter a valid email address.')
  return input.trim().toLowerCase()
}
export function textValue(input: unknown, label: string, min = 1, max = 100) {
  if (typeof input !== 'string' || input.trim().length < min || input.trim().length > max) throw new AccountError(`${label} must be ${min}–${max} characters.`)
  return input.trim()
}
function passwordValue(input: unknown): string {
  if (typeof input !== 'string' || input.length < 15 || input.length > 128) throw new AccountError('Use a password or passphrase of 15–128 characters.')
  return input
}
let hashing = 0
async function derive(password: string, salt: string) {
  if (hashing >= 2) throw new AccountError('Sign-in service is busy. Please try again shortly.', 503)
  hashing++
  try { return await new Promise<Buffer>((resolve, reject) => scrypt(password, salt, 64, { N: 131072, r: 8, p: 1, maxmem: 256 * 1024 * 1024 }, (error, key) => error ? reject(error) : resolve(key))) }
  finally { hashing-- }
}
export async function hashPassword(password: string) {
  const salt = randomBytes(16).toString('hex')
  return `scrypt-v1$${salt}$${(await derive(password, salt)).toString('hex')}`
}
async function verifyPassword(password: string, stored: string) {
  const [version, salt, hash] = stored.split('$')
  if (version !== 'scrypt-v1' || !salt || !hash) return false
  const derived = await derive(password, salt)
  const expected = Buffer.from(hash, 'hex')
  return expected.length === derived.length && timingSafeEqual(expected, derived)
}
const dummyHash = `scrypt-v1$00000000000000000000000000000000$${'00'.repeat(64)}`
export async function register(input: Record<string, unknown>) {
  const email = emailValue(input.email), name = textValue(input.name, 'Name', 2, 80)
  const password = passwordValue(input.password)
  if (input.accepted !== true) throw new AccountError('Please accept the responsible-use terms.')
  // Hash even for duplicate addresses; no stored credential or role is accepted from clients.
  const hash = await hashPassword(password)
  return transaction(() => {
    if (database().prepare('SELECT id FROM accounts WHERE email=?').get(email)) throw new AccountError('Unable to create this account. Try signing in or use another email.', 409)
    const id = randomUUID()
    database().prepare('INSERT INTO accounts(id,email,name,password_hash,created_at) VALUES (?,?,?,?,?)').run(id, email, name, hash, now())
    audit(id, 'account.registered', id)
    return id
  })
}
export async function login(input: Record<string, unknown>) {
  const email = emailValue(input.email)
  const password = typeof input.password === 'string' && input.password.length <= 128 ? input.password : ''
  const row = database().prepare('SELECT * FROM accounts WHERE email=?').get(email) as Credential | undefined
  const valid = await verifyPassword(password, row?.password_hash || dummyHash)
  if (!valid || !row || row.status !== 'active') throw new AccountError('Email or password is incorrect.', 401)
  const current = database().prepare('SELECT password_hash,status FROM accounts WHERE id=?').get(row.id)
  if (current?.password_hash !== row.password_hash || current?.status !== 'active') throw new AccountError('Please sign in again.', 401)
  audit(row.id, 'account.login', row.id)
  return row.id
}
export function createSession(id: string) {
  const token = randomBytes(32).toString('hex')
  const db = database()
  db.prepare('DELETE FROM sessions WHERE expires_at<=?').run(now())
  const user = db.prepare('SELECT status FROM accounts WHERE id=?').get(id)
  if (user?.status !== 'active') throw new AccountError('Account unavailable.', 401)
  db.prepare('INSERT INTO sessions VALUES (?,?,?,?)').run(digest(token), id, now(), now() + 60 * 60 * 24 * 7)
  // Bound active sessions to the ten newest tokens per account.
  db.prepare('DELETE FROM sessions WHERE account_id=? AND token_hash NOT IN (SELECT token_hash FROM sessions WHERE account_id=? ORDER BY created_at DESC,rowid DESC LIMIT 10)').run(id, id)
  return token
}
export function getSession(token?: string): Account | null {
  if (!token || !/^[a-f0-9]{64}$/.test(token)) return null
  const row = database().prepare(`SELECT ${publicColumns.split(',').map(c => `a.${c}`).join(',')} FROM accounts a JOIN sessions s ON a.id=s.account_id WHERE s.token_hash=? AND s.expires_at>? AND a.status='active'`).get(digest(token), now()) as Account | undefined
  return row ? { ...row } : null
}
export function logout(token?: string) {
  if (token) database().prepare('DELETE FROM sessions WHERE token_hash=?').run(digest(token))
}
export function getDashboard(id: string) {
  return {
    searches: database().prepare('SELECT id,label,name,state,county,created_at FROM saved_searches WHERE account_id=? ORDER BY created_at DESC').all(id).map(row => ({ ...row })) as SavedSearch[],
    sessions: Number(database().prepare('SELECT count(*) AS n FROM sessions WHERE account_id=? AND expires_at>?').get(id, now())?.n),
  }
}
export function updateProfile(id: string, input: Record<string, unknown>) {
  database().prepare('UPDATE accounts SET name=? WHERE id=?').run(textValue(input.name, 'Name', 2, 80), id)
}
export async function changePassword(id: string, input: Record<string, unknown>) {
  const password = passwordValue(input.password)
  const currentPassword = typeof input.currentPassword === 'string' && input.currentPassword.length <= 128 ? input.currentPassword : ''
  const row = database().prepare('SELECT password_hash FROM accounts WHERE id=?').get(id)
  if (!row || !await verifyPassword(currentPassword, String(row.password_hash))) throw new AccountError('Current password is incorrect.', 400)
  const hash = await hashPassword(password)
  transaction(() => {
    const updated = database().prepare("UPDATE accounts SET password_hash=? WHERE id=? AND password_hash=? AND status='active'").run(hash, id, String(row.password_hash))
    if (!updated.changes) throw new AccountError('Account changed. Please sign in again.', 401)
    database().prepare('DELETE FROM sessions WHERE account_id=?').run(id)
    audit(id, 'password.changed', id)
  })
}
export function revokeOtherSessions(id: string, token: string) {
  database().prepare('DELETE FROM sessions WHERE account_id=? AND token_hash!=?').run(id, digest(token))
  audit(id, 'sessions.revoked', id)
}
export function saveSearch(id: string, input: Record<string, unknown>) {
  const label = textValue(input.label, 'Label', 2, 80), name = textValue(input.name, 'Search name', 2, 100)
  const state = typeof input.state === 'string' ? input.state.toUpperCase() : ''
  const county = typeof input.county === 'string' ? input.county.trim() : ''
  if ((state && !/^[A-Z]{2}$/.test(state)) || county.length > 100) throw new AccountError('Invalid state or county.')
  transaction(() => {
    const count = Number(database().prepare('SELECT count(*) AS n FROM saved_searches WHERE account_id=?').get(id)?.n)
    if (count >= 25) throw new AccountError('You can save up to 25 searches. Remove one to add another.')
    database().prepare('INSERT INTO saved_searches VALUES (?,?,?,?,?,?,?)').run(randomUUID(), id, label, name, state, county, now())
  })
}
export function deleteSearch(accountId: string, id: string) {
  const result = database().prepare('DELETE FROM saved_searches WHERE id=? AND account_id=?').run(id, accountId)
  if (!result.changes) throw new AccountError('Saved search not found.', 404)
}
export function adminOverview(page = 1) {
  const db = database()
  return {
    total: Number(db.prepare('SELECT count(*) AS n FROM accounts').get()?.n),
    active: Number(db.prepare("SELECT count(*) AS n FROM accounts WHERE status='active'").get()?.n),
    admins: Number(db.prepare("SELECT count(*) AS n FROM accounts WHERE role='admin' AND status='active'").get()?.n),
    searches: Number(db.prepare('SELECT count(*) AS n FROM saved_searches').get()?.n),
    users: db.prepare(`SELECT ${publicColumns} FROM accounts ORDER BY created_at DESC,id LIMIT 25 OFFSET ?`).all((page - 1) * 25).map(row => ({ ...row })) as Account[],
    audit: db.prepare('SELECT id,actor_id,action,target_id,created_at FROM account_audit ORDER BY created_at DESC,rowid DESC LIMIT 20').all().map(row => ({ ...row })), page,
  }
}
export function updateAccount(actor: string, target: string, input: Record<string, unknown>) {
  if (actor === target) throw new AccountError('You cannot change your own access here.')
  if (!['member', 'admin'].includes(String(input.role)) || !['active', 'suspended'].includes(String(input.status))) throw new AccountError('Invalid role or status.')
  transaction(() => {
    const admin = database().prepare("SELECT id FROM accounts WHERE id=? AND role='admin' AND status='active'").get(actor)
    if (!admin) throw new AccountError('Administrator access required.', 403)
    if (!database().prepare('UPDATE accounts SET role=?,status=? WHERE id=?').run(String(input.role), String(input.status), target).changes) throw new AccountError('Account not found.', 404)
    database().prepare('DELETE FROM sessions WHERE account_id=?').run(target)
    audit(actor, `access.${input.role}.${input.status}`, target)
  })
}
export function promoteAdmin(email: string) {
  transaction(() => {
    const account = database().prepare('SELECT id FROM accounts WHERE email=?').get(emailValue(email))
    if (!account) throw new AccountError('Register this account first.')
    database().prepare("UPDATE accounts SET role='admin',status='active' WHERE id=?").run(String(account.id))
    database().prepare('DELETE FROM sessions WHERE account_id=?').run(String(account.id))
    audit(null, 'operator.promoted-admin', String(account.id))
  })
}

const RESET_TOKEN_TTL = 60 * 60 // one hour
export function requestPasswordReset(email: string): string | null {
  const normalized = emailValue(email)
  return transaction(() => {
    const account = database().prepare('SELECT id FROM accounts WHERE email=?').get(normalized)
    if (!account) return null
    const token = randomBytes(32).toString('hex')
    database().prepare('DELETE FROM password_resets WHERE account_id=?').run(String(account.id))
    database().prepare('INSERT INTO password_resets (id,account_id,token_hash,created_at,expires_at) VALUES (?,?,?,?,?)')
      .run(randomUUID(), String(account.id), digest(token), now(), now() + RESET_TOKEN_TTL)
    return token
  })
}
export async function resetPassword(token: string, password: string) {
  if (!/^[a-f0-9]{64}$/.test(token)) throw new AccountError('This reset link is invalid or expired. Please request a new one.', 400)
  const hash = await hashPassword(password)
  transaction(() => {
    const row = database().prepare('SELECT account_id, expires_at, used_at FROM password_resets WHERE token_hash=?').get(digest(token)) as { account_id: string; expires_at: number; used_at: number | null } | undefined
    if (!row || row.used_at || Number(row.expires_at) < now()) throw new AccountError('This reset link is invalid or expired. Please request a new one.', 400)
    const account = database().prepare("SELECT id FROM accounts WHERE id=? AND status='active'").get(row.account_id)
    if (!account) throw new AccountError('This reset link is invalid or expired. Please request a new one.', 400)
    database().prepare('UPDATE accounts SET password_hash=? WHERE id=?').run(hash, row.account_id)
    database().prepare('UPDATE password_resets SET used_at=? WHERE token_hash=?').run(now(), digest(token))
    database().prepare('DELETE FROM sessions WHERE account_id=?').run(row.account_id)
    database().prepare('DELETE FROM password_resets WHERE account_id=? AND token_hash!=?').run(row.account_id, digest(token))
    audit(row.account_id, 'password.reset', row.account_id)
  })
}
