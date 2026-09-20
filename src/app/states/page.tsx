import { Metadata } from 'next'
import Link from 'next/link'
import { US_STATES, STATE_ABBREV_TO_NAME } from '@/lib/states'

// Queries the DB at render time; must not be prerendered at image build.
export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: 'JailMap by State — All 50 States',
  description: 'Browse JailMap coverage by state. Search inmate rosters, jail bookings and detention facility information across the United States.',
  alternates: { canonical: '/states' },
  openGraph: {
    title: 'JailMap by State — All 50 States',
    description: 'Browse JailMap coverage by state. Search inmate rosters, jail bookings and detention facility information across the United States.',
    url: 'https://jailmap.com/states',
    siteName: 'JailMap',
  },
}

interface LiveState {
  state: string
  counties: number
  facilities: number
  recent_bookings: number
}

async function getLiveStates(): Promise<Map<string, LiveState>> {
  const { prisma } = await import('@/lib/prisma')
  const rows = await prisma.$queryRawUnsafe<LiveState[]>(`
    SELECT j.state,
      count(DISTINCT j.county) AS counties,
      count(DISTINCT j.id) AS facilities,
      (SELECT count(*) FROM records.inmates i
         JOIN records.jurisdictions jj ON jj.id = i.jurisdiction_id
         WHERE jj.state = j.state AND i.visibility = 'public'
           AND i.booking_date > now() - interval '48 hours') AS recent_bookings
    FROM records.jurisdictions j
    WHERE j.enabled AND j.review_status = 'verified'
    GROUP BY j.state ORDER BY j.state
  `)
  const map = new Map<string, LiveState>()
  for (const r of rows) {
    map.set(r.state, { ...r, counties: Number(r.counties), facilities: Number(r.facilities), recent_bookings: Number(r.recent_bookings) })
  }
  return map
}

export default async function StatesPage() {
  const live = await getLiveStates()
  const hasLive = [...live.keys()]

  const webPageLd = {
    '@context': 'https://schema.org',
    '@type': 'WebPage',
    name: 'JailMap by State',
    description: 'Browse JailMap coverage across all 50 US states.',
    url: 'https://jailmap.com/states',
  }

  return (
    <div className="jm-theme">
      <main id="main-content" className="site-width states-page">
        <h1>All States</h1>
        <p className="states-intro">
          Browse every US state. Highlighted states have live booking data on JailMap today.
        </p>

        <section className="states-section">
          {hasLive.length > 0 && (
            <>
              <h2>States with live data</h2>
              <div className="state-grid">
                {hasLive.map((s) => {
                  const info = live.get(s)!
                  return (
                    <Link
                      key={s}
                      href={`/state/${s}`}
                      className="state-card live"
                    >
                      <span className="state-card__abbrev">{STATE_ABBREV_TO_NAME[s] || s}</span>
                      <span className="state-card__meta">
                        {info.counties} {info.counties === 1 ? 'county' : 'counties'} · {info.recent_bookings} recent booking{info.recent_bookings === 1 ? '' : 's'}
                      </span>
                    </Link>
                  )
                })}
              </div>
            </>
          )}
        </section>

        <section className="states-section">
          <h2>All 50 states &amp; DC</h2>
          <div className="state-grid compact">
            {US_STATES.map((state) => {
              const isActive = live.has(state.abbrev)
              return (
                isActive ? (
                  <Link
                    key={state.abbrev}
                    href={`/state/${state.abbrev}`}
                    className="state-card compact live"
                  >
                    <span>{state.name}</span>
                    <span className="state-card__badge">Live</span>
                  </Link>
                ) : (
                  <span key={state.abbrev} className="state-card compact">
                    <span>{state.name}</span>
                  </span>
                )
              )
            })}
          </div>
        </section>
      </main>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(webPageLd) }} />
    </div>
  )
}