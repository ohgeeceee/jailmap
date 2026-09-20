import { createHmac, randomBytes, randomUUID, timingSafeEqual } from 'node:crypto'
import { database } from '../accounts/store.ts'

const SEAL_MARKS = [
  { id: 'ring', glyph: '○', label: 'open ring' },
  { id: 'double-ring', glyph: '◎', label: 'double ring' },
  { id: 'diamond', glyph: '◇', label: 'open diamond' },
  { id: 'star', glyph: '✦', label: 'four-point star' },
  { id: 'flower', glyph: '✿', label: 'flower mark' },
  { id: 'waves', glyph: '≋', label: 'three waves' },
  { id: 'square', glyph: '□', label: 'open square' },
  { id: 'cross', glyph: '＋', label: 'plus mark' },
] as const
const PERMIT_SECONDS = 15 * 60

function secret() {
  const value = process.env.ROUTE_CHECK_SECRET || process.env.RECORDS_API_TOKEN
  if (!value || value.length < 32) throw new Error('Route Check secret is not configured')
  return value
}

const hmac = (value: string) => createHmac('sha256', secret()).update(value).digest('hex')
export const routeCheckCookie = process.env.NODE_ENV === 'production' ? '__Host-jailmap_route' : 'jailmap_route'

function ensureTable() {
  const db = database()
  db.exec(`CREATE TABLE IF NOT EXISTS search_challenges (
    id TEXT PRIMARY KEY,
    answer_hash TEXT NOT NULL,
    client_hash TEXT NOT NULL,
    expires_at INTEGER NOT NULL,
    used_at INTEGER
  ); CREATE INDEX IF NOT EXISTS search_challenge_expiry ON search_challenges(expires_at);`)
  return db
}

export function clientHash(value: string) {
  return hmac(`client:${value}`)
}

export function createRouteChallenge(client: string) {
  const db = ensureTable()
  const id = randomUUID()
  const target = SEAL_MARKS[randomBytes(1)[0] % SEAL_MARKS.length]
  const alternatives = SEAL_MARKS.filter(mark => mark.id !== target.id)
  for (let index = alternatives.length - 1; index > 0; index--) {
    const swap = randomBytes(1)[0] % (index + 1)
    ;[alternatives[index], alternatives[swap]] = [alternatives[swap], alternatives[index]]
  }
  const options = [target, ...alternatives.slice(0, 3)]
  for (let index = options.length - 1; index > 0; index--) {
    const swap = randomBytes(1)[0] % (index + 1)
    ;[options[index], options[swap]] = [options[swap], options[index]]
  }
  const expiresAt = Math.floor(Date.now() / 1000) + 5 * 60
  db.prepare('DELETE FROM search_challenges WHERE expires_at<? OR used_at IS NOT NULL').run(Math.floor(Date.now() / 1000) - 3600)
  db.prepare('INSERT INTO search_challenges(id,answer_hash,client_hash,expires_at) VALUES (?,?,?,?)')
    .run(id, hmac(`answer:${id}:${target.id}`), clientHash(client), expiresAt)
  return {
    id,
    target: { glyph: target.glyph, label: target.label },
    options: options.map(mark => ({ id: mark.id, glyph: mark.glyph, label: mark.label })),
    expiresAt,
  }
}

export function solveRouteChallenge(id: unknown, answer: unknown, client: string) {
  if (typeof id !== 'string' || !/^[0-9a-f-]{36}$/i.test(id) || typeof answer !== 'string' || !SEAL_MARKS.some(mark => mark.id === answer)) return null
  const db = ensureTable()
  const row = db.prepare('SELECT answer_hash,client_hash,expires_at,used_at FROM search_challenges WHERE id=?').get(id)
  const now = Math.floor(Date.now() / 1000)
  if (!row || row.used_at || Number(row.expires_at) < now || row.client_hash !== clientHash(client)) return null
  const actual = Buffer.from(hmac(`answer:${id}:${answer}`), 'hex')
  const expected = Buffer.from(String(row.answer_hash), 'hex')
  if (actual.length !== expected.length || !timingSafeEqual(actual, expected)) return null
  const claimed = db.prepare('UPDATE search_challenges SET used_at=? WHERE id=? AND used_at IS NULL AND expires_at>=?').run(now, id, now)
  if (!claimed.changes) return null
  const payload = `${now + PERMIT_SECONDS}.${clientHash(client)}.${randomBytes(12).toString('hex')}`
  return `${payload}.${hmac(`permit:${payload}`)}`
}

export function validRoutePermit(token: string | undefined, client: string) {
  if (!token || token.length > 500) return false
  const parts = token.split('.')
  if (parts.length !== 4 || !/^\d+$/.test(parts[0])) return false
  const payload = parts.slice(0, 3).join('.')
  const actual = Buffer.from(parts[3], 'hex')
  const expected = Buffer.from(hmac(`permit:${payload}`), 'hex')
  return Number(parts[0]) >= Math.floor(Date.now() / 1000) && parts[1] === clientHash(client) && actual.length === expected.length && timingSafeEqual(actual, expected)
}

export function routeClient(headers: Headers) {
  const trusted = process.env.AUTH_TRUSTED_CLIENT_HEADER
  return trusted ? headers.get(trusted) || 'shared' : 'shared'
}
