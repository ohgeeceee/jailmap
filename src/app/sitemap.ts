import type { MetadataRoute } from 'next'
import { US_STATES } from '@/lib/states'
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
  { url: `${BASE}/about`, changeFrequency: 'monthly', priority: 0.5 },
  { url: `${BASE}/name-removal`, changeFrequency: 'monthly', priority: 0.5 },
]

interface CountyRow {
  state: string
  county: string
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const lastModified = new Date()
  const entries: MetadataRoute.Sitemap = [
    ...STATIC_ENTRIES.map((e) => ({ ...e, lastModified })),
    ...US_STATES.map((state) => ({
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
