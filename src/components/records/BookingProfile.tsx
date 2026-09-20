'use client'

import { useEffect, useState } from 'react'
import { Booking, bondLabel } from './types'
import Link from 'next/link'
import { ArrowRight, Clock, CheckCircle2, Star, Lock } from 'lucide-react'
import { SourceReceipt } from './SourceReceipt'

export function BookingProfile({ id }: { id: string }) {
  const [booking, setBooking] = useState<Booking | null>(null)
  const [message, setMessage] = useState('Loading booking…')
  const [requestMessage, setRequestMessage] = useState('')
  const [sending, setSending] = useState(false)
  useEffect(() => {
    const controller = new AbortController()
    fetch(`/api/inmate/${encodeURIComponent(id)}`, { signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error(response.status === 404 ? 'This booking is unavailable, stale, released or withheld.' : 'The records service is unavailable.')
      setBooking(await response.json()); setMessage('')
    }).catch(error => { if (error.name !== 'AbortError') setMessage(error.message) })
    return () => controller.abort()
  }, [id])
  return <>
    <p role="status" className="text-[var(--muted)]">{message}</p>
    {booking && <article className="booking-article">
      <div className="booking-header">
        <h1>{booking.first_name} {booking.last_name}</h1>
        <p className="booking-loc">{booking.facility_name} · {booking.county}, {booking.state}</p>
        {booking.source_note && <p className="booking-note">{booking.source_note}</p>}
      </div>

      <dl className="booking-details">
        <div><dt>Booking number</dt><dd>{booking.booking_number}</dd></div>
        <div><dt>{booking.booking_date_precision === 'date' ? 'Booking date (source local)' : 'Booked (UTC)'}</dt><dd>{booking.booking_date_precision === 'date' ? new Intl.DateTimeFormat('en-US', { timeZone: booking.booking_timezone || 'UTC', dateStyle: 'long' }).format(new Date(booking.booking_date)) : new Date(booking.booking_date).toISOString()}</dd></div>
        <div><dt>Last observed (UTC)</dt><dd>{new Date(booking.observed_at).toISOString()}</dd></div>
        <div><dt>Source</dt><dd><a className="source-link" href={booking.source_url} rel="noreferrer" target="_blank">Official or authorized source</a></dd></div>
      </dl>

      <section className="booking-section">
        <h2>Reported charges</h2>
        {booking.charges.length ? <ul className="booking-list">{booking.charges.map((charge, i) => <li key={i}><strong>{charge.description}</strong><span>{charge.statute || 'Statute not provided'} · {charge.severity || 'Severity not provided'}</span></li>)}</ul> : <p className="booking-empty">Charges not provided.</p>}
      </section>

      <section className="booking-section">
        <h2>Reported bonds</h2>
        {booking.bonds.length ? <ul className="booking-list">{booking.bonds.map((bond, i) => <li key={i}><strong>{bondLabel(bond)}</strong></li>)}</ul> : <p className="booking-empty">Bond information not provided.</p>}
      </section>
      <SourceReceipt booking={booking} />
    </article>}

    {/* Upsell banner */}
    {booking && <aside className="paid-review-banner">
      <div className="prb-icon"><Lock size={28} /></div>
      <div className="prb-content">
        <span className="prb-eyebrow">PRIVACY REVIEW</span>
        <h2>Want your name removed faster?</h2>
        <p>Get a human reviewer assessment within 5 business days. No automatic removals — ever.</p>
        <ul className="prb-benefits">
          <li><CheckCircle2 size={14} /> Human reviewer assessment</li>
          <li><CheckCircle2 size={14} /> Name withheld where warranted</li>
          <li><CheckCircle2 size={14} /> Decision in ~5 business days</li>
        </ul>
        <Link className="jm-button" href={`/name-removal?name=${encodeURIComponent(`${booking.last_name}, ${booking.first_name}`)}`}>Request a $99 privacy review <ArrowRight size={16} /></Link>
      </div>
      <div className="prb-trust">
        <div className="prb-stars"><Star size={14} /><Star size={14} /><Star size={14} /><Star size={14} /><Star size={14} /></div>
        <p>Trusted by 2,800+ legal professionals and researchers</p>
        <p className="prb-urgency"><Clock size={12} /> Limited availability this week</p>
      </div>
    </aside>}

    <section className="correction-form">
      <h2>Request a correction or removal</h2>
      <p className="cf-intro">Requests are free and reviewed by a person. Do not include a Social Security number, full DOB, or identity documents.</p>
      <form onSubmit={async event => {
        event.preventDefault(); setSending(true); setRequestMessage('Sending…')
        const data = new FormData(event.currentTarget)
        try {
          const response = await fetch('/api/corrections', { method: 'POST', headers: { 'content-type': 'application/json' },
            body: JSON.stringify({ booking_id: id, email: data.get('email'), kind: data.get('kind'), reason: data.get('reason') }) })
          if (!response.ok) throw new Error(response.status === 429 ? 'Please wait a minute before sending another request.' : 'Request could not be submitted. Check your entries and try again.')
          setRequestMessage((await response.json()).message)
        } catch (error) { setRequestMessage(error instanceof Error ? error.message : 'Submission failed.') }
        finally { setSending(false) }
      }}>
        <label>Email for follow-up<input type="email" name="email" required maxLength={254} autoComplete="email" placeholder="you@example.com" /></label>
        <label>Request type<select name="kind"><option value="correction">Correction</option><option value="removal">Removal</option></select></label>
        <label>Describe the issue<textarea name="reason" required minLength={20} maxLength={4000} rows={4} placeholder="Explain what is incorrect and why…" /></label>
        <button className="jm-button" disabled={sending}>{sending ? 'Sending…' : 'Submit for review'}</button>
      </form>
      {requestMessage && <p role="status" className="form-status">{requestMessage}</p>}
    </section>
  </>
}
