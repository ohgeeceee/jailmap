import { after, test } from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve, sep } from 'node:path'

const directory = mkdtempSync(join(tmpdir(), 'jailmap-route-check-'))
process.env.AUTH_DATABASE_PATH = join(directory, 'accounts.sqlite')
process.env.ROUTE_CHECK_SECRET = 'synthetic-route-check-secret-at-least-32-characters'
const accounts = await import('../src/lib/accounts/store.ts')
const routeCheck = await import('../src/lib/search/route-check.ts')

after(() => { accounts.database().close(); assert.ok(resolve(directory).startsWith(resolve(tmpdir()) + sep + 'jailmap-route-check-')); rmSync(directory, { recursive: true, force: true }) })

test('challenge is client-bound, single-use, and produces a client-bound permit', () => {
  const challenge = routeCheck.createRouteChallenge('client-a')
  assert.equal(challenge.options.length, 4)
  assert.equal(new Set(challenge.options.map(option => option.id)).size, 4)
  const answer = challenge.options.find(option => option.glyph === challenge.target.glyph)?.id
  assert.ok(answer)
  assert.equal('prompt' in challenge, false)
  assert.equal(routeCheck.solveRouteChallenge(challenge.id, answer, 'client-b'), null)
  const permit = routeCheck.solveRouteChallenge(challenge.id, answer, 'client-a')
  assert.ok(permit)
  assert.equal(routeCheck.solveRouteChallenge(challenge.id, answer, 'client-a'), null)
  assert.equal(routeCheck.validRoutePermit(permit!, 'client-a'), true)
  assert.equal(routeCheck.validRoutePermit(permit!, 'client-b'), false)
  assert.equal(routeCheck.validRoutePermit(permit!.slice(0, -1) + '0', 'client-a'), false)
})
