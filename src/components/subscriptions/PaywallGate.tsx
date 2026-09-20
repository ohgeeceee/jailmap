'use client'

import { useSubscription, Tier } from '@/lib/subscriptions/useSubscription'
import Link from 'next/link'
import { Lock } from 'lucide-react'

interface PaywallGateProps {
  requiredTier: Tier
  children: React.ReactNode
  fallback?: React.ReactNode
}

export function PaywallGate({ requiredTier, children, fallback }: PaywallGateProps) {
  const { subscription, loading, canAccess } = useSubscription()

  if (loading) {
    return (
      <div style={{ padding: '32px', textAlign: 'center', color: 'var(--jm-text-secondary)' }}>
        Loading...
      </div>
    )
  }

  if (canAccess(requiredTier)) {
    return <>{children}</>
  }

  if (fallback) {
    return <>{fallback}</>
  }

  const tierLabels: Record<Tier, string> = {
    free: 'Free',
    basic: 'Basic',
    pro: 'Pro',
    developer: 'Developer',
    enterprise: 'Enterprise',
  }

  return (
    <div className="paywall-gate" style={{
      padding: '32px',
      textAlign: 'center',
      background: 'var(--jm-bg-secondary)',
      borderRadius: 12,
      border: '1px solid var(--jm-border)',
    }}>
      <Lock size={32} style={{ margin: '0 auto 16px', color: 'var(--jm-text-secondary)' }} />
      <h3 style={{ margin: '0 0 8px' }}>Upgrade to {tierLabels[requiredTier]}</h3>
      <p style={{ margin: '0 0 16px', color: 'var(--jm-text-secondary)' }}>
        This feature requires a {tierLabels[requiredTier]} subscription or higher.
      </p>
      <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
        <Link href="/pricing" className="jm-button">View plans</Link>
        <Link href={`/checkout?tier=${requiredTier}`} className="jm-button secondary">
          Subscribe
        </Link>
      </div>
    </div>
  )
}
