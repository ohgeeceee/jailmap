import type { MetadataRoute } from 'next'
import { prisma } from '@/lib/prisma'
import { slugifyCounty } from '@/lib/county-slug'

const BASE = 'https://jailmap.com'

// This route must run per-request. Its whole job is to reflect live coverage, and
// `docker build` runs with no DATABASE_URL, so a prerendered sitemap freezes a
// zero-county version into the image (that was the live defect: 54 URLs, 0 county
// URLs, permanently). Do not reintroduce prerendering or an ISR window here.
export const dynamic = 'force-dynamic'

// Static, indexable surfaces. /search and /inmate/[id] stay noindexed by design:
// query-driven result pages and per-record profiles are not what we want Google
// spending crawl budget on (or holding in the index).
//
// /leaderboard and /new-bookings are deliberately ABSENT: both set
// `robots: { index: false }` in their own metadata. Listing a noindexed URL in
// the sitemap is a contradiction — it asks Google to crawl a page we are telling
// it not to index. Only indexable URLs belong here.
const STATIC_ENTRIES: MetadataRoute.Sitemap = [
  { url: `${BASE}/`, changeFrequency: 'daily', priority: 1.0 },
  { url: `${BASE}/jail-roster`, changeFrequency: 'daily', priority: 0.9 },
  { url: `${BASE}/about`, changeFrequency: 'monthly', priority: 0.6 },
  { url: `${BASE}/privacy`, changeFrequency: 'monthly', priority: 0.6 },
  { url: `${BASE}/terms`, changeFrequency: 'monthly', priority: 0.6 },
  { url: `${BASE}/name-removal`, changeFrequency: 'monthly', priority: 0.7 },
  { url: `${BASE}/coverage`, changeFrequency: 'daily', priority: 0.7 },
  { url: `${BASE}/help`, changeFrequency: 'monthly', priority: 0.6 },
  { url: `${BASE}/states`, changeFrequency: 'daily', priority: 0.9 },
  { url: `${BASE}/pricing`, changeFrequency: 'monthly', priority: 0.7 },
  { url: `${BASE}/careers`, changeFrequency: 'monthly', priority: 0.5 },
  { url: `${BASE}/contact`, changeFrequency: 'monthly', priority: 0.5 },
  { url: `${BASE}/enterprise`, changeFrequency: 'monthly', priority: 0.6 },
  { url: `${BASE}/legal`, changeFrequency: 'monthly', priority: 0.5 },
  { url: `${BASE}/trust-safety`, changeFrequency: 'monthly', priority: 0.5 },
  { url: `${BASE}/api-docs`, changeFrequency: 'monthly', priority: 0.6 },
]

interface CountyRow {
  state: string
  county: string
}

interface StateRow {
  abbrev: string
}

// /state/[abbrev] 404s when there is no row in public."State" (the StatePage
// does a findUnique), so the sitemap must be driven by that table — not the
// static US_STATES list, which includes DC and would advertise a dead URL.
async function getIndexedStates(): Promise<StateRow[]> {
  return prisma.$queryRawUnsafe<StateRow[]>(`SELECT abbrev FROM "public"."State" ORDER BY abbrev`)
}

// Use the max successful-ingestion timestamp as the sitemap lastmod so it
// reflects real data freshness instead of the current request time.
// Fall back to "now" if the ingestion_runs table is empty or unreachable.
async function getSitemapLastModified(): Promise<Date> {
  try {
    const rows = await prisma.$queryRawUnsafe<{ max: Date | null }[]>(
      `SELECT max(started_at) AS max FROM records.ingestion_runs WHERE status = 'success'`
    )
    const ts = rows[0]?.max
    if (ts instanceof Date && !isNaN(ts.getTime())) return ts
  } catch (error) {
    console.error('[sitemap] lastmod query failed:', error)
  }
  return new Date()
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const lastModified = await getSitemapLastModified()
  const states = await getIndexedStates()
  const entries: MetadataRoute.Sitemap = [
    ...STATIC_ENTRIES.map((e) => ({ ...e, lastModified })),
    ...states.map((state) => ({
      url: `${BASE}/state/${state.abbrev}`,
      changeFrequency: 'daily' as const,
      priority: 0.8,
      lastModified,
    })),
  ]

  // Counties worth indexing: enabled ingestion AND at least one public record.
  //
  // The content gate matters more than the count. Advertising a county page with
  // zero records points Google at a thin shell, which is worse than not being
  // listed at all. Verified 2026-09-14: of 27 enabled jurisdictions, 8 had public
  // records and 19 were empty — and those 19 were exactly the jurisdictions whose
  // sources are broken or awaiting review. Gate on content, not on the flag.
  //
  // Deliberately NOT included: counties that only have a verified row in
  // records.facility_contact_details. The county route renders from
  // records.jurisdictions, so such a county 404s — advertising it would point
  // Google at a 404. Revisit once the facility↔jurisdiction bridge lands.
  let counties: CountyRow[] = []
  try {
    counties = await prisma.$queryRawUnsafe<CountyRow[]>(`
      SELECT DISTINCT j.state, j.county
        FROM records.jurisdictions j
       WHERE j.enabled
         AND EXISTS (
           SELECT 1 FROM records.inmates i
            WHERE i.jurisdiction_id = j.id AND i.visibility = 'public'
         )
       ORDER BY j.state, j.county
    `)
  } catch (error) {
    // Keep the route from 500-ing (the original intent) but never swallow this
    // silently — a silent catch is what hid the defect for this long.
    console.error('[sitemap] county query failed:', error)
  }

  for (const c of counties) {
    const slug = slugifyCounty(c.county)
    if (!slug) continue
    entries.push({
      url: `${BASE}/county/${c.state}/${slug}`,
      changeFrequency: 'daily',
      priority: 0.7,
      lastModified,
    })
  }

  return entries
}
