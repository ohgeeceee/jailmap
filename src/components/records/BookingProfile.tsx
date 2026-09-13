'use client'
import { useEffect, useState } from 'react'
import { Booking, bondLabel } from './types'
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
    <p role="status">{message}</p>
    {booking && <article>
      <h1 className="text-3xl font-bold">{booking.first_name} {booking.last_name}</h1>
      <p className="mt-3">{booking.facility_name} · {booking.county}, {booking.state}</p>
      {booking.source_note && <p className="mt-3 text-sm text-slate-600">{booking.source_note}</p>}
      <dl className="my-6 grid gap-3 sm:grid-cols-2">
        <div><dt className="font-semibold">Booking number</dt><dd>{booking.booking_number}</dd></div>
        <div><dt className="font-semibold">{booking.booking_date_precision === 'date' ? 'Booking date (source local date)' : 'Booked (UTC)'}</dt><dd>{booking.booking_date_precision === 'date' ? new Intl.DateTimeFormat('en-US', { timeZone: booking.booking_timezone || 'UTC', dateStyle: 'long' }).format(new Date(booking.booking_date)) : new Date(booking.booking_date).toISOString()}</dd></div>
        <div><dt className="font-semibold">Last observed (UTC)</dt><dd>{new Date(booking.observed_at).toISOString()}</dd></div>
        <div><dt className="font-semibold">Source</dt><dd><a className="text-blue-700 underline" href={booking.source_url} rel="noreferrer" target="_blank">Official or authorized source</a></dd></div>
      </dl>
      <h2 className="mt-6 text-xl font-semibold">Reported charges</h2>
      <ul className="my-3 space-y-2">{booking.charges.map((charge, i) => <li key={i}>{charge.description} — {charge.statute || 'Statute not provided'} · {charge.severity || 'Severity not provided'}</li>)}</ul>
      {!booking.charges.length && <p>Charges not provided.</p>}
      <h2 className="mt-6 text-xl font-semibold">Reported bonds</h2>
      <ul className="my-3 space-y-2">{booking.bonds.map((bond, i) => <li key={i}>{bondLabel(bond)}</li>)}</ul>
      {!booking.bonds.length && <p>Bond information not provided.</p>}
    </article>}
    <section className="mt-10 border-t pt-6">
      <h2 className="text-xl font-semibold">Request a correction or removal</h2>
      <p className="my-3">Requests are free and reviewed by a person. Do not include a Social Security number, full DOB, or identity documents.</p>
      <form className="grid gap-4" onSubmit={async event => {
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
        <label>Email for follow-up<input className="mt-1 block w-full rounded border p-3" type="email" name="email" required maxLength={254} autoComplete="email" /></label>
        <label>Request type<select className="mt-1 block w-full rounded border bg-white p-3 text-slate-950" name="kind"><option value="correction">Correction</option><option value="removal">Removal</option></select></label>
        <label>Describe the issue<textarea className="mt-1 block w-full rounded border p-3" name="reason" required minLength={20} maxLength={4000} rows={4} /></label>
        <button disabled={sending} className="rounded bg-blue-800 p-3 font-semibold text-white disabled:opacity-50">Submit for review</button>
      </form>
      <p role="status" className="mt-3">{requestMessage}</p>
    </section>
  </>
}
