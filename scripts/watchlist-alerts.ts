import { runWatchlistAlerts } from '../src/lib/watchlists/alerts.ts'

const send = process.argv.includes('--send')
const limitArg = process.argv.find(argument => argument.startsWith('--limit='))
const limit = limitArg ? Number(limitArg.slice('--limit='.length)) : 25

if (!Number.isInteger(limit) || limit < 1 || limit > 100) {
  console.error('Usage: node --experimental-strip-types scripts/watchlist-alerts.ts [--send] [--limit=25]')
  process.exit(1)
}

const result = await runWatchlistAlerts({ dryRun: !send, limit })
console.log(JSON.stringify(result, null, 2))
if (result.errors.length) process.exitCode = 1
