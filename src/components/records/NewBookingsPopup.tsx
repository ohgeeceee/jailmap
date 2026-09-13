'use client'

import { useEffect, useState, useRef } from 'react'
import { Radio, Activity } from 'lucide-react'
import { STATE_ABBREV_TO_NAME } from '@/lib/states'

type Item = {
  id: string
  first_name: string
  last_name: string
  booking_date: string
  state: string
  county: string
  facility_name: string
}

type PopupState = 'idle' | 'entering' | 'visible' | 'exiting'

export function NewBookingsPopup() {
  const [state, setState] = useState<PopupState>('idle')
  const [count, setCount] = useState(0)
  const [latest, setLatest] = useState<Item | null>(null)
  const [nowText, setNowText] = useState('checking…')
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const exitTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const ageLabel = (iso: string) => {
    const then = new Date(iso).getTime()
    const diff = Math.max(0, Date.now() - then)
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'just now'
    if (mins < 60) return `${mins}m ago`
    const hrs = Math.floor(mins / 60)
    if (hrs < 24) return `${hrs}h ago`
    return 'today'
  }

  const fetchFeed = () => {
    fetch('/api/new-bookings?limit=10')
      .then(r => (r.ok ? r.json() : null))
      .then(d => {
        const items: Item[] = d?.items || []
        setCount(items.length)
        setLatest(items[0] ?? null)
        setNowText(items.length ? ageLabel(items[0].booking_date) : 'no recent bookings')
      })
      .catch(() => setNowText('feed unavailable'))
  }

  useEffect(() => {
    if (typeof window === 'undefined') return
    const dismissed = sessionStorage.getItem('jm_popup_dismissed') === '1'
    if (dismissed) return

    // start fetching immediately — data should land before the popup
    // slides into view at 1650ms (fetch ~885ms)
    void fetchFeed()
    const iv = setInterval(fetchFeed, 20000)
    return () => clearInterval(iv)
  }, [])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const dismissed = sessionStorage.getItem('jm_popup_dismissed') === '1'
    if (dismissed) return

    const enter = () => setState('entering')
    const visible = () => setState('visible')
    timerRef.current = setTimeout(enter, 1200)
    const enterTimer = setTimeout(visible, 1200 + 450)
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
      if (enterTimer) clearTimeout(enterTimer)
    }
  }, [])

  const close = () => {
    setState('exiting')
    if (exitTimerRef.current) clearTimeout(exitTimerRef.current)
    exitTimerRef.current = setTimeout(() => {
      setState('idle')
      try { sessionStorage.setItem('jm_popup_dismissed', '1') } catch {}
    }, 350)
  }

  // auto-dismiss once visible
  useEffect(() => {
    if (state !== 'visible') return
    const t = setTimeout(close, 9000)
    return () => clearTimeout(t)
  }, [state, close])

  if (state === 'idle' || state === 'exiting') return null

  const show = latest && count > 0
  const stateName = latest ? (STATE_ABBREV_TO_NAME[latest.state] || latest.state) : ''

  return (
    <div className={`jm-popup jm-popup--${state}`} role="status" aria-live="polite">
      <div className="jm-popup__inner">
        <div className="jm-popup__mark">
          <Radio size={12} className="pulse" />
          <span>NEW BOOKINGS</span>
        </div>
        <div className="jm-popup__body">
          {show ? (
            <>
              <span className="jm-popup__count">
                <Activity size={11} />
                {count} new booking{count === 1 ? '' : 's'} in the last 48 hours
              </span>
              <span className="jm-popup__sep">·</span>
              <span className="jm-popup__latest">
                <strong>{latest.first_name} {latest.last_name}</strong>
                {' '}booked at {latest.facility_name} in {latest.county}, {stateName}
              </span>
              <span className="jm-popup__time">{nowText}</span>
            </>
          ) : (
            <span className="jm-popup__count">
              <Activity size={11} />
              Live booking feed active — {count} bookings tracked
            </span>
          )}
        </div>
        <button className="jm-popup__close" onClick={close} aria-label="Dismiss notification">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
            <path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
          </svg>
        </button>
      </div>
    </div>
  )
}
