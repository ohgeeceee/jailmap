import { createHmac } from 'node:crypto'
import { dueWatchlists, recordWatchlistCheck, unnotifiedWatchlistMatches, type WatchlistCandidate } from '../accounts/store.ts'
import { sendWatchlistAlertEmail, type WatchlistAlertBooking } from '../accounts/mail.ts'

type SearchResponse = { items: WatchlistAlertBooking[] }
export type WatchlistAlertResult = {
  checked: number
  matched: number
  queuedEmails: number
  sentEmails: number
  dryRun: boolean
  errors: string[]
}

type Options = {
  dryRun?: boolean
  limit?: number
  fetchImpl?: typeof fetch
  sendEmail?: typeof sendWatchlistAlertEmail
}

function recordsConfig() {
  const base = process.env.RECORDS_API_URL
  const token = process.env.RECORDS_API_TOKEN
  if (!base || !token || token.length < 32) throw new Error('Records service is not configured')
  return { base, token }
}

function manageUrl() {
  return `${process.env.APP_ORIGIN || 'https://jailmap.com'}/dashboard?tab=watchlists`
}

async function searchWatchlist(watchlist: WatchlistCandidate, fetchImpl: typeof fetch) {
  const { base, token } = recordsConfig()
  const query = new URLSearchParams({ name: watchlist.name, page: '1' })
  if (watchlist.state) query.set('state', watchlist.state)
  if (watchlist.county) query.set('county', watchlist.county)
  const client = createHmac('sha256', token).update(`watchlist:${watchlist.id}`).digest('hex')
  const response = await fetchImpl(new URL(`/api/search?${query}`, base), {
    method: 'GET',
    cache: 'no-store',
    signal: AbortSignal.timeout(15000),
    headers: { 'x-gateway-token': token, 'x-records-client': client },
  })
  if (!response.ok) throw new Error(`Search failed with status ${response.status}`)
  const data = await response.json() as SearchResponse
  return Array.isArray(data.items) ? data.items : []
}

export async function runWatchlistAlerts(options: Options = {}): Promise<WatchlistAlertResult> {
  const dryRun = options.dryRun ?? true
  const limit = options.limit ?? 25
  const fetchImpl = options.fetchImpl ?? fetch
  const sendEmail = options.sendEmail ?? sendWatchlistAlertEmail
  const result: WatchlistAlertResult = { checked: 0, matched: 0, queuedEmails: 0, sentEmails: 0, dryRun, errors: [] }
  for (const watchlist of dueWatchlists(limit)) {
    result.checked += 1
    try {
      const matches = await searchWatchlist(watchlist, fetchImpl)
      const ids = matches.map(match => match.id).filter(Boolean)
      const freshIds = dryRun ? ids : unnotifiedWatchlistMatches(watchlist.id, ids)
      const fresh = matches.filter(match => freshIds.includes(match.id))
      result.matched += fresh.length
      if (fresh.length) {
        result.queuedEmails += 1
        if (!dryRun) {
          await sendEmail({
            to: watchlist.account_email,
            accountName: watchlist.account_name,
            label: watchlist.label,
            query: watchlist.name,
            state: watchlist.state,
            county: watchlist.county,
            matches: fresh,
            manageUrl: manageUrl(),
          })
          result.sentEmails += 1
        }
      }
      if (!dryRun) recordWatchlistCheck(watchlist.id, ids, freshIds)
    } catch (error) {
      result.errors.push(`${watchlist.id}: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }
  return result
}
