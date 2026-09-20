import Link from 'next/link'
import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import { prisma } from '@/lib/prisma'

export const metadata = { title: 'JailMap status', robots: { index: false, follow: false } }
export const dynamic = 'force-dynamic'

type StatRow = { enabled_jurisdictions: bigint; bookings_48h: bigint; bookings_total: bigint }
type RunRow = { success_24h: bigint; failed_24h: bigint; running_now: bigint }
type ErrorRow = { error_type: string; count: bigint }

export default async function StatusPage() {
  let stats: StatRow = { enabled_jurisdictions: BigInt(0), bookings_48h: BigInt(0), bookings_total: BigInt(0) }
  let runs: RunRow = { success_24h: BigInt(0), failed_24h: BigInt(0), running_now: BigInt(0) }
  let topErrors: ErrorRow[] = []
  let lastSuccess: Date | null = null

  try {
    const [statsRows, runRows, errorRows, lastRun] = await Promise.all([
      prisma.$queryRawUnsafe<StatRow[]>(`SELECT
        (SELECT count(*) FROM records.jurisdictions WHERE enabled) AS enabled_jurisdictions,
        (SELECT count(*) FROM records.inmates i JOIN records.jurisdictions j ON j.id=i.jurisdiction_id
          WHERE j.enabled AND i.visibility='public' AND i.observed_at > now() - interval '48 hours') AS bookings_48h,
        (SELECT count(*) FROM records.inmates i JOIN records.jurisdictions j ON j.id=i.jurisdiction_id
          WHERE j.enabled AND i.visibility='public') AS bookings_total`),
      prisma.$queryRawUnsafe<RunRow[]>(`SELECT
        count(*) FILTER (WHERE status='success') AS success_24h,
        count(*) FILTER (WHERE status='failed') AS failed_24h,
        count(*) FILTER (WHERE status='running') AS running_now
        FROM records.ingestion_runs WHERE started_at > now() - interval '24 hours'`),
      prisma.$queryRawUnsafe<ErrorRow[]>(`SELECT error_type, count(*) AS count FROM records.ingestion_runs
        WHERE started_at > now() - interval '7 days' AND status='failed' AND error_type IS NOT NULL
        GROUP BY error_type ORDER BY count DESC LIMIT 5`),
      prisma.$queryRawUnsafe<{ ts: Date }[]>(`SELECT max(started_at) AS ts FROM records.ingestion_runs WHERE status='success'`),
    ])
    if (statsRows[0]) stats = statsRows[0]
    if (runRows[0]) runs = runRows[0]
    topErrors = errorRows
    lastSuccess = lastRun[0]?.ts ?? null
  } catch {
    // Log but do not 500 — status page should degrade gracefully
    console.error('[status] DB query failed')
  }

  const health: 'healthy' | 'degraded' | 'down' =
    runs.success_24h > 0 && runs.failed_24h < runs.success_24h ? 'healthy'
    : runs.running_now > 0 ? 'degraded'
    : stats.enabled_jurisdictions > 0 ? 'down' : 'degraded'

  const healthLabel = { healthy: 'Systems operational', degraded: 'Degraded', down: 'Service disruption' }[health]
  const healthColor = { healthy: 'var(--sage)', degraded: 'var(--gold)', down: '#c0392b' }[health]

  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content">
        <section className="site-width status-page">
          <Link href="/" className="back-link">← JailMap</Link>
          <h1>Platform status</h1>
          <div className="status-health" style={{ borderLeftColor: healthColor }}>
            <span className="status-dot" style={{ background: healthColor }} />
            <strong>{healthLabel}</strong>
            {lastSuccess && <span className="status-last">Last successful refresh {lastSuccess.toLocaleString()}</span>}
          </div>

          <section className="stats-strip">
            <div className="stats-strip__grid">
              <div className="stat-pill"><span className="stat-num">{Number(stats.enabled_jurisdictions)}</span><span className="stat-label">Live jurisdictions</span></div>
              <div className="stat-pill"><span className="stat-num">{Number(stats.bookings_48h)}</span><span className="stat-label">Bookings (48h)</span></div>
              <div className="stat-pill"><span className="stat-num">{Number(stats.bookings_total)}</span><span className="stat-label">Total indexed</span></div>
              <div className="stat-pill"><span className="stat-num">{Number(runs.running_now)}</span><span className="stat-label">Ingests in progress</span></div>
            </div>
          </section>

          <h2>Last 24 hours</h2>
          <div className="ingestion-summary">
            <div className="ingestion-metric success"><strong>{Number(runs.success_24h)}</strong><span>Successful runs</span></div>
            <div className="ingestion-metric failed"><strong>{Number(runs.failed_24h)}</strong><span>Failed runs</span></div>
          </div>

          {topErrors.length > 0 && (
            <>
              <h2>Top errors (7 days)</h2>
              <table className="admin-table">
                <thead><tr><th scope="col">Error</th><th scope="col">Count</th></tr></thead>
                <tbody>{topErrors.map(e => <tr key={e.error_type}><td>{e.error_type}</td><td>{Number(e.count)}</td></tr>)}</tbody>
              </table>
            </>
          )}

          <p className="status-note">
            JailMap refreshes authorized records daily. A jurisdiction is &ldquo;live&rdquo; when its most recent authorized refresh completed successfully.
            Pages like <Link href="/search">search</Link> and the <Link href="/leaderboard">leaderboard</Link> reflect the latest committed data.
          </p>
        </section>
      </main>
      <Footer />
    </div>
  )
}
