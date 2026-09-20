'use client'

import { useEffect, useState } from 'react'
import { RefreshCw, ShieldCheck, Stamp } from 'lucide-react'
import { SearchRecords } from './SearchRecords'

type SealMark = { id: string; glyph: string; label: string }
type Challenge = { id: string; target: Omit<SealMark, 'id'>; options: SealMark[]; expiresAt: number }

export function SearchGate({ initial }: { initial: { name: string; state: string; county: string } }) {
  const [challenge, setChallenge] = useState<Challenge | null>(null)
  const [answer, setAnswer] = useState('')
  const [message, setMessage] = useState('Preparing a quick seal check…')
  const [verified, setVerified] = useState(false)
  const [busy, setBusy] = useState(false)

  async function loadChallenge() {
    setBusy(true); setAnswer(''); setMessage('Preparing a new seal…')
    try { const response = await fetch('/api/route-check', { cache: 'no-store' }); const data = await response.json(); if (!response.ok) throw new Error(data.error || 'Seal Check unavailable.'); setChallenge(data); setMessage('') }
    catch (error) { setChallenge(null); setMessage(error instanceof Error ? error.message : 'Seal Check unavailable.') }
    finally { setBusy(false) }
  }

  useEffect(() => {
    let active = true
    fetch('/api/route-check', { cache: 'no-store' }).then(async response => {
      const data = await response.json()
      if (!response.ok) throw new Error(data.error || 'Seal Check unavailable.')
      if (active) { setChallenge(data); setMessage('') }
    }).catch(error => { if (active) setMessage(error instanceof Error ? error.message : 'Seal Check unavailable.') })
    return () => { active = false }
  }, [])
  if (verified) return <SearchRecords initial={initial} />
  return <section className="route-check" aria-labelledby="route-check-title">
    <div className="route-check-heading"><span className="route-check-stamp"><Stamp size={24} /></span><div><span className="eyebrow">HUMAN CHECK</span><h2 id="route-check-title">Match the seal</h2><p>Pick the mark that matches the sample. One quick check keeps automated traffic from crowding out public access.</p></div></div>
    {challenge && <form onSubmit={async event => { event.preventDefault(); if (!answer) return; setBusy(true); setMessage('Checking the seal…'); try { const response = await fetch('/api/route-check', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ id: challenge.id, answer }) }); const data = await response.json(); if (!response.ok) throw new Error(data.error || 'That mark did not match.'); setVerified(true) } catch (error) { setMessage(error instanceof Error ? error.message : 'Seal Check failed.'); await loadChallenge() } finally { setBusy(false) } }}>
      <div className="seal-sample" aria-label={`Sample mark: ${challenge.target.label}`}><span aria-hidden="true">{challenge.target.glyph}</span><small>Match this mark</small></div>
      <fieldset><legend>Choose the identical mark</legend><div className="route-options">{challenge.options.map(option => <label key={option.id} className={answer === option.id ? 'selected' : ''}><input type="radio" name="seal-mark" value={option.id} checked={answer === option.id} onChange={() => setAnswer(option.id)} /><span className="seal-option-glyph" aria-hidden="true">{option.glyph}</span><span className="sr-only">{option.label}</span></label>)}</div></fieldset>
      <div className="route-check-actions"><button className="jm-button" disabled={!answer || busy}><ShieldCheck size={16} />{busy ? 'Checking…' : 'Continue to search'}</button><button className="text-link" type="button" onClick={() => void loadChallenge()} disabled={busy}><RefreshCw size={14} />Different seal</button></div>
    </form>}
    {message && <p className="route-check-status" role="status">{message}</p>}
    <p className="route-check-privacy">Private by design: no tracking, image recognition, or third-party CAPTCHA service. Access expires after 15 minutes.</p>
  </section>
}
