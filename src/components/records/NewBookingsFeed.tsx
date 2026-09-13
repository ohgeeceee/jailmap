'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import Link from 'next/link'
import { ShieldCheck, Activity, Radio, ArrowRight } from 'lucide-react'

type NewBooking = {
  id: string
  first_name: string
  last_name: string
  booking_date: string
  state: string
  county: string
  facility_name: string
}

function timeAgo(iso: string): string {
  const then = new Date(iso).getTime()
  const now = Date.now()
  const diff = Math.max(0, now - then)
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  return `${days}d ago`
}

function initialState(): { items: NewBooking[]; fresh: number[] } {
  return { items: [], fresh: [] }
}

export function NewBookingsFeed() {
  const [state, setState] = useState<{ items: NewBooking[]; fresh: number[] }>(initialState)
  const [loading, setLoading] = useState(true)
  const [count, setCount] = useState(0)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const lastIdsRef = useRef<Set<string>>(new Set())

  const fetchFeed = useCallback(async () => {
    try {
      const response = await fetch('/api/new-bookings?limit=50')
      if (!response.ok) throw new Error('feed unavailable')
      const data = await response.json()
      const items: NewBooking[] = data.items || []
      const now = Date.now()
      const freshIds: number[] = []
      const knownIds = lastIdsRef.current
      items.forEach((item, idx) => {
        if (!knownIds.has(item.id)) {
          const age = now - new Date(item.booking_date).getTime()
          if (age < 3600_000) freshIds.push(idx)
        }
      })
      lastIdsRef.current = new Set(items.map(i => i.id))
      setState({ items, fresh: freshIds })
      setCount(prev => Math.max(prev, items.length))
      setLoading(false)
    } catch {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void fetchFeed()
    pollRef.current = setInterval(() => void fetchFeed(), 15000)
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [fetchFeed])

  useEffect(() => {
    const timer = setInterval(() => setState(s => ({ ...s })), 30000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="new-bookings">
      <div className="new-bookings__status-bar">
        <div className="status-indicator">
          <Radio size={14} className="status-dot pulse" />
          <span>LIVE FEED</span>
        </div>
        <div className="activity-stats">
          <Activity size={14} />
          <span>{count} active bookings tracked</span>
        </div>
        <div className="last-updated">
          Updates every 15s
        </div>
      </div>

      {loading ? (
        <div className="feed-loading">
          <div className="loading-dot" />
          <div className="loading-dot" />
          <div className="loading-dot" />
        </div>
      ) : state.items.length === 0 ? (
        <div className="feed-empty">
          <ShieldCheck size={28} />
          <p>No bookings in the last 48 hours from authorized sources.</p>
          <span>Check back soon or explore the search.</span>
        </div>
      ) : (
        <ul className="feed-list">
          {state.items.map((booking, idx) => (
            <li
              key={booking.id}
              className={`feed-item ${state.fresh.includes(idx) ? 'fresh' : ''}`}
            >
              <div className="feed-item__badge">
                <span className={`badge-state badge-${booking.state.toLowerCase()}`}>
                  {booking.state}
                </span>
              </div>
              <div className="feed-item__body">
                <Link href={`/inmate/${booking.id}`} className="feed-item__name">
                  {booking.first_name} {booking.last_name}
                </Link>
                <span className="feed-item__loc">
                  {booking.county}, {booking.state} — {booking.facility_name}
                </span>
              </div>
              <div className="feed-item__time">
                <time dateTime={booking.booking_date}>{timeAgo(booking.booking_date)}</time>
                {state.fresh.includes(idx) && <span className="new-pill">NEW</span>}
              </div>
            </li>
          ))}
        </ul>
      )}

      <div className="feed-footer">
        <ShieldCheck size={14} />
        <span>
          Live bookings from authorized sources. Records not refreshed within 48 hours are automatically hidden.
        </span>
        <Link href="/search" className="feed-footer__link">
          Search all records <ArrowRight size={14} />
        </Link>
      </div>
    </div>
  )
}
