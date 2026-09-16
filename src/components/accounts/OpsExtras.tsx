/* JailMap admin - operations additions.
   Run history with real failure text, a coverage-gap map, and freshness/triage
   for enabled sources. The only write in this file is an administrator pressing
   Save on a triage note: nothing here enables a source or publishes a record. */
'use client'
import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { AlertTriangle, CheckCircle2, Clock, MapPin, RefreshCw } from 'lucide-react'

function stamp(value: string | null | undefined) {
  if (!value) return '—'
  return new Date(value).toISOString().replace('T', ' ').slice(0, 16) + ' UTC'
}
function num(value: number | null | undefined) {
  return value === null || value === undefined ? '—' : Number(value).toLocaleString('en-US')
}
function pct(part: number, whole: number) {
  if (!whole) return '0%'
  return ((part / whole) * 100).toFixed(1) + '%'
}
function age(hours: number | string | null | undefined) {
  if (hours === null || hours === undefined) return 'never'
  const value = Number(hours)
  if (!Number.isFinite(value)) return 'never'
  if (value < 1) return 'under an hour'
  if (value < 48) return Math.round(value) + 'h'
  return Math.round(value / 24) + 'd'
}

function useOpsData<T>(name: string) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const load = useCallback(async () => {
    try {
      const response = await fetch('/api/admin/records/' + name, { cache: 'no-store' })
      if (!response.ok) {
        setError(response.status === 403 ? 'Administrator access required.' : 'Request failed (' + response.status + ').')
        return
      }
      setData((await response.json()) as T)
      setError(null)
    } catch {
      setError('Could not reach the records service.')
    }
  }, [name])
  useEffect(() => { void load() }, [load])
  return { data, error, refresh: load }
}

function PanelShell({ title, error, refresh, children }: { title: string; error?: string | null; refresh: () => void; children: ReactNode }) {
  if (error) return <section className="panel"><div className="panel-heading"><div><h2>{title}</h2><p>{error}</p></div><button className="jm-button secondary compact" onClick={refresh}><RefreshCw size={15} />Retry</button></div></section>
  return <>{children}</>
}

type Gap = { state: string; county: string; sources: number }
type Gaps = { totals: { counties: number; with_source: number; with_enabled: number }; gaps: Gap[]; limit: number; truncated: boolean }

