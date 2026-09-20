import { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { prisma } from '@/lib/prisma'
import { getStateByAbbrev } from '@/lib/states'
import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import { slugifyCounty } from '@/lib/county-slug'

interface Props {
  params: Promise<{ abbrev: string }>
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { abbrev } = await params
  const state = getStateByAbbrev(abbrev)
  if (!state) return { title: 'State Not Found' }

  return {
    title: `${state.name} Jails & JailMap Bookings`,
    description: `JailMap booking data in ${state.name}. View participating counties, recent bookings and jail roster information from authorized sources.`,
    alternates: { canonical: `/state/${state.abbrev}` },
    openGraph: {
      title: `${state.name} Jails & JailMap Bookings | JailMap`,
      description: `JailMap booking data in ${state.name}. View participating counties, recent bookings and jail roster information from authorized sources.`,
      url: `https://jailmap.com/state/${state.abbrev}`,
      siteName: 'JailMap',
    },
  }
}

interface ParticipatingCounty {
  county: string
  facilities: number
  bookings: number
}

export default async function StatePage({ params }: Props) {
  const { abbrev } = await params
  const stateInfo = getStateByAbbrev(abbrev)

  if (!stateInfo) notFound()

  const state = await prisma.state.findUnique({
    where: { abbrev: stateInfo.abbrev },
    include: {
      counties: { orderBy: { name: 'asc' } },
      _count: { select: { jails: true, counties: true } },
    },
  })

  if (!state) notFound()

  const participating = await prisma.$queryRawUnsafe<ParticipatingCounty[]>(
    `SELECT j.county,
       count(DISTINCT j.id) AS facilities,
       (SELECT count(*) FROM records.inmates i
          JOIN records.jurisdictions jj ON jj.id = i.jurisdiction_id
         WHERE jj.state = j.state AND jj.county = j.county AND i.visibility = 'public'
           AND i.booking_date > now() - interval '48 hours') AS bookings
     FROM records.jurisdictions j
     WHERE j.enabled AND j.state = $1
     GROUP BY j.state, j.county ORDER BY j.county`,
    stateInfo.abbrev,
  )

  const participatingSlugs = new Set(participating.map((p) => slugifyCounty(p.county)))

  const countyLd = {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: `${stateInfo.name} counties — JailMap`,
    itemListElement: state.counties.map((c, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: `${c.name} County`,
      ...(participatingSlugs.has(slugifyCounty(c.name))
        ? { url: `https://jailmap.com/county/${state.abbrev}/${slugifyCounty(c.name)}` }
        : {}),
    })),
  }

  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content">
        <nav aria-label="Breadcrumb" className="breadcrumb">
          <Link href="/">JailMap</Link>
          {' / '}
          <span>{stateInfo.name}</span>
        </nav>

        <div className="site-width state-page">
          <h1>{stateInfo.name}</h1>
          <p className="state-meta">
            {state._count.counties} counties · {state._count.jails} facilities in the directory
          </p>

          {participating.length > 0 && (
            <section className="state-section">
              <h2>Counties with live booking data</h2>
              <p className="section-description">
                These counties have participating facilities feeding current rosters into JailMap.
              </p>
              <div className="county-grid">
                {participating.map((p) => (
                  <Link
                    key={p.county}
                    href={`/county/${state.abbrev}/${slugifyCounty(p.county)}`}
                    className="county-card"
                  >
                    <span className="county-card__name">{p.county} County</span>
                    <span className="county-card__meta">
                      {p.facilities} facility{p.facilities === 1 ? '' : 's'} · {p.bookings} booking{p.bookings === 1 ? '' : 's'} in last 48h
                    </span>
                  </Link>
                ))}
              </div>
            </section>
          )}

          <section className="state-section">
            <h2>All counties in {stateInfo.name}</h2>
            <p className="section-description">
              The jail directory includes facilities that may not yet be part of JailMap's live roster feed.
            </p>
            <div className="county-grid compact">
              {state.counties.map((c) => {
                const slug = slugifyCounty(c.name)
                const isParticipating = participatingSlugs.has(slug)
                return (
                  isParticipating ? (
                    <Link
                      key={c.id}
                      href={`/county/${state.abbrev}/${slug}`}
                      className="county-card compact live"
                    >
                      <span>{c.name} County</span>
                      <span className="county-card__badge">Live</span>
                    </Link>
                  ) : (
                    <span key={c.id} className="county-card compact">
                      <span>{c.name} County</span>
                    </span>
                  )
                )
              })}
            </div>
          </section>

          <section className="state-section">
            <h2>Search {stateInfo.name} bookings</h2>
            <p className="section-description">
              Search across all participating jurisdictions in {stateInfo.name}, or pick a county above to scope your search.
            </p>
            <form action="/search" className="inline-search">
              <input type="hidden" name="state" value={state.abbrev} />
              <input
                name="name"
                placeholder="First or last name"
                minLength={2}
                maxLength={100}
                required
              />
              <button type="submit" className="jm-button">Search</button>
            </form>
          </section>
        </div>
      </main>
      <Footer />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(countyLd) }} />
    </div>
  )
}