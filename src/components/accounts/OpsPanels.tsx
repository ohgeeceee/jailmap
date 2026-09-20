'use client'

import { useCallback, useEffect, useState } from 'react'
import { AlertTriangle, Building2, CheckCircle2, Coins, Database, Gauge, MapPin, RefreshCw, Users, Clock, ArrowRight, ExternalLink } from 'lucide-react'

/** Shared loader for the read-only administrator operations endpoints. */
function useOpsData<T>(name: string) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState('')
  const [revision, setRevision] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    fetch(`/api/admin/records/${name}`, { signal: controller.signal })
      .then(async response => {
        if (!response.ok) throw new Error('The records service is not connected or is temporarily unavailable. Account administration is still available.')
        setData(await response.json())
        setError('')
      })
      .catch(err => { if (err.name !== 'AbortError') { setError(err.message); setData(null) } })
    return () => controller.abort()
  }, [name, revision])
  return { data, error, refresh: useCallback(() => setRevision(value => value + 1), []) }
}

const n = (value: unknown) => Number(value || 0).toLocaleString('en-US')
const pct = (part: number, whole: number) => (whole > 0 ? `${((part / whole) * 100).toFixed(1)}%` : '—')
const day = (value: string | null) => (value ? new Date(value).toISOString().slice(0, 10) : '—')
const stamp = (value: string | null) => (value ? new Date(value).toISOString().replace('T', ' ').slice(0, 16) + ' UTC' : 'Never')
const hoursSince = (value: string | null) => (value ? (Date.now() - new Date(value).getTime()) / 36e5 : Infinity)

function PanelError({ message, refresh }: { message: string; refresh: () => void }) {
  return (
    <div className="panel">
      <div className="empty-state">
        <span className="empty-icon"><Database size={27} /></span>
        <h3>Records connection unavailable</h3>
        <p role="status">{message}</p>
        <button className="jm-button secondary compact" onClick={refresh}><RefreshCw size={15} />Try again</button>
      </div>
    </div>
  )
}

type Coverage = {
  directory: { states: number; counties: number; jails: number }
  pipeline: { registered: number; enabled: number; verified: number; staging: number; counties_with_source: number }
  bookings: { bookings: number; public_bookings: number; suppressed_bookings: number; active_jurisdictions: number }
  states: { state: string; state_name: string; counties: number; jails: number; registered: number; enabled: number; verified: number; staging: number; bookings: number }[]
}

export function CoveragePanel() {
  const { data, error, refresh } = useOpsData<Coverage>('coverage')
  if (error) return <PanelError message={error} refresh={refresh} />
  if (!data) return <div className="panel"><p className="panel-content" role="status">Loading coverage…</p></div>
  const { directory, pipeline, bookings } = data
  const funnel = [
    { label: 'Counties in national directory', value: directory.counties },
    { label: 'Counties with a registered source', value: pipeline.counties_with_source },
    { label: 'Registered jurisdictions', value: pipeline.registered },
    { label: 'Privacy-verified sources', value: pipeline.verified },
    { label: 'Enabled for ingestion', value: pipeline.enabled },
  ]
  const top = funnel[0].value || 1
  return (
    <>
      <div className="stat-grid five">
        <div className="stat-card"><MapPin size={20} /><span>Counties in directory</span><strong>{n(directory.counties)}</strong><p>Across {n(directory.states)} states</p></div>
        <div className="stat-card"><Building2 size={20} /><span>Facilities mapped</span><strong>{n(directory.jails)}</strong><p>Jails and detention centers</p></div>
        <div className="stat-card"><Database size={20} /><span>Registered sources</span><strong>{n(pipeline.registered)}</strong><p>{n(pipeline.staging)} staging-only</p></div>
        <div className="stat-card"><CheckCircle2 size={20} /><span>Enabled for ingestion</span><strong>{n(pipeline.enabled)}</strong><p>{n(pipeline.verified)} privacy-verified</p></div>
        <div className="stat-card"><Users size={20} /><span>Public bookings</span><strong>{n(bookings.public_bookings)}</strong><p>{n(bookings.suppressed_bookings)} withheld</p></div>
      </div>

      <section className="panel">
        <div className="panel-heading"><div><h2>National coverage funnel</h2><p>Directory → mapped facility → registered source → privacy-verified → enabled. Each step is a human decision; nothing advances automatically.</p></div><span className="status-badge">{pct(pipeline.enabled, directory.counties)} of counties live</span></div>
        <div className="funnel">
          {funnel.map(step => (
            <div className="funnel-row" key={step.label}>
              <span className="funnel-label">{step.label}</span>
              <span className="funnel-track"><span className="funnel-fill" style={{ width: `${Math.max(1, (step.value / top) * 100)}%` }} /></span>
              <span className="funnel-value">{n(step.value)}<small>{pct(step.value, top)}</small></span>
            </div>
          ))}
        </div>
      </section>

      <section className="panel">
        <div className="panel-heading"><div><h2>Coverage by state</h2><p>All {n(directory.states)} states and the District of Columbia. Rows with no registered source are the expansion backlog.</p></div></div>
        <div className="table-scroll">
          <table className="admin-table">
            <caption className="sr-only">Coverage by state</caption>
            <thead><tr><th scope="col">State</th><th scope="col">Counties</th><th scope="col">Facilities</th><th scope="col">Registered</th><th scope="col">Enabled</th><th scope="col">Public bookings</th><th scope="col">County coverage</th></tr></thead>
            <tbody>
              {data.states.map(row => (
                <tr key={row.state}>
                  <td><strong>{row.state}</strong><span>{row.state_name}</span></td>
                  <td>{n(row.counties)}</td>
                  <td>{n(row.jails)}</td>
                  <td>{n(row.registered)}{row.staging > 0 && <span>{n(row.staging)} staging</span>}</td>
                  <td><span className={`status-badge ${row.enabled === 0 ? 'warning' : ''}`}>{n(row.enabled)}</span></td>
                  <td>{n(row.bookings)}</td>
                  <td><span className="cov-cell"><span className="cov-track"><span className="cov-fill" style={{ width: `${row.counties > 0 ? Math.min(100, (row.enabled / row.counties) * 100) : 0}%` }} /></span>{row.enabled > 0 ? pct(row.enabled, row.counties) : '—'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}

type Ingestion = {
  totals: { runs: number; success: number; failed: number; running: number; last_run: string | null }
  errors: { error_type: string; count: number }[]
  sources: { id: string; state: string; county: string; facility_name: string; adapter: string; enabled: boolean; review_status: string; staging_only: boolean; last_success_at: string | null; last_status: string | null; last_run_at: string | null; last_error: string | null; last_record_count: number | null; failed_runs: number; success_runs: number }[]
}

export function IngestionPanel() {
  const { data, error, refresh } = useOpsData<Ingestion>('ingestion')
  if (error) return <PanelError message={error} refresh={refresh} />
  if (!data) return <div className="panel"><p className="panel-content" role="status">Loading ingestion health…</p></div>
  const { totals } = data
  const rate = totals.runs > 0 ? (totals.failed / totals.runs) * 100 : 0
  const failing = data.sources.filter(source => source.last_status === 'failed')
  const stale = data.sources.filter(source => source.enabled && hoursSince(source.last_success_at) > 24)
  return (
    <>
      <div className="stat-grid four">
        <div className="stat-card"><Gauge size={20} /><span>Ingestion runs</span><strong>{n(totals.runs)}</strong><p>Last run {stamp(totals.last_run)}</p></div>
        <div className="stat-card"><CheckCircle2 size={20} /><span>Successful runs</span><strong>{n(totals.success)}</strong><p>{pct(totals.success, totals.runs)} of all runs</p></div>
        <div className="stat-card"><AlertTriangle size={20} /><span>Failed runs</span><strong>{n(totals.failed)}</strong><p>{rate.toFixed(1)}% failure rate</p></div>
        <div className="stat-card"><RefreshCw size={20} /><span>Stale enabled sources</span><strong>{n(stale.length)}</strong><p>No success in 24 hours</p></div>
      </div>

      {failing.length > 0 && (
        <section className="panel">
          <div className="panel-heading"><div><h2>Failing sources</h2><p>{n(failing.length)} jurisdiction{failing.length === 1 ? '' : 's'} whose most recent run failed. Diagnose before re-running.</p></div><button className="jm-button secondary compact" onClick={refresh}><RefreshCw size={15} />Refresh</button></div>
          <div className="table-scroll">
            <table className="admin-table">
              <thead><tr><th scope="col">Facility</th><th scope="col">Location</th><th scope="col">Adapter</th><th scope="col">Last run</th><th scope="col">Last error</th><th scope="col">Fail / OK</th></tr></thead>
              <tbody>
                {failing.map(source => (
                  <tr key={source.id}>
                    <td><strong>{source.facility_name}</strong><span>{source.enabled ? 'Enabled' : 'Disabled'}</span></td>
                    <td>{source.county}, {source.state}</td>
                    <td>{source.adapter}</td>
                    <td>{stamp(source.last_run_at)}</td>
                    <td><span className="status-badge warning">{source.last_error || 'unknown'}</span></td>
                    <td>{n(source.failed_runs)} / {n(source.success_runs)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {data.errors.length > 0 && (
        <section className="panel">
          <div className="panel-heading"><div><h2>Failure reasons</h2><p>Every failed run across all sources, grouped by recorded error type.</p></div></div>
          <div className="source-stats">{data.errors.map(item => <span key={item.error_type}><strong>{n(item.count)}</strong> {item.error_type}</span>)}</div>
        </section>
      )}

      <section className="panel">
        <div className="panel-heading"><div><h2>Source run history</h2><p>{n(data.sources.length)} sources with ingestion activity. Sorted with failures first.</p></div></div>
        <div className="table-scroll">
          <table className="admin-table">
            <caption className="sr-only">Per-source ingestion health</caption>
            <thead><tr><th scope="col">Facility</th><th scope="col">Location</th><th scope="col">Adapter</th><th scope="col">Status</th><th scope="col">Last run</th><th scope="col">Last success</th><th scope="col">Records</th><th scope="col">Fail / OK</th></tr></thead>
            <tbody>
              {data.sources.map(source => (
                <tr key={source.id}>
                  <td><strong>{source.facility_name}</strong><span>{source.review_status}{source.staging_only ? ' · staging-only' : ''}</span></td>
                  <td>{source.county}, {source.state}</td>
                  <td>{source.adapter}</td>
                  <td><span className={`status-badge ${source.last_status === 'failed' ? 'warning' : ''}`}>{source.last_status || (source.enabled ? 'pending' : 'inactive')}</span></td>
                  <td>{stamp(source.last_run_at)}</td>
                  <td>{stamp(source.last_success_at)}</td>
                  <td>{source.last_record_count === null ? '—' : n(source.last_record_count)}</td>
                  <td>{n(source.failed_runs)} / {n(source.success_runs)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}

type Pipeline = {
  counties: { status: string; count: number }[]
  facilities: { status: string; count: number }[]
  enrichment: { status: string; count: number }[]
  staged: { state: string; county: string; facility_name: string; staged: number; latest_fetch: string; latest_snapshot: string }[]
  staged_total: { n: number; latest: string | null }
  advanced: { status: string; county: string; state: string; source_url: string | null; adapter: string | null; notes: string; updated_at: string }[]
}

export function PipelinePanel() {
  const { data, error, refresh } = useOpsData<Pipeline>('pipeline')
  if (error) return <PanelError message={error} refresh={refresh} />
  if (!data) return <div className="panel"><p className="panel-content" role="status">Loading discovery pipeline…</p></div>
  const total = (rows: { count: number }[]) => rows.reduce((sum, row) => sum + Number(row.count), 0)
  const queues = [
    { title: 'County discovery', rows: data.counties, note: 'Every county that still needs an official source located.' },
    { title: 'Facility discovery', rows: data.facilities, note: 'Per-jail source discovery state across the national directory.' },
    { title: 'Directory enrichment', rows: data.enrichment, note: 'County directory records awaiting research, review, or a blocker decision.' },
  ]
  return (
    <>
      <div className="stat-grid four">
        <div className="stat-card"><MapPin size={20} /><span>Counties tracked</span><strong>{n(total(data.counties))}</strong><p>In the discovery queue</p></div>
        <div className="stat-card"><Building2 size={20} /><span>Facilities tracked</span><strong>{n(total(data.facilities))}</strong><p>In the discovery queue</p></div>
        <div className="stat-card"><Database size={20} /><span>Staged bookings</span><strong>{n(data.staged_total.n)}</strong><p>Never published unreviewed</p></div>
        <div className="stat-card"><Gauge size={20} /><span>Advanced past discovery</span><strong>{n(data.counties.filter(row => row.status !== 'source_discovery').reduce((sum, row) => sum + Number(row.count), 0))}</strong><p>Adapter, testing, or blocked</p></div>
      </div>

      {queues.map(queue => (
        <section className="panel" key={queue.title}>
          <div className="panel-heading"><div><h2>{queue.title}</h2><p>{queue.note}</p></div><span className="status-badge">{n(total(queue.rows))} total</span></div>
          <div className="source-stats">{queue.rows.length === 0 ? <span>Queue is empty.</span> : queue.rows.map(row => <span key={row.status}><strong>{n(row.count)}</strong> {row.status.replaceAll('_', ' ')}</span>)}</div>
        </section>
      ))}

      {data.advanced.length > 0 && (
        <section className="panel">
          <div className="panel-heading"><div><h2>Counties past discovery</h2><p>Sources that reached adapter work, testing, or a blocker. Notes are operator-recorded.</p></div></div>
          <div className="table-scroll">
            <table className="admin-table">
              <thead><tr><th scope="col">County</th><th scope="col">State</th><th scope="col">Status</th><th scope="col">Adapter</th><th scope="col">Source</th><th scope="col">Notes</th><th scope="col">Updated</th></tr></thead>
              <tbody>
                {data.advanced.map(row => (
                  <tr key={`${row.state}-${row.county}`}>
                    <td><strong>{row.county}</strong></td>
                    <td>{row.state}</td>
                    <td><span className="status-badge">{row.status.replaceAll('_', ' ')}</span></td>
                    <td>{row.adapter || '—'}</td>
                    <td>{row.source_url ? <a className="text-link" href={row.source_url} rel="noreferrer nofollow" target="_blank">Open source<ExternalLink size={12} /></a> : '—'}</td>
                    <td>{row.notes || '—'}</td>
                    <td>{day(row.updated_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section className="panel">
        <div className="panel-heading"><div><h2>Staged bookings by source</h2><p>Records held outside the public index. Promotion to public is a separate human decision. Latest fetch {stamp(data.staged_total.latest)}.</p></div></div>
        {data.staged.length === 0 ? <div className="empty-state"><h3>No staged bookings.</h3><p>Staging-only adapters write here until an operator reviews them.</p></div> : (
          <div className="table-scroll">
            <table className="admin-table">
              <thead><tr><th scope="col">Facility</th><th scope="col">Location</th><th scope="col">Staged</th><th scope="col">Latest snapshot</th><th scope="col">Last fetched</th></tr></thead>
              <tbody>
                {data.staged.map(row => (
                  <tr key={`${row.state}-${row.county}-${row.facility_name}`}>
                    <td><strong>{row.facility_name}</strong></td>
                    <td>{row.county}, {row.state}</td>
                    <td>{n(row.staged)}</td>
                    <td>{day(row.latest_snapshot)}</td>
                    <td>{stamp(row.latest_fetch)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  )
}

type Revenue = {
  counts: { total: number; pending: number; approved: number; rejected: number; corrections: number; removals: number; overdue: number }
  requests: { id: string; kind: string; status: string; submitted_at: string; reviewed_at: string | null; booking_id: string; first_name: string; last_name: string; visibility: string; state: string; county: string; facility_name: string }[]
  payments: { configured: boolean; paid: number; gross_cents: number; error?: string; sessions: { id: string; created: number; amount_total: number | null; currency: string | null; payment_status: string; status: string | null }[] }
}

export function RevenuePanel() {
  const { data, error, refresh } = useOpsData<Revenue>('revenue')
  if (error) return <PanelError message={error} refresh={refresh} />
  if (!data) return <div className="panel"><p className="panel-content" role="status">Loading removal operations…</p></div>
  const { counts, payments } = data
  const money = (cents: number) => `$${(cents / 100).toFixed(2)}`
  return (
    <>
      <div className="stat-grid four">
        <div className="stat-card"><Coins size={20} /><span>Paid removal sessions</span><strong>{payments.configured ? n(payments.paid) : '—'}</strong><p>{payments.configured ? `${money(payments.gross_cents)} collected` : 'Payments not configured'}</p></div>
        <div className="stat-card"><Database size={20} /><span>Requests on file</span><strong>{n(counts.total)}</strong><p>{n(counts.corrections)} correction · {n(counts.removals)} removal</p></div>
        <div className="stat-card"><AlertTriangle size={20} /><span>Awaiting review</span><strong>{n(counts.pending)}</strong><p>{n(counts.overdue)} older than 7 days</p></div>
        <div className="stat-card"><CheckCircle2 size={20} /><span>Decided</span><strong>{n(counts.approved + counts.rejected)}</strong><p>{n(counts.approved)} withheld · {n(counts.rejected)} rejected</p></div>
      </div>

      <section className="panel">
        <div className="panel-heading"><div><h2>Payment provider</h2><p>Stripe checkout sessions matching the JailMap name-removal price. Payment is a review fee and never removes a record on its own.</p></div><button className="jm-button secondary compact" onClick={refresh}><RefreshCw size={15} />Refresh</button></div>
        {!payments.configured ? (
          <div className="empty-state"><h3>Payments are not configured.</h3><p>Set STRIPE_SECRET_KEY and STRIPE_REMOVAL_PRICE_ID on the API service to surface paid sessions here.</p></div>
        ) : payments.error ? (
          <p className="panel-content" role="status">{payments.error}</p>
        ) : payments.sessions.length === 0 ? (
          <div className="empty-state"><h3>No paid removal sessions yet.</h3><p>Completed checkouts will appear here with their payment status.</p></div>
        ) : (
          <div className="table-scroll">
            <table className="admin-table">
              <caption className="sr-only">Stripe checkout sessions for name removal</caption>
              <thead><tr><th scope="col">Session</th><th scope="col">Created</th><th scope="col">Amount</th><th scope="col">Payment</th><th scope="col">Checkout</th></tr></thead>
              <tbody>
                {payments.sessions.map(session => (
                  <tr key={session.id}>
                    <td><strong>{session.id}</strong></td>
                    <td>{stamp(new Date(session.created * 1000).toISOString())}</td>
                    <td>{session.amount_total === null ? '—' : money(session.amount_total)} {session.currency?.toUpperCase() || ''}</td>
                    <td><span className={`status-badge ${session.payment_status === 'paid' ? '' : 'warning'}`}>{session.payment_status}</span></td>
                    <td>{session.status || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="panel">
        <div className="panel-heading"><div><h2>Correction &amp; removal requests</h2><p>Pending requests first. Approving withholds the record; it never rewrites the source facts. Review from the Sources &amp; reviews tab.</p></div></div>
        {data.requests.length === 0 ? (
          <div className="empty-state"><h3>No requests on file.</h3><p>Public correction and removal submissions will appear here.</p></div>
        ) : (
          <div className="table-scroll">
            <table className="admin-table">
              <caption className="sr-only">Correction and removal requests</caption>
              <thead><tr><th scope="col">Booking</th><th scope="col">Location</th><th scope="col">Kind</th><th scope="col">Status</th><th scope="col">Submitted</th><th scope="col">Reviewed</th><th scope="col">Visibility</th></tr></thead>
              <tbody>
                {data.requests.map(request => (
                  <tr key={request.id}>
                    <td><strong>{request.last_name}, {request.first_name}</strong><span>{request.booking_id.slice(0, 8)}…</span></td>
                    <td>{request.county}, {request.state}</td>
                    <td><span className="status-badge">{request.kind}</span></td>
                    <td><span className={`status-badge ${request.status === 'pending' ? 'warning' : ''}`}>{request.status}</span></td>
                    <td>{day(request.submitted_at)}</td>
                    <td>{request.reviewed_at ? day(request.reviewed_at) : '—'}</td>
                    <td>{request.visibility}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  )
}