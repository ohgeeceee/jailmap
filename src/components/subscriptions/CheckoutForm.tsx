'use client'

import { useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { ArrowRight, Loader2 } from 'lucide-react'

const TIERS = {
  basic: { name: 'Basic Search / Alerts', price: '$9.99', period: '/mo', annualPrice: '$79.99/yr' },
  pro: { name: 'Pro / Investigator', price: '$49', period: '/mo', annualPrice: '$392/yr' },
  developer: { name: 'Developer API (Starter)', price: '$149', period: '/mo', annualPrice: '$1,192/yr' },
  enterprise: { name: 'Enterprise / Data Stream', price: '$499', period: '/mo', annualPrice: '$3,992/yr' },
}

export function CheckoutForm() {
  const searchParams = useSearchParams()
  const tierParam = searchParams.get('tier') as keyof typeof TIERS | null
  const [tier, setTier] = useState<keyof typeof TIERS>(tierParam && TIERS[tierParam] ? tierParam : 'basic')
  const [annual, setAnnual] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleCheckout = async () => {
    setLoading(true); setError('')
    try {
      const response = await fetch('/api/subscriptions/checkout', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ tier, annual }) })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Checkout failed')
      if (data.checkout_url) window.location.href = data.checkout_url
    } catch (err) { setError(err instanceof Error ? err.message : 'Checkout failed') }
    finally { setLoading(false) }
  }

  return <div className="panel" style={{ maxWidth: 600, margin: '0 auto' }}><div className="panel-content">
    <div className="form-two"><label>Tier<select value={tier} onChange={event => setTier(event.target.value as keyof typeof TIERS)}>{Object.entries(TIERS).map(([id, item]) => <option key={id} value={id}>{item.name} — {item.price}{item.period}</option>)}</select></label><label>Billing<select value={annual ? 'annual' : 'monthly'} onChange={event => setAnnual(event.target.value === 'annual')}><option value="monthly">Monthly</option><option value="annual">Annual (20% off)</option></select></label></div>
    <div style={{ marginBlock: '24px', padding: '16px', background: 'var(--jm-bg-secondary)', borderRadius: 8 }}><div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}><div><strong>{TIERS[tier].name}</strong><p style={{ margin: '4px 0 0', color: 'var(--jm-text-secondary)' }}>{annual ? TIERS[tier].annualPrice : `${TIERS[tier].price}${TIERS[tier].period}`}</p></div><div style={{ textAlign: 'right' }}><span style={{ fontSize: '1.5rem', fontWeight: 700 }}>{annual ? TIERS[tier].annualPrice : TIERS[tier].price}</span><span style={{ color: 'var(--jm-text-secondary)' }}>{annual ? '/year' : TIERS[tier].period}</span></div></div></div>
    {error && <p className="form-error">{error}</p>}
    <button className="jm-button full" onClick={handleCheckout} disabled={loading}>{loading ? <Loader2 size={16} className="animate-spin" /> : <ArrowRight size={16} />}{loading ? 'Redirecting...' : 'Continue to payment'}</button>
    <p style={{ marginTop: '16px', fontSize: '0.85rem', color: 'var(--jm-text-secondary)', textAlign: 'center' }}>Secure payment via Stripe. Cancel anytime.</p>
  </div></div>
}
