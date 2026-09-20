'use client'

import Link from 'next/link'
import { useEffect, useRef, useState, useEffectEvent } from 'react'
import { Booking, Jurisdiction, bondLabel } from './types'
import { PaywallGate } from '@/components/subscriptions/PaywallGate'
import { useSubscription } from '@/lib/subscriptions/useSubscription'
import { Download, Bell, Lock } from 'lucide-react'

export function SearchRecords({ initial = { name: '', state: '', county: '' } }: { initial?: { name: string; state: string; county: string } }) {
  const [name, setName] = useState(initial.name)
  const [state, setState] = useState(initial.state)
  const [county, setCounty] = useState(initial.county)
  const [jurisdictions, setJurisdictions] = useState<Jurisdiction[]>([])
  const [items, setItems] = useState<Booking[]>([])
  const [suggestions, setSuggestions] = useState<Booking[]>([])
  const [active, setActive] = useState(-1)
  const [open, setOpen] = useState(false)
  const [message, setMessage] = useState('Enter a name to search supported jurisdictions.')
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [more, setMore] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [chargeFilter, setChargeFilter] = useState('')
  const [watchMessage, setWatchMessage] = useState('')
  const generation = useRef(0)
  const resultsController = useRef<AbortController | null>(null)
  const selectedQuery = useRef({ name: '', state: '', county: '' })
  const { canAccess } = useSubscription()
  const runInitial = useEffectEvent(() => { void search() })
  useEffect(() => { if (initial.name.trim().length >= 2) runInitial() }, [initial.name])

  useEffect(() => {
    const controller = new AbortController()
    fetch('/api/jurisdictions', { signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error('Supported jurisdictions are unavailable. The records service may not be configured.')
      setJurisdictions(await response.json())
    }).catch(error => { if (error.name !== 'AbortError') setMessage(error.message) })
    return () => { controller.abort(); resultsController.current?.abort() }
  }, [])

  useEffect(() => {
    if (name.trim().length < 2 || !open) return
    const controller = new AbortController()
    const timeout = setTimeout(async () => {
      try {
        const query = new URLSearchParams({ name: name.trim(), ...(state && { state }), ...(county && { county }) })
        const response = await fetch('/api/search?' + query, { signal: controller.signal })
        if (response.ok) setSuggestions((await response.json()).items.slice(0, 5))
      } catch { /* Full search displays service errors; autocomplete is optional. */ }
    }, 350)
    return () => { clearTimeout(timeout); controller.abort() }
  }, [name, state, county, open])

  async function search(nextPage = 1) {
    setOpen(false); setSuggestions([])
    const values = nextPage === 1 ? { name: name.trim(), state, county } : selectedQuery.current
    if (values.name.length < 2) { setMessage('Enter at least two characters.'); return }
    selectedQuery.current = values
    resultsController.current?.abort()
    const controller = new AbortController()
    resultsController.current = controller
    const current = ++generation.current
    setLoading(true); setMessage('Searching…'); setItems([]); setMore(false)
    try {
      const query = new URLSearchParams({ name: values.name, page: String(nextPage), ...(values.state && { state: values.state }), ...(values.county && { county: values.county }) })
      const response = await fetch('/api/search?' + query, { signal: controller.signal })
      if (!response.ok) throw new Error(response.status === 429 ? 'Too many searches. Please wait a minute.' : response.status === 428 ? 'Your Route Check expired. Refresh this page to unlock search again.' : 'Search is unavailable. Please try again later.')
      const data = await response.json()
      if (current !== generation.current) return
      setItems(data.items); setPage(nextPage); setMore(data.has_more)
      setMessage(data.items.length ? `${data.items.length} bookings on page ${nextPage}. Similar names may belong to different people.` : 'No currently publishable matches on this page. Coverage is limited to participating sources.')
    } catch (error) {
      if (current === generation.current && !controller.signal.aborted) setMessage(error instanceof Error ? error.message : 'Search failed.')
    } finally { if (current === generation.current) setLoading(false) }
  }
  async function watchCurrentSearch() {
    const values = selectedQuery.current.name ? selectedQuery.current : { name: name.trim(), state, county }
    if (values.name.length < 2) { setWatchMessage('Search for a name first, then add it to your watchlist.'); return }
    setWatchMessage('Saving watchlist…')
    try {
      const response = await fetch('/api/account/watchlists', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          label: `${values.name}${values.county ? ` in ${values.county}` : values.state ? ` in ${values.state}` : ''}`,
          name: values.name,
          state: values.state,
          county: values.county,
        }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(response.status === 401 ? 'Sign in or create a free account to create a watchlist.' : data.error || 'Watchlist could not be saved.')
      setWatchMessage('Watchlist saved. Manage it in your workspace.')
    } catch (error) { setWatchMessage(error instanceof Error ? error.message : 'Watchlist could not be saved.') }
  }

  return <section>
    <form onSubmit={event => { event.preventDefault(); void search() }} className="search-form">
      <div className="search-field relative">
        <label htmlFor="record-name">First or last name</label>
        <input id="record-name" className="search-input" value={name} minLength={2} maxLength={100} required autoComplete="off"
          role="combobox" aria-autocomplete="list" aria-expanded={open && suggestions.length > 0} aria-controls="name-options"
          aria-activedescendant={open && active >= 0 && suggestions[active] ? `name-option-${active}` : undefined}
          onFocus={() => setOpen(true)} onBlur={() => { setOpen(false); setActive(-1) }}
          onChange={event => { setName(event.target.value); setSuggestions([]); setActive(-1); setOpen(true) }}
          onKeyDown={event => {
            if (event.key === 'Escape') { setOpen(false); setActive(-1) }
            if (event.key === 'ArrowDown' && suggestions.length) { event.preventDefault(); setActive(index => Math.min(index + 1, suggestions.length - 1)); setOpen(true) }
            if (event.key === 'ArrowUp') { event.preventDefault(); setActive(index => Math.max(0, index - 1)) }
            if (event.key === 'Enter' && open && suggestions[active]) { event.preventDefault(); setName(`${suggestions[active].first_name} ${suggestions[active].last_name}`); setOpen(false); setActive(-1) }
          }} />
        <ul id="name-options" role="listbox" aria-label="Suggested booking names" hidden={!open || !suggestions.length} className="search-suggestions">
          {suggestions.map((item, index) => <li key={item.id} id={`name-option-${index}`} role="option" aria-selected={index === active}
            className={`search-suggestion ${index === active ? 'active' : ''}`}
            onMouseDown={event => { event.preventDefault(); setName(`${item.first_name} ${item.last_name}`); setOpen(false); setActive(-1) }}>
            {item.first_name} {item.last_name} — {item.county}, {item.state}
          </li>)}
        </ul>
      </div>
      <label className="search-field">State<select className="search-select" value={state} onChange={event => { setState(event.target.value); setCounty(''); setSuggestions([]); setActive(-1) }}>
        <option value="">All supported states</option>{state && !jurisdictions.some(j => j.state === state) && <option value={state}>{state} (coverage unconfirmed)</option>}{[...new Set(jurisdictions.map(j => j.state))].map(value => <option key={value}>{value}</option>)}
      </select></label>
      <label className="search-field">County<select className="search-select" value={county} onChange={event => { setCounty(event.target.value); setSuggestions([]); setActive(-1) }}>
        <option value="">All supported counties</option>{county && !jurisdictions.some(j => j.county === county && (!state || j.state === state)) && <option value={county}>{county} (coverage unconfirmed)</option>}{[...new Set(jurisdictions.filter(j => !state || j.state === state).map(j => j.county))].map(value => <option key={value}>{value}</option>)}
      </select></label>
      <button disabled={loading} className="jm-button">{loading ? 'Searching…' : 'Search public records'}</button>
    </form>

    <div style={{ display: 'flex', gap: '8px', marginBlock: '12px', flexWrap: 'wrap' }}>
      <button className="jm-button secondary" type="button" onClick={() => void watchCurrentSearch()}>
        <Bell size={14} /> Watch this search
      </button>
      <PaywallGate requiredTier="pro" fallback={
        <button className="jm-button secondary" disabled title="Requires Pro subscription">
          <Lock size={14} /> Export CSV
        </button>
      }>
        <button className="jm-button secondary" onClick={() => alert('Export feature coming soon')}>
          <Download size={14} /> Export CSV
        </button>
      </PaywallGate>
      <PaywallGate requiredTier="pro" fallback={
        <button className="jm-button secondary" disabled title="Requires Pro subscription">
          <Lock size={14} /> Advanced filters
        </button>
      }>
        <button className="jm-button secondary" onClick={() => setShowAdvanced(!showAdvanced)}>
          Advanced filters
        </button>
      </PaywallGate>
    </div>
    {watchMessage && <p role="status" className="search-status">{watchMessage}</p>}

    {/* Advanced filters (Pro tier) */}
    {showAdvanced && canAccess('pro') && (
      <div style={{ padding: '16px', background: 'var(--jm-bg-secondary)', borderRadius: 8, marginBlock: '12px' }}>
        <h3 style={{ margin: '0 0 12px' }}>Advanced Filters</h3>
        <div className="form-two">
          <label>
            Booking date from
            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </label>
          <label>
            Booking date to
            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </label>
          <label>
            Charge classification
            <select value={chargeFilter} onChange={(e) => setChargeFilter(e.target.value)}>
              <option value="">All charges</option>
              <option value="felony">Felony</option>
              <option value="misdemeanor">Misdemeanor</option>
              <option value="infraction">Infraction</option>
            </select>
          </label>
        </div>
      </div>
    )}

    <p role="status" aria-live="polite" className="search-status">{message}</p>
    {items.length > 0 && <div className="search-results">
      <table className="admin-table">
        <caption className="sr-only">Booking search results</caption>
        <thead><tr><th scope="col">Name</th><th scope="col">County</th><th scope="col">Charges</th><th scope="col">Bond</th></tr></thead>
        <tbody>{items.map(item => <tr key={item.id}>
          <td><Link className="text-link" href={`/inmate/${item.id}`}>{item.first_name} {item.last_name}</Link></td>
          <td>{item.county}, {item.state}</td>
          <td>{item.charges.map(c => c.description).join('; ') || 'Not provided'}</td>
          <td>{item.bonds.map(bondLabel).join('; ') || 'Not provided'}</td>
        </tr>)}</tbody>
      </table>
    </div>}
    <div className="search-pagination">
      {page > 1 && <button className="text-link" disabled={loading} onClick={() => void search(page - 1)}>Previous page</button>}
      {more && <button className="text-link" disabled={loading} onClick={() => void search(page + 1)}>Next page</button>}
    </div>
  </section>
}
