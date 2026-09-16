'use client'

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import { Trophy, Repeat } from 'lucide-react'

type Entry = {
  state: string
  county: string
  last_name: string
  first_name: string
  booking_count: number
  first_booking: string
  last_booking: string
  latest_booking_id: string
}

type Scope = 'all' | 'state' | 'county'

const STATES = ['MT', 'ID', 'GA'] // states with verified live sources today

function LeaderboardTable({ entries }: { entries: Entry[] }) {
  if (entries.length === 0) {
    return <p className="lb-empty">No repeat bookings observed yet in this scope. Counts build up as rosters are observed over time.</p>
  }
  return (
    <table className="lb-table">
      <thead>
        <tr>
          <th className="lb-rank">#</th>
          <th>Name</th>
          <th>Jurisdiction</th>
          <th className="lb-count">Bookings</th>
          <th>Most recent</th>
        </tr>
      </thead>
      <tbody>
        {entries.map((e, i) => (
          <tr key={`${e.state}-${e.county}-${e.last_name}-${e.first_name}`}>
            <td className={`lb-rank ${i < 3 ? 'lb-top' : ''}`}>{i + 1}</td>
            <td>
              <Link href={`/inmate/${e.latest_booking_id}`} className="lb-name">
                {e.last_name}, {e.first_name}
              </Link>
            </td>
            <td>{e.county}, {e.state}</td>
            <td className="lb-count"><Repeat size={13} /> {e.booking_count}</td>
            <td>{new Date(e.last_booking).toLocaleDateString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export function LeaderboardClient() {
  const [scope, setScope] = useState<Scope>('all')
  const [state, setState] = useState<string>(STATES[0])
  const [county, setCounty] = useState<string>('')
  const [counties, setCounties] = useState<{ state: string; county: string }[]>([])
  const [entries, setEntries] = useState<Entry[]>([])
  const [note, setNote] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    fetch('/api/jurisdictions')
      .then(r => (r.ok ? r.json() : Promise.reject()))
      .then(data => {
        const rows = (data as { state: string; county: string }[]) || []
        setCounties(rows.map(r => ({ state: r.state, county: r.county })))
      })
      .catch(() => {})
  }, [])

  const load = useCallback(async () => {
    setLoading(true)
    setError(false)
    try {
      const params = new URLSearchParams()
      if (scope === 'state') params.set('state', state)
      if (scope === 'county' && county) {
        params.set('state', state)
        params.set('county', county)
      }
      const response = await fetch('/api/leaderboard?' + params.toString())
      if (!response.ok) throw new Error()
      const data = await response.json()
      setEntries(data.items || [])
      setNote(data.note || '')
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }, [scope, state, county])

  useEffect(() => { void load() }, [load])

  const stateCounties = Array.from(new Set(counties.filter(c => c.state === state).map(c => c.county))).sort()

  return (
    <>
      <section className="new-bookings-hero">
        <div className="site-width">
          <div className="hero-badge"><Trophy size={14} /><span>STATS</span></div>
          <h1>Repeat Booking Leaderboard</h1>
          <p>
            Who has been booked into jail the most, based on bookings observed across
            authorized jurisdictions nationwide. Scope it to the whole country, one state, or one county.
          </p>
          <div className="hero-strip">
            <span><Trophy size={14} /> Trailing 365 days</span>
            <span>Distinct booking numbers only</span>
            <span>Name-based matching</span>
          </div>
        </div>
      </section>

      <section className="new-bookings-stage">
        <div className="site-width">
          <div className="lb-controls">
            <label>
              Scope{' '}
              <select value={scope} onChange={e => setScope(e.target.value as Scope)}>
                <option value="all">All states</option>
                <option value="state">By state</option>
                <option value="county">By county</option>
              </select>
            </label>
            {scope !== 'all' && (
              <label>
                State{' '}
                <select value={state} onChange={e => { setState(e.target.value); setCounty('') }}>
                  {STATES.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </label>
            )}
            {scope === 'county' && (
              <label>
                County{' '}
                <select value={county} onChange={e => setCounty(e.target.value)}>
                  <option value="">Choose a county…</option>
                  {stateCounties.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </label>
            )}
          </div>

          {loading ? (
            <p className="lb-empty">Loading…</p>
          ) : error ? (
            <p className="lb-empty">Leaderboard temporarily unavailable.</p>
          ) : (
            <LeaderboardTable entries={entries} />
          )}

          {note && <p className="lb-note">{note}</p>}
        </div>
      </section>
    </>
  )
}
