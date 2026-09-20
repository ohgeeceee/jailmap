'use client'

import { useEffect, useMemo, useState } from 'react'
import { Check, Clipboard, ExternalLink, Fingerprint, Info, ShieldCheck } from 'lucide-react'
import type { Booking } from './types'
import { canonicalPublicRecord, observationAge, receiptCompleteness } from '@/lib/records/source-receipt'

export function SourceReceipt({ booking }: { booking: Booking }) {
  const [fingerprint, setFingerprint] = useState('Preparing…')
  const [copied, setCopied] = useState(false)
  const completeness = useMemo(() => receiptCompleteness(booking), [booking])
  const sourceHost = useMemo(() => { try { return new URL(booking.source_url).hostname } catch { return 'Official source' } }, [booking.source_url])

  useEffect(() => {
    let active = true
    crypto.subtle.digest('SHA-256', new TextEncoder().encode(canonicalPublicRecord(booking)))
      .then(buffer => Array.from(new Uint8Array(buffer)).map(byte => byte.toString(16).padStart(2, '0')).join(''))
      .then(value => { if (active) setFingerprint(value.slice(0, 20)) })
      .catch(() => { if (active) setFingerprint('Unavailable') })
    return () => { active = false }
  }, [booking])

  const receiptText = [
    'JailMap Source Receipt',
    `Record: ${booking.booking_number}`,
    `Facility: ${booking.facility_name}, ${booking.county}, ${booking.state}`,
    `Observed: ${new Date(booking.observed_at).toISOString()}`,
    `Source: ${booking.source_url}`,
    `Charges: ${booking.charges.length} (${completeness.charges})`,
    `Bonds: ${booking.bonds.length} (${completeness.bonds})`,
    `Public projection fingerprint: ${fingerprint}`,
    'A booking is not a conviction. Verify with the official source.',
  ].join('\n')

  return <section className="source-receipt" aria-labelledby="source-receipt-title">
    <div className="receipt-heading"><div className="receipt-icon"><Fingerprint size={22} /></div><div><span className="eyebrow">PUBLIC PROVENANCE</span><h2 id="source-receipt-title">Source Receipt</h2><p>A plain-language receipt for what this source supplied—and what it did not.</p></div></div>
    <div className="receipt-grid">
      <div><span>Source</span><strong>{sourceHost}</strong><a href={booking.source_url} target="_blank" rel="noreferrer">Open official record <ExternalLink size={12} /></a></div>
      <div><span>Observation</span><strong>{observationAge(booking.observed_at)}</strong><small>{new Date(booking.observed_at).toISOString()}</small></div>
      <div><span>Categories supplied</span><strong>{booking.charges.length} charge{booking.charges.length === 1 ? '' : 's'} · {booking.bonds.length} bond{booking.bonds.length === 1 ? '' : 's'}</strong><small>Statutes: {completeness.statutes}</small></div>
      <div><span>Change fingerprint</span><strong className="receipt-hash">{fingerprint}</strong><small>Changes when the public record content changes</small></div>
    </div>
    <div className="receipt-note"><Info size={16} /><p>“Not supplied” does not mean “none.” This fingerprint detects changes; it does not prove the record is correct or establish identity.</p></div>
    <div className="receipt-actions"><span><ShieldCheck size={15} /> Source-linked · privacy-filtered</span><button type="button" className="jm-button secondary compact" disabled={fingerprint === 'Preparing…'} onClick={async () => { try { await navigator.clipboard.writeText(receiptText); setCopied(true); window.setTimeout(() => setCopied(false), 2000) } catch { setCopied(false) } }}>{copied ? <Check size={15} /> : <Clipboard size={15} />}{copied ? 'Copied' : 'Copy receipt'}</button></div>
  </section>
}
