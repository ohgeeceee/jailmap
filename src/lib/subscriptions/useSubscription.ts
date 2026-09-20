'use client'

import { useState, useEffect, useCallback } from 'react'

export type Tier = 'free' | 'basic' | 'pro' | 'developer' | 'enterprise'
export type SubscriptionStatus = 'active' | 'inactive' | 'cancelled' | 'past_due'

export interface Subscription {
  tier: Tier
  status: SubscriptionStatus
  api_requests_this_period: number
  current_period_end: number | null
}

const TIER_HIERARCHY: Record<Tier, number> = { free: 0, basic: 1, pro: 2, developer: 3, enterprise: 4 }

export function hasTierAccess(accountTier: Tier, requiredTier: Tier): boolean {
  return TIER_HIERARCHY[accountTier] >= TIER_HIERARCHY[requiredTier]
}

export function useSubscription() {
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch('/api/subscriptions/status')
      if (!response.ok) throw new Error('Failed to fetch subscription')
      const data = await response.json()
      setSubscription(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load subscription')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchStatus() }, [fetchStatus])

  const canAccess = useCallback((requiredTier: Tier): boolean => {
    if (!subscription) return false
    if (subscription.status !== 'active') return false
    return hasTierAccess(subscription.tier, requiredTier)
  }, [subscription])

  return { subscription, loading, error, canAccess, refresh: fetchStatus }
}