export function CoverageGaps() {
  const { data, error, refresh } = useOpsData<Gaps>('gaps')
  const [filter, setFilter] = useState('')
  const rows = useMemo(() => {
    if (!data) return []
    const needle = filter.trim().toLowerCase()
    if (!needle) return data.gaps
    return data.gaps.filter(row => (row.state + ' ' + row.county).toLowerCase().includes(needle))
  }, [data, filter])

  if (!data) return <PanelShell title="Coverage gaps" error={error} refresh={refresh}><section className="panel"><p className="panel-content" role="status">Loading coverage gaps…</p></section></PanelShell>
  const { totals } = data
  return (
    <PanelShell title="Coverage gaps" error={error} refresh={refresh}>
      <div className="stat-grid four">
        <div className="stat-card"><MapPin size={20} /><span>Counties in directory</span><strong>{num(totals.counties)}</strong><p>From the geographic directory</p></div>
        <div className="stat-card"><CheckCircle2 size={20} /><span>Counties with a source</span><strong>{num(totals.with_source)}</strong><p>{pct(totals.with_source, totals.counties)} of the directory</p></div>
        <div className="stat-card"><CheckCircle2 size={20} /><span>Counties with an enabled source</span><strong>{num(totals.with_enabled)}</strong><p>{pct(totals.with_enabled, totals.counties)} live coverage</p></div>
        <div className="stat-card"><AlertTriangle size={20} /><span>Counties with no enabled source</span><strong>{num(totals.counties - totals.with_enabled)}</strong><p>The expansion roadmap</p></div>
      </div>
      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Counties with no enabled source</h2>
            <p>Every county in the directory that has no enabled jurisdiction, alphabetically. Showing {num(rows.length)} of {num(data.gaps.length)} loaded (limit {num(data.limit)}{data.truncated ? ', truncated' : ''}).</p>
          </div>
          <div className="access-form">
            <label className="sr-only" htmlFor="gap-filter">Filter counties</label>
            <input id="gap-filter" type="search" value={filter} onChange={event => setFilter(event.target.value)} placeholder="Filter by state or county" />
            <button className="jm-button secondary compact" type="button" onClick={refresh}><RefreshCw size={15} />Refresh</button>
          </div>
        </div>
        <div className="table-scroll">
          <table className="admin-table">
            <caption className="sr-only">Counties without an enabled ingestion source</caption>
            <thead><tr><th scope="col">State</th><th scope="col">County</th><th scope="col">Registered sources</th><th scope="col">Status</th></tr></thead>
            <tbody>
              {rows.map(row => (
                <tr key={row.state + '-' + row.county}>
                  <td><strong>{row.state}</strong></td>
                  <td>{row.county}</td>
                  <td>{num(row.sources)}</td>
                  <td><span className="status-badge warning">{row.sources ? 'registered, none enabled' : 'no source found yet'}</span></td>
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan={4}>No county matches that filter.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>
    </PanelShell>
  )
}

type Run = {
  id: number; status: string; started_at: string; finished_at: string | null
  record_count: number | null; error_type: string | null; error_detail: string | null
  jurisdiction_id: string; state: string; county: string; facility_name: string; adapter: string
}
type Runs = { runs: Run[]; totals: { runs: number; success: number; failed: number }; limit: number }

export function RunHistory() {
  const { data, error, refresh } = useOpsData<Runs>('ingestion/runs')
  const [onlyFailed, setOnlyFailed] = useState(true)
  const [filter, setFilter] = useState('')
  const rows = useMemo(() => {
    if (!data) return []
    const needle = filter.trim().toLowerCase()
    return data.runs.filter(run => {
      if (onlyFailed && run.status !== 'failed') return false
      if (!needle) return true
      return [run.state, run.county, run.facility_name, run.adapter, run.error_type, run.error_detail]
        .join(' ').toLowerCase().includes(needle)
    })
  }, [data, onlyFailed, filter])

  if (!data) return <PanelShell title="Run history" error={error} refresh={refresh}><section className="panel"><p className="panel-content" role="status">Loading run history…</p></section></PanelShell>
  return (
    <PanelShell title="Run history" error={error} refresh={refresh}>
      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Run history and failure detail</h2>
            <p>Most recent {num(data.limit)} runs across all sources ({num(data.totals.failed)} failed of {num(data.totals.runs)} recorded). Error text is captured when a run fails; runs recorded before this upgrade show the error type only.</p>
          </div>
          <div className="access-form">
            <label className="sr-only" htmlFor="run-filter">Filter runs</label>
            <input id="run-filter" type="search" value={filter} onChange={event => setFilter(event.target.value)} placeholder="Filter by county, adapter or error" />
            <label className="sr-only" htmlFor="run-status">Show failures only</label>
            <input id="run-status" type="checkbox" checked={onlyFailed} onChange={event => setOnlyFailed(event.target.checked)} />
            <span>Failures only</span>
            <button className="jm-button secondary compact" type="button" onClick={refresh}><RefreshCw size={15} />Refresh</button>
          </div>
        </div>
        <div className="table-scroll">
          <table className="admin-table">
            <caption className="sr-only">Recent ingestion runs</caption>
            <thead><tr><th scope="col">Started</th><th scope="col">Facility</th><th scope="col">Adapter</th><th scope="col">Status</th><th scope="col">Records</th><th scope="col">Error</th></tr></thead>
            <tbody>
              {rows.map(run => (
                <tr key={run.id}>
                  <td>{stamp(run.started_at)}</td>
                  <td><strong>{run.facility_name}</strong><span>{run.county}, {run.state}</span></td>
                  <td>{run.adapter}</td>
                  <td><span className={'status-badge ' + (run.status === 'failed' ? 'warning' : '')}>{run.status}</span></td>
                  <td>{num(run.record_count)}</td>
                  <td>
                    <span className="status-badge warning">{run.error_type || '—'}</span>
                    {run.error_detail && <span className="error-detail">{run.error_detail}</span>}
                  </td>
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan={6}>No run matches that filter.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>
    </PanelShell>
  )
}

const TRIAGE_CHOICES = [
  { value: 'open', label: 'Open' },
  { value: 'investigating', label: 'Investigating' },
  { value: 'waiting_on_source', label: 'Waiting on source' },
  { value: 'fixed', label: 'Fixed' },
  { value: 'accepted_stale', label: 'Accepted stale' },
]

type FreshSource = {
  jurisdiction_id: string; state: string; county: string; facility_name: string; adapter: string
  staging_only: boolean; last_success_at: string | null; hours_since_success: number | string | null
  failed_7d: number; last_error: string | null; last_status: string | null; last_run_at: string | null
  triage_status: string; triage_note: string; triage_updated_at: string | null
}
type Freshness = {
  totals: { enabled: number; fresh: number; stale: number; never_succeeded: number }
  sources: FreshSource[]; hours: number
}

export function FreshnessPanel() {
  const { data, error, refresh } = useOpsData<Freshness>('freshness')
  const [drafts, setDrafts] = useState<Record<string, { status: string; note: string }>>({})
  const [saving, setSaving] = useState<string | null>(null)
  const [message, setMessage] = useState('')
  const [onlyProblems, setOnlyProblems] = useState(true)

  const rows = useMemo(() => {
    if (!data) return []
    if (!onlyProblems) return data.sources
    return data.sources.filter(source => source.last_success_at === null
      || Number(source.hours_since_success) > data.hours
      || source.last_status === 'failed')
  }, [data, onlyProblems])

  function draftOf(source: FreshSource) {
    return drafts[source.jurisdiction_id] ?? { status: source.triage_status, note: source.triage_note }
  }
  function updateDraft(source: FreshSource, patch: Partial<{ status: string; note: string }>) {
    setDrafts(current => ({ ...current, [source.jurisdiction_id]: { ...draftOf(source), ...patch } }))
  }
  async function save(source: FreshSource) {
    const draft = draftOf(source)
    setSaving(source.jurisdiction_id); setMessage('')
    try {
      const response = await fetch('/api/admin/records/work', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ kind: 'source_health', state: source.state, county: source.county, status: draft.status, note: draft.note }),
      })
      const result = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(result.detail || 'Save failed (' + response.status + ')')
      setMessage('Triage saved for ' + source.county + ', ' + source.state + '. Nothing was enabled or published.')
      setDrafts(current => {
        const next = { ...current }
        delete next[source.jurisdiction_id]
        return next
      })
      refresh()
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : 'Save failed.')
    } finally {
      setSaving(null)
    }
  }

  if (!data) return <PanelShell title="Freshness and triage" error={error} refresh={refresh}><section className="panel"><p className="panel-content" role="status">Loading freshness…</p></section></PanelShell>
  const { totals } = data
  return (
    <PanelShell title="Freshness and triage" error={error} refresh={refresh}>
      <div className="stat-grid four">
        <div className="stat-card"><CheckCircle2 size={20} /><span>Enabled sources</span><strong>{num(totals.enabled)}</strong><p>Jurisdictions currently live</p></div>
        <div className="stat-card"><CheckCircle2 size={20} /><span>Fresh sources</span><strong>{num(totals.fresh)}</strong><p>Successful run within {num(data.hours)}h</p></div>
        <div className="stat-card"><Clock size={20} /><span>Stale sources</span><strong>{num(totals.stale)}</strong><p>No success in {num(data.hours)}h</p></div>
        <div className="stat-card"><AlertTriangle size={20} /><span>Never succeeded</span><strong>{num(totals.never_succeeded)}</strong><p>Enabled but no successful run</p></div>
      </div>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Source freshness and triage</h2>
            <p>Enabled sources, stalest first. A triage note is recorded only when you press Save; it never changes whether a source is enabled or publishes anything.</p>
          </div>
          <div className="access-form">
            <label className="sr-only" htmlFor="fresh-status">Show problems only</label>
            <input id="fresh-status" type="checkbox" checked={onlyProblems} onChange={event => setOnlyProblems(event.target.checked)} />
            <span>Problems only</span>
            <button className="jm-button secondary compact" type="button" onClick={refresh}><RefreshCw size={15} />Refresh</button>
          </div>
        </div>
        {message && <p className="form-success" role="status">{message}</p>}
        <div className="table-scroll">
          <table className="admin-table">
            <caption className="sr-only">Freshness and triage state for enabled sources</caption>
            <thead><tr><th scope="col">Facility</th><th scope="col">Adapter</th><th scope="col">Last success</th><th scope="col">Failures 7d</th><th scope="col">Last error</th><th scope="col">Triage</th></tr></thead>
            <tbody>
              {rows.map(source => {
                const draft = draftOf(source)
                const stale = source.last_success_at === null || Number(source.hours_since_success) > data.hours
                return (
                  <tr key={source.jurisdiction_id}>
                    <td><strong>{source.facility_name}</strong><span>{source.county}, {source.state}{source.staging_only ? ' · staging-only' : ''}</span></td>
                    <td>{source.adapter}</td>
                    <td>
                      <span className={'status-badge ' + (stale ? 'warning' : '')}>{age(source.hours_since_success)}</span>
                      <span>{stamp(source.last_success_at)}</span>
                    </td>
                    <td>{num(source.failed_7d)}</td>
                    <td><span className="status-badge warning">{source.last_error || source.last_status || '—'}</span></td>
                    <td>
                      <form className="access-form" onSubmit={event => { event.preventDefault(); void save(source) }}>
                        <label className="sr-only" htmlFor={'status-' + source.jurisdiction_id}>Triage status for {source.facility_name}</label>
                        <select id={'status-' + source.jurisdiction_id} value={draft.status} onChange={event => updateDraft(source, { status: event.target.value })}>
                          {TRIAGE_CHOICES.map(choice => <option key={choice.value} value={choice.value}>{choice.label}</option>)}
                        </select>
                        <label className="sr-only" htmlFor={'note-' + source.jurisdiction_id}>Triage note for {source.facility_name}</label>
                        <input id={'note-' + source.jurisdiction_id} type="text" maxLength={500} value={draft.note}
                          onChange={event => updateDraft(source, { note: event.target.value })} placeholder="Note" />
                        <button className="jm-button secondary compact" disabled={saving === source.jurisdiction_id}>
                          {saving === source.jurisdiction_id ? 'Saving…' : 'Save'}
                        </button>
                      </form>
                      {source.triage_updated_at && <span>Updated {stamp(source.triage_updated_at)}</span>}
                    </td>
                  </tr>
                )
              })}
              {rows.length === 0 && <tr><td colSpan={6}>No source is stale or failing right now.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>
    </PanelShell>
  )
}
