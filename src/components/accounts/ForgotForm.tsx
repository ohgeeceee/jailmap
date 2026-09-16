'use client'
import Link from 'next/link'
import { useState } from 'react'
import { ArrowRight } from 'lucide-react'
export function ForgotForm() {
  const [busy, setBusy] = useState(false), [done, setDone] = useState(false), [error, setError] = useState('')
  return <form className="account-form" onSubmit={async event => {
    event.preventDefault(); setBusy(true); setError('')
    const form = new FormData(event.currentTarget)
    try {
      const response = await fetch('/api/account/password/forgot', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ email: form.get('email') }) })
      const result = await response.json(); if (!response.ok) throw new Error(result.error || 'Please try again.')
      setDone(true)
    } catch (error) { setError(error instanceof Error ? error.message : 'Unable to connect. Please try again.'); setBusy(false) }
  }}>
    {done ? <p className="auth-note">If an account exists for that address, we've emailed a password reset link. It expires in one hour.</p> : <>
      <label>Email address<input name="email" type="email" autoComplete="email" placeholder="you@example.com" maxLength={254} required /></label>
      {error && <p className="form-error" role="alert">{error}</p>}
      <button className="jm-button full" disabled={busy}>{busy ? 'Please wait…' : 'Send reset link'}{!busy && <ArrowRight size={18} />}</button>
      <p className="auth-switch">Remembered it? <Link href="/login">Back to log in</Link></p>
    </>}
  </form>
}