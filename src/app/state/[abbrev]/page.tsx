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
     GROUP BY j.county ORDER BY j.county`,
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
        <nav aria-label="Breadcrumb" className="mx-auto w-full max-w-6xl px-5 pt-8 text-sm text-[var(--muted)]">
          <Link href="/" className="underline">JailMap</Link>
          {' / '}
          <span>{stateInfo.name}</span>
        </nav>

        <div className="mx-auto w-full max-w-6xl px-5 pb-16">
          <h1 className="mt-6 text-4xl font-bold">{stateInfo.name}</h1>
          <p className="mt-2 text-[var(--muted)]">
            {state._count.counties} counties · {state._count.jails} facilities in the directory
          </p>

          {participating.length > 0 && (
            <section className="mt-10">
              <h2 className="text-2xl font-semibold">Counties with live booking data</h2>
              <p className="mt-2 text-[var(--muted)]">
                These counties have participating facilities feeding current rosters into JailMap.
              </p>
              <ul className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {participating.map((p) => (
                  <li key={p.county}>
                    <Link
                      href={`/county/${state.abbrev}/${slugifyCounty(p.county)}`}
                      className="block rounded border border-[var(--line)] bg-white p-4 hover:border-[var(--green)] transition-colors"
                    >
                      <span className="font-medium text-[var(--ink)]">{p.county} County</span>
                      <span className="block mt-1 text-sm text-[var(--muted)]">
                        {p.facilities} facility{p.facilities === 1 ? '' : 's'} · {p.bookings} booking{p.bookings === 1 ? '' : 's'} in last 48h
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section className="mt-12">
            <h2 className="text-2xl font-semibold">All counties in {stateInfo.name}</h2>
            <p className="mt-2 text-[var(--muted)]">
              The jail directory includes facilities that may not yet be part of JailMap's live roster feed.
            </p>
            <ul className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {state.counties.map((c) => {
                const slug = slugifyCounty(c.name)
                const isParticipating = participatingSlugs.has(slug)
                return (
                  <li key={c.id}>
                    {isParticipating ? (
                      <Link
                        href={`/county/${state.abbrev}/${slug}`}
                        className="flex items-center justify-between rounded border border-[var(--line)] bg-white p-3 hover:border-[var(--green)] transition-colors"
                      >
                        <span className="text-[var(--ink)]">{c.name} County</span>
                        <span className="text-xs text-[var(--muted)]">Live →</span>
                      </Link>
                    ) : (
                      <span className="flex items-center justify-between rounded border border-[var(--line)] bg-[var(--paper)] p-3 text-[var(--muted)]">
                        <span>{c.name} County</span>
                        <span className="text-xs">—</span>
                      </span>
                    )}
                  </li>
                )
              })}
            </ul>
          </section>

          <section className="mt-10 max-w-3xl">
            <h2 className="text-2xl font-semibold">Search {stateInfo.name} bookings</h2>
            <p className="mt-3 text-[var(--muted)]">
              Search across all participating jurisdictions in {stateInfo.name}, or pick a county above to scope your search.
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <form action="/search" className="flex gap-2 w-full max-w-md">
                <input type="hidden" name="state" value={state.abbrev} />
                <input
                  name="name"
                  placeholder="First or last name"
                  minLength={2}
                  maxLength={100}
                  required
                  className="flex-1 rounded border border-[var(--line)] bg-white px-4 py-2 text-[var(--ink)]"
                />
                <button type="submit" className="jm-button">Search</button>
              </form>
            </div>
          </section>
        </div>
      </main>
      <Footer />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(countyLd) }} />
    </div>
  )
}
