import { test, after } from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve, sep } from 'node:path'

const directory = mkdtempSync(join(tmpdir(), 'jailmap-watchlist-alerts-test-'))
process.env.AUTH_DATABASE_PATH = join(directory, 'accounts.sqlite')
process.env.RECORDS_API_URL = 'https://records.example.test'
process.env.RECORDS_API_TOKEN = 'a'.repeat(40)
process.env.APP_ORIGIN = 'https://jailmap.test'

const store = await import('../src/lib/accounts/store.ts')
const alerts = await import('../src/lib/watchlists/alerts.ts')
const password = 'synthetic-test-passphrase-123'

after(() => {
  store.database().close()
  assert.ok(resolve(directory).startsWith(resolve(tmpdir()) + sep + 'jailmap-watchlist-alerts-test-'))
  rmSync(directory, { recursive: true, force: true })
})

test('watchlist alert runner sends only new matches once', async () => {
  const accountId = await store.register({ name: 'Alert User', email: 'alert@example.test', password, accepted: true })
  store.createSubscription(accountId, 'basic')
  store.saveWatchlist(accountId, { label: 'Example watch', name: 'Example', state: 'MT', county: 'Yellowstone', emailAlerts: true })
  let sent = 0
  const fetchImpl = async (input: string | URL | Request) => {
    assert.match(String(input), /name=Example/)
    return Response.json({ items: [{
      id: 'booking-1',
      first_name: 'Example',
      last_name: 'Person',
      county: 'Yellowstone',
      state: 'MT',
      facility_name: 'Yellowstone County Detention Facility',
    }] })
  }
  const sendEmail: typeof import('../src/lib/accounts/mail.ts').sendWatchlistAlertEmail = async input => {
    sent += 1
    assert.equal(input.to, 'alert@example.test')
    assert.equal(input.matches[0].id, 'booking-1')
  }

  const first = await alerts.runWatchlistAlerts({ dryRun: false, fetchImpl: fetchImpl as typeof fetch, sendEmail, limit: 5 })
  assert.deepEqual({ checked: first.checked, matched: first.matched, queuedEmails: first.queuedEmails, sentEmails: first.sentEmails, errors: first.errors.length }, {
    checked: 1, matched: 1, queuedEmails: 1, sentEmails: 1, errors: 0,
  })
  assert.equal(sent, 1)

  const second = await alerts.runWatchlistAlerts({ dryRun: false, fetchImpl: fetchImpl as typeof fetch, sendEmail, limit: 5 })
  assert.deepEqual({ checked: second.checked, matched: second.matched, queuedEmails: second.queuedEmails, sentEmails: second.sentEmails, errors: second.errors.length }, {
    checked: 1, matched: 0, queuedEmails: 0, sentEmails: 0, errors: 0,
  })
  assert.equal(sent, 1)
})
