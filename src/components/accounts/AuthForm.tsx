'use client'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { ArrowRight, Eye, EyeOff } from 'lucide-react'
export function AuthForm({ mode }: { mode: 'login' | 'register' }) {
  const register = mode === 'register', router = useRouter()
  const [visible, setVisible] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState('')
  return <form className="account-form" onSubmit={async event => {
    event.preventDefault(); setBusy(true); setError('')
    const form = new FormData(event.currentTarget)
    try {
      const response = await fetch(`/api/account/${mode}`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ name: form.get('name'), email: form.get('email'), password: form.get('password'), accepted: form.get('accepted') === 'on' }) })
      const result = await response.json(); if (!response.ok) throw new Error(result.error || 'Please try again.')
      router.push(result.user.role === 'admin' ? '/admin' : '/dashboard'); router.refresh()
    } catch (error) { setError(error instanceof Error ? error.message : 'Unable to connect. Please try again.'); setBusy(false) }
  }}>
    {register && <label>Full name<input name="name" autoComplete="name" placeholder="Your name" minLength={2} maxLength={80} required /></label>}
    <label>Email address<input name="email" type="email" autoComplete="email" placeholder="you@example.com" maxLength={254} required /></label>
    <label>Password<div className="password-field"><input name="password" type={visible ? 'text' : 'password'} autoComplete={register ? 'new-password' : 'current-password'} placeholder={register ? 'Choose a strong passphrase' : 'Enter your password'} minLength={register ? 15 : 1} maxLength={128} required aria-describedby={register ? 'password-hint' : undefined} /><button type="button" aria-label={visible ? 'Hide password' : 'Show password'} aria-pressed={visible} onClick={() => setVisible(!visible)}>{visible ? <EyeOff size={18} /> : <Eye size={18} />}</button></div></label>
    {register && <><p id="password-hint" className="field-hint">Use 15–128 characters. A few unrelated words make a memorable passphrase.</p><label className="checkbox-label"><input type="checkbox" name="accepted" required /><span>I agree to the <Link href="/terms">responsible-use terms</Link> and have read the <Link href="/privacy">privacy notice</Link>.</span></label></>}
    {error && <p className="form-error" role="alert">{error}</p>}
    <button className="jm-button full" disabled={busy}>{busy ? 'Please wait…' : register ? 'Create account' : 'Log in'}{!busy && <ArrowRight size={18} />}</button>
    <p className="auth-switch">{register ? 'Already have an account?' : 'New to JailMap?'} <Link href={register ? '/login' : '/register'}>{register ? 'Log in' : 'Create an account'}</Link></p>
  </form>
}
