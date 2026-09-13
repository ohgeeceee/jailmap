'use client'
import { useEffect, useState } from 'react'

const FEE_LABEL = '$99'

export function NameRemovalForm({ prefilledName }: { prefilledName?: string }) {
  const [status, setStatus] = useState<'idle' | 'creating'>('idle')
  const [message, setMessage] = useState('')

  async function startCheckout(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setStatus('creating'); setMessage('')
    const data = new FormData(event.currentTarget)
    try {
      const response = await fetch('/api/name-removal/checkout', {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ email: String(data.get('email') || ''), person_name: String(data.get('person_name') || '') }),
      })
      if (!response.ok) throw new Error(response.status === 429 ? 'Please wait a minute and try again.' : 'Could not start checkout. Please try again.')
      const payload = await response.json()
      if (!payload.checkout_url) throw new Error('Checkout unavailable.')
      window.location.assign(payload.checkout_url)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Something went wrong.')
      setStatus('idle')
    }
  }

  return (
    <form className="grid gap-4" onSubmit={startCheckout}>
      <label className="block text-sm font-medium">
        Your name (as it appears on the record)
        <input className="mt-1 block w-full rounded border border-[var(--line)] p-3" name="person_name" required maxLength={120} defaultValue={prefilledName} placeholder="Last, First M" />
      </label>
      <label className="block text-sm font-medium">
        Email for the receipt and review updates
        <input className="mt-1 block w-full rounded border border-[var(--line)] p-3" type="email" name="email" required maxLength={254} autoComplete="email" />
      </label>
      <button disabled={status === 'creating'}
        className="rounded bg-[var(--green)] p-3 font-semibold text-white disabled:opacity-50">
        {status === 'creating' ? 'Redirecting to secure checkout…' : `Continue to secure checkout · ${FEE_LABEL}`}
      </button>
      <p role="status" className="text-sm text-[var(--muted)]">{message}</p>
    </form>
  )
}

export function CheckoutSuccess() {
  const [state, setState] = useState<'checking' | 'paid' | 'unpaid' | 'error'>('checking')
  useEffect(() => {
    const sessionId = new URLSearchParams(window.location.search).get('session_id')
    if (!sessionId) { setState('error'); return }
    fetch(`/api/name-removal/session/${encodeURIComponent(sessionId)}`).then(async response => {
      if (!response.ok) throw new Error()
      const data = await response.json()
      setState(data.payment_status === 'paid' ? 'paid' : 'unpaid')
    }).catch(() => setState('error'))
  }, [])
  if (state === 'paid') {
    return <p className="rounded border border-[var(--line)] bg-white p-4">Payment received. Your request now enters human review — approved requests have the name redacted from public pages. You will be contacted at the email you provided.</p>
  }
  if (state === 'unpaid') return <p className="rounded border border-[var(--line)] bg-white p-4">Payment has not completed yet. If you just paid, refresh this page in a moment.</p>
  if (state === 'error') return <p className="rounded border border-[var(--line)] bg-white p-4">We could not verify this checkout session. If you completed payment, contact us with your receipt email.</p>
  return <p className="rounded border border-[var(--line)] bg-white p-4">Verifying your payment…</p>
}
