'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { LogOut } from 'lucide-react'
export function SignOut() {
  const router = useRouter(); const [busy, setBusy] = useState(false); const [error, setError] = useState('')
  return <div><button className="side-signout" disabled={busy} onClick={async () => {
    setBusy(true); setError('')
    try { const response = await fetch('/api/account/logout', { method: 'POST' }); if (!response.ok) throw new Error(); router.push('/login'); router.refresh() }
    catch { setError('Sign out failed. Try again.'); setBusy(false) }
  }}><LogOut size={17} />{busy ? 'Signing out…' : 'Sign out'}</button>{error && <p role="alert" className="form-error">{error}</p>}</div>
}
