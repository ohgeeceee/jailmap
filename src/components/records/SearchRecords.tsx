'use client'
import Link from 'next/link'
import { useEffect, useEffectEvent, useRef, useState } from 'react'
import { Booking, Jurisdiction, bondLabel } from './types'

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
  const generation = useRef(0)
  const resultsController = useRef<AbortController | null>(null)
  const selectedQuery = useRef({ name: '', state: '', county: '' })
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
      if (!response.ok) throw new Error(response.status === 429 ? 'Too many searches. Please wait a minute.' : 'Search is unavailable. Please try again later.')
      const data = await response.json()
      if (current !== generation.current) return
      setItems(data.items); setPage(nextPage); setMore(data.has_more)
      setMessage(data.items.length ? `${data.items.length} bookings on page ${nextPage}. Similar names may belong to different people.` : 'No currently publishable matches on this page. Coverage is limited to participating sources.')
    } catch (error) {
      if (current === generation.current && !controller.signal.aborted) setMessage(error instanceof Error ? error.message : 'Search failed.')
    } finally { if (current === generation.current) setLoading(false) }
  }

  const field = 'mt-1 w-full rounded-md border border-slate-400 bg-white p-3 text-slate-950 focus:outline-2 focus:outline-blue-700'
  return <section>
    <form onSubmit={event => { event.preventDefault(); void search() }} className="grid items-end gap-4 rounded-xl border border-slate-300 bg-slate-50 p-5 sm:grid-cols-4">
      <div className="relative sm:col-span-2">
        <label htmlFor="record-name" className="font-semibold">First or last name</label>
        <input id="record-name" className={field} value={name} minLength={2} maxLength={100} required autoComplete="off"
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
        <ul id="name-options" role="listbox" aria-label="Suggested booking names" hidden={!open || !suggestions.length} className="absolute z-10 w-full rounded border border-slate-300 bg-white text-slate-950 shadow-lg">
          {suggestions.map((item, index) => <li key={item.id} id={`name-option-${index}`} role="option" aria-selected={index === active}
            className={`cursor-pointer p-3 ${index === active ? 'bg-blue-100' : ''}`}
            onMouseDown={event => { event.preventDefault(); setName(`${item.first_name} ${item.last_name}`); setOpen(false); setActive(-1) }}>
            {item.first_name} {item.last_name} — {item.county}, {item.state}
          </li>)}
        </ul>
      </div>
      <label className="font-semibold">State<select className={field} value={state} onChange={event => { setState(event.target.value); setCounty(''); setSuggestions([]); setActive(-1) }}>
        <option value="">All supported states</option>{state && !jurisdictions.some(j => j.state === state) && <option value={state}>{state} (coverage unconfirmed)</option>}{[...new Set(jurisdictions.map(j => j.state))].map(value => <option key={value}>{value}</option>)}
      </select></label>
      <label className="font-semibold">County<select className={field} value={county} onChange={event => { setCounty(event.target.value); setSuggestions([]); setActive(-1) }}>
        <option value="">All supported counties</option>{county && !jurisdictions.some(j => j.county === county && (!state || j.state === state)) && <option value={county}>{county} (coverage unconfirmed)</option>}{[...new Set(jurisdictions.filter(j => !state || j.state === state).map(j => j.county))].map(value => <option key={value}>{value}</option>)}
      </select></label>
      <button disabled={loading} className="rounded-md bg-blue-800 px-6 py-3 font-semibold text-white disabled:opacity-50 sm:col-span-4">{loading ? 'Searching…' : 'Search public records'}</button>
    </form>
    <p role="status" aria-live="polite" className="my-5">{message}</p>
    {items.length > 0 && <div className="overflow-x-auto"><table className="w-full border-collapse text-left">
      <caption className="sr-only">Booking search results</caption>
      <thead><tr>{['Name', 'County', 'Charges', 'Bond amount and status'].map(label => <th scope="col" className="border-b p-3" key={label}>{label}</th>)}</tr></thead>
      <tbody>{items.map(item => <tr key={item.id} className="border-b border-slate-300">
        <td className="p-3"><Link className="font-semibold text-blue-700 underline" href={`/inmate/${item.id}`}>{item.first_name} {item.last_name}</Link></td>
        <td className="p-3">{item.county}, {item.state}</td>
        <td className="p-3">{item.charges.map(c => c.description).join('; ') || 'Not provided'}</td>
        <td className="p-3">{item.bonds.map(bondLabel).join('; ') || 'Not provided'}</td>
      </tr>)}</tbody>
    </table></div>}
    <div className="my-5 flex gap-5">
      {page > 1 && <button className="underline" disabled={loading} onClick={() => void search(page - 1)}>Previous page</button>}
      {more && <button className="underline" disabled={loading} onClick={() => void search(page + 1)}>Next page</button>}
    </div>
  </section>
}
