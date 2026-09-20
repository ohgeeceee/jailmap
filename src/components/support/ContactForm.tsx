'use client'

import { useState } from 'react'
import { Send } from 'lucide-react'

export function ContactForm() {
  const [state, setState] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')
  const [message, setMessage] = useState('')
  return <form className="support-form" onSubmit={async event => {
    event.preventDefault(); setState('sending'); const form = event.currentTarget
    try {
      const response = await fetch('/api/support', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(Object.fromEntries(new FormData(form))) })
      const result = await response.json(); if (!response.ok) throw new Error(result.error || 'Your message could not be sent.')
      form.reset(); setState('sent'); setMessage('Thanks — your support ticket is in our inbox. We usually reply within 1–2 business days.')
    } catch (error) { setState('error'); setMessage(error instanceof Error ? error.message : 'Your message could not be sent.') }
  }}>
    <div className="form-two"><label>Name<input name="name" minLength={2} maxLength={80} autoComplete="name" required /></label><label>Email<input name="email" type="email" maxLength={254} autoComplete="email" required /></label></div>
    <label>Subject<input name="subject" minLength={3} maxLength={140} required /></label>
    <label>How can we help?<textarea name="message" minLength={10} maxLength={5000} rows={7} required /></label>
    <div className="support-form-actions"><button className="jm-button" disabled={state === 'sending'}>{state === 'sending' ? 'Sending…' : <>Send message <Send size={16} /></>}</button><span className="field-hint">Please do not include SSNs, full birth dates, or identity documents.</span></div>
    {message && <p className={state === 'sent' ? 'form-success' : 'form-error'} role="status">{message}</p>}
  </form>
}
