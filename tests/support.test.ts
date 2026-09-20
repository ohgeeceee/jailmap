import { after, test } from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve, sep } from 'node:path'

const directory = mkdtempSync(join(tmpdir(), 'jailmap-support-test-'))
process.env.AUTH_DATABASE_PATH = join(directory, 'accounts.sqlite')
const accounts = await import('../src/lib/accounts/store.ts')
const support = await import('../src/lib/support/store.ts')

after(() => {
  accounts.database().close()
  assert.ok(resolve(directory).startsWith(resolve(tmpdir()) + sep + 'jailmap-support-test-'))
  rmSync(directory, { recursive: true, force: true })
})

test('support tickets validate, list, and close without exposing credentials', () => {
  const id = support.createSupportTicket({ name: 'Test Sender', email: 'Sender@Example.test', subject: 'Account question', message: 'This is a synthetic support request.' })
  const open = support.listSupportTickets()
  assert.equal(open.length, 1)
  assert.equal(open[0].id, id)
  assert.equal(open[0].email, 'sender@example.test')
  assert.equal(open[0].status, 'open')
  support.setSupportTicketStatus(id, 'closed')
  assert.equal(support.listSupportTickets().length, 0)
  assert.equal(support.listSupportTickets('closed')[0].status, 'closed')
  assert.throws(() => support.createSupportTicket({ name: 'T', email: 'invalid', subject: 'No', message: 'short' }))
})
