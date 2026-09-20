import { prisma } from '@/lib/prisma'
import Link from 'next/link'
import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'

export const dynamic = 'force-dynamic'

export const metadata = {
  title: 'Coverage map',
  description: 'JailMap public booking records by state and county. See which jurisdictions have live data and how many records are currently available.',
  alternates: { canonical: 'https://jailmap.com/coverage' },
  openGraph: {
    title: 'Coverage map | JailMap',
    description: 'JailMap public booking records by state and county. See which jurisdictions have live data and how many records are currently available.',
    url: 'https://jailmap.com/coverage',
  },
}

const STATE_NAMES: Record<string, string> = {
  AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California',
  CO: 'Colorado', CT: 'Connecticut', DE: 'Delaware', FL: 'Florida', GA: 'Georgia',
  HI: 'Hawaii', ID: 'Idaho', IL: 'Illinois', IN: 'Indiana', IA: 'Iowa',
  KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland',
  MA: 'Massachusetts', MI: 'Michigan', MN: 'Minnesota', MS: 'Mississippi', MO: 'Missouri',
  MT: 'Montana', NE: 'Nebraska', NV: 'Nevada', NH: 'New Hampshire', NJ: 'New Jersey',
  NM: 'New Mexico', NY: 'New York', NC: 'North Carolina', ND: 'North Dakota', OH: 'Ohio',
  OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania', RI: 'Rhode Island', SC: 'South Carolina',
  SD: 'South Dakota', TN: 'Tennessee', TX: 'Texas', UT: 'Utah', VT: 'Vermont',
  VA: 'Virginia', WA: 'Washington', WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming',
  DC: 'District of Columbia'
}

export default async function CoveragePage() {
  const coverage = await prisma.$queryRawUnsafe(`
    SELECT j.state, COUNT(DISTINCT j.county) AS covered_counties, COUNT(i.id)::int AS records
    FROM records.jurisdictions j
    JOIN records.inmates i ON i.jurisdiction_id = j.id
    WHERE j.enabled = true
      AND j.review_status = 'verified'
      AND i.visibility = 'public'
      AND i.observed_at > now() - interval '48 hours'
    GROUP BY j.state
    ORDER BY j.state
  `) as { state: string; covered_counties: bigint; records: number }[]

  const totalRecords = coverage.reduce((s, c) => s + c.records, 0)
  const totalCovered = coverage.reduce((s, c) => s + Number(c.covered_counties), 0)

  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content">
        <section className="site-width info-page">
          <span className="eyebrow"><span className="small-dot" />COVERAGE</span>
          <h1>National coverage map.</h1>
          <p className="info-intro">
            JailMap currently has public booking data from {totalCovered} counties across {coverage.length} states.
            {' '}{totalRecords.toLocaleString()} records have been refreshed within the last 48 hours.
          </p>
        </section>

        <section className="site-width" style={{ paddingBlock: '0 48px' }}>
          <div className="feature-grid">
            <article className="feature-card stat-highlight">
              <div className="feature-top"><span>01</span></div>
              <h3>Counties indexed</h3>
              <p style={{ fontSize: '28px', fontWeight: 600, fontFamily: 'var(--font-data)', color: 'var(--ink)' }}>{totalCovered.toLocaleString()}</p>
            </article>
            <article className="feature-card stat-highlight">
              <div className="feature-top"><span>02</span></div>
              <h3>States with current records</h3>
              <p style={{ fontSize: '28px', fontWeight: 600, fontFamily: 'var(--font-data)', color: 'var(--ink)' }}>{coverage.length} / 51</p>
            </article>
            <article className="feature-card stat-highlight">
              <div className="feature-top"><span>03</span></div>
              <h3>Total booking records</h3>
              <p style={{ fontSize: '28px', fontWeight: 600, fontFamily: 'var(--font-data)', color: 'var(--ink)' }}>{totalRecords.toLocaleString()}</p>
            </article>
          </div>
        </section>

        <section className="site-width" style={{ paddingBlock: '0 64px' }}>
          <div className="section-heading"><div><span className="eyebrow">BY STATE</span><h2>States with current public records.</h2></div></div>
          <div className="state-grid">
            {coverage.map((c) => (
              <Link key={c.state} href={`/state/${c.state}`} className="state-card">
                <div className="state-card__abbrev">{c.state}</div>
                <div className="state-card__name">{STATE_NAMES[c.state]}</div>
                <div className="state-card__meta">
                  <span className="state-card__num">{Number(c.covered_counties)}</span> counties
                  <span className="state-card__sep">·</span>
                  <span>{c.records.toLocaleString()}</span> records
                </div>
              </Link>
            ))}
          </div>

          {coverage.length < 51 && (
            <section style={{ marginTop: '48px' }}>
              <h2 style={{ fontSize: '22px', fontWeight: 550, marginBottom: '14px', letterSpacing: '-0.4px' }}>Coming soon</h2>
              <p style={{ fontSize: '14px', lineHeight: 1.9, color: 'var(--muted)' }}>
                We&rsquo;re actively discovering and verifying official roster sources for all 3,143 U.S. counties.
                States not yet listed are in the source-discovery queue.
              </p>
            </section>
          )}
        </section>
      </main>
      <Footer />
    </div>
  )
}
