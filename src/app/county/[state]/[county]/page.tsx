import { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { prisma } from '@/lib/prisma'
import { getStateByAbbrev } from '@/lib/states'
import { slugifyCounty, countyKey } from '@/lib/county-slug'
import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import { Disclaimer } from '@/components/records/Disclaimer'

export const revalidate = 300

interface Props {
  params: Promise<{ state: string; county: string }>
}

interface JurisdictionRow {
  id: string
  state: string
  county: string
  facility_name: string
  source_url: string
  last_success_at: Date | null
  total_bookings: bigint
  recent_bookings: bigint
}

async function getJurisdictions(state: string, countySlug: string): Promise<JurisdictionRow[]> {
  const rows = await prisma.$queryRawUnsafe<(JurisdictionRow & { county: string })[]>(
    `SELECT j.id::text, j.state, j.county, j.facility_name, j.source_url, j.last_success_at,
       (SELECT count(*) FROM records.inmates i WHERE i.jurisdiction_id=j.id AND i.visibility='public') AS total_bookings,
       (SELECT count(*) FROM records.inmates i WHERE i.jurisdiction_id=j.id AND i.visibility='public'
          AND i.booking_date > now() - interval '48 hours') AS recent_bookings
     FROM records.jurisdictions j
     WHERE j.enabled AND j.state = $1
     ORDER BY j.facility_name`,
    state,
  )
  // Match with the SAME slug rule the sitemap uses (src/lib/county-slug.ts):
  // DB county names may carry a " County" suffix ("Cassia County" -> slug "cassia").
  // An ad-hoc SQL replace() disagreed with slugifyCounty and 404'd those pages.
  return rows.filter((r) => slugifyCounty(r.county) === countySlug)
}

function formatDate(d: Date | null): string {
  if (!d) return 'pending'
  return new Date(d).toISOString().slice(0, 10)
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { state, county } = await params
  const stateInfo = getStateByAbbrev(state.toUpperCase())
  const countyName = countyKey(county.replace(/-/g, ' ')).replace(/\b\w/g, (c) => c.toUpperCase())
  if (!stateInfo) return { title: 'County Not Found', robots: { index: false } }

  return {
    title: `${countyName} County, ${stateInfo.name} Jail Bookings & Inmate Roster`,
    description: `Recent jail bookings and inmate roster information for ${countyName} County, ${stateInfo.name}. See charges, bond details and the original booking source, updated continuously from authorized sources.`,
    alternates: { canonical: `/county/${stateInfo.abbrev}/${county}` },
  }
}

export default async function CountyPage({ params }: Props) {
  const { state, county } = await params
  const abbrev = state.toUpperCase()
  const stateInfo = getStateByAbbrev(abbrev)
  if (!stateInfo || !/^[a-z0-9-]+$/.test(county)) notFound()

  const jurisdictions = await getJurisdictions(abbrev, county)
  if (jurisdictions.length === 0) notFound()

  // DB names may already carry the " County" suffix ("Cassia County"); the
  // templates below append " County" themselves, so normalize with the shared key.
  const countyName = countyKey(jurisdictions[0].county).replace(/\b\w/g, (c) => c.toUpperCase())
  const totalRecent = jurisdictions.reduce((sum, j) => sum + Number(j.recent_bookings), 0)
  const totalAll = jurisdictions.reduce((sum, j) => sum + Number(j.total_bookings), 0)

  const breadcrumbLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'JailMap', item: 'https://jailmap.com/' },
      { '@type': 'ListItem', position: 2, name: stateInfo.name, item: `https://jailmap.com/state/${abbrev}` },
      { '@type': 'ListItem', position: 3, name: `${countyName} County` },
    ],
  }

  const datasetLd = {
    '@context': 'https://schema.org',
    '@type': 'Dataset',
    name: `${countyName} County, ${stateInfo.name} jail booking records`,
    description: `Public jail booking records for ${countyName} County, ${stateInfo.name}, including charges, bond information and booking dates, aggregated from authorized official sources.`,
    url: `https://jailmap.com/county/${abbrev}/${county}`,
    keywords: [`${countyName} County jail bookings`, `${countyName} County inmate roster`, `${stateInfo.name} public records`],
    creator: { '@type': 'Organization', name: 'JailMap', url: 'https://jailmap.com' },
    distribution: [
      {
        '@type': 'DataDownload',
        encodingFormat: 'text/html',
        contentUrl: `https://jailmap.com/search?state=${abbrev}&county=${encodeURIComponent(jurisdictions[0].county)}`,
        name: 'Browse current bookings online',
      },
    ],
  }

  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content" className="mx-auto w-full max-w-6xl px-5 py-12">
        <nav aria-label="Breadcrumb" className="text-sm text-[var(--muted,#65726b)]">
          <Link href="/" className="underline">JailMap</Link>
          {' / '}
          <Link href={`/state/${abbrev}`} className="underline">{stateInfo.name}</Link>
          {' / '}
          <span>{countyName} County</span>
        </nav>

        <h1 className="mt-6 text-4xl font-bold">{countyName} County Jail Bookings &amp; Inmate Roster</h1>
        <p className="mt-3 text-lg text-[var(--muted,#65726b)]">
          Public booking information from {jurisdictions.length === 1 ? 'the participating detention facility' : `${jurisdictions.length} participating facilities`} in {countyName} County, {stateInfo.name}.
          Every record links back to the original official source. All individuals are presumed innocent.
        </p>
        <p className="mt-2 text-sm text-[var(--muted,#65726b)]">
          {totalRecent} booking{totalRecent === 1 ? '' : 's'} in the last 48 hours · {totalAll.toLocaleString()} in the current archive.
        </p>

        <section className="mt-8 space-y-4">
          {jurisdictions.map((j) => (
            <article key={j.id} className="rounded-lg border border-[var(--line,#dfe4dc)] bg-[var(--paper,#f8f9f4)] p-5">
              <h2 className="text-xl font-semibold">{j.facility_name}</h2>
              <p className="mt-2 text-sm text-[var(--muted,#65726b)]">
                {Number(j.recent_bookings)} booking{Number(j.recent_bookings) === 1 ? '' : 's'} in the last 48 hours ·
                {' '}{Number(j.total_bookings).toLocaleString()} records archived ·
                {' '}source last refreshed {formatDate(j.last_success_at)}
              </p>
              <div className="mt-4 flex flex-wrap gap-3 text-sm">
                <Link
                  href={`/search?state=${abbrev}&county=${encodeURIComponent(j.county)}`}
                  className="rounded bg-[var(--green,#214f40)] px-4 py-2 font-medium text-white"
                >
                  View current bookings
                </Link>
                <a
                  href={j.source_url}
                  rel="nofollow"
                  className="rounded border border-[var(--line,#dfe4dc)] px-4 py-2"
                >
                  Official source
                </a>
              </div>
            </article>
          ))}
        </section>

        <section className="mt-10 max-w-3xl">
          <h2 className="text-2xl font-semibold">How {countyName} County booking data works</h2>
          <p className="mt-3">
            JailMap aggregates booking information published by authorized official sources in {countyName} County.
            Records not refreshed within 48 hours are hidden so results stay current. Booking data is a snapshot of an
            arrest — it is not evidence of a conviction, and a name match does not establish identity.
          </p>
          <p className="mt-3">
            If information about you or someone you represent appears here, you can request a correction or removal at
            no charge from the booking page itself. See <Link href="/about" className="underline">our approach</Link> or
            the <Link href="/name-removal" className="underline">name removal process</Link>.
          </p>
        </section>

        <Disclaimer />
      </main>
      <Footer />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbLd) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(datasetLd) }} />
    </div>
  )
}
