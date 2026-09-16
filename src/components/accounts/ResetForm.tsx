'use client'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { ArrowRight, Eye, EyeOff } from 'lucide-react'
export function ResetForm({ token }: { token: string | null }) {
  const router = useRouter()
  const [visible, setVisible] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState('')
  return <form className="account-form" onSubmit={async event => {
    event.preventDefault(); setBusy(true); setError('')
    const form = new FormData(event.currentTarget)
    const password = String(form.get('password') || ''), confirm = String(form.get('confirm') || '')
    if (password !== confirm) { setError('Passwords do not match.'); setBusy(false); return }
    if (!token) { setError('This reset link is missing its token. Please request a new one.'); setBusy(false); return }
    try {
      const response = await fetch('/api/account/password/reset', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ token, password }) })
      const result = await response.json(); if (!response.ok) throw new Error(result.error || 'Please try again.')
      router.push('/login'); router.refresh()
    } catch (error) { setError(error instanceof Error ? error.message : 'Unable to connect. Please try again.'); setBusy(false) }
  }}>
    <label>New password<div className="password-field"><input name="password" type={visible ? 'text' : 'password'} autoComplete="new-password" placeholder="Choose a strong passphrase" minLength={15} maxLength={128} required aria-describedby="reset-hint" /><button type="button" aria-label={visible ? 'Hide password' : 'Show password'} aria-pressed={visible} onClick={() => setVisible(!visible)}>{visible ? <EyeOff size={18} /> : <Eye size={18} />}</button></div></label>
    <p id="reset-hint" className="field-hint">Use 15–128 characters. A few unrelated words make a memorable passphrase.</p>
    <label>Confirm password<input name="confirm" type={visible ? 'text' : 'password'} autoComplete="new-password" placeholder="Repeat your passphrase" minLength={15} maxLength={128} required /></label>
    {error && <p className="form-error" role="alert">{error}</p>}
    <button className="jm-button full" disabled={busy}>{busy ? 'Please wait…' : 'Set new password'}{!busy && <ArrowRight size={18} />}</button>
    <p className="auth-switch"><Link href="/forgot">Request a fresh link</Link></p>
  </form>
}