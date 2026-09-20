# JailMap SEO rules

## Indexing policy (standing decision)

The money pages are static, content-rich state and county pages that rank for "[county] jail bookings" / "[state] inmate roster" searches. Query-driven and per-record surfaces are deliberately kept out of the index.

| Surface | Indexed? | Why |
|---|---|---|
| `/` | yes | brand + SearchAction target |
| `/jail-roster` | yes | keyword-rich jail roster landing page with FAQ schema |
| `/about`, `/name-removal` | yes | trust/legal pages |
| `/state/[abbrev]` (all 50) | yes | hub pages, link to live counties |
| `/county/[STATE]/[county-slug]` | yes, when content-eligible | the ranking target |
| `/jail/[state]/[county]/[slug]` | yes, ONLY where enrichment is verified | see `references/directory-and-jurisdiction-joins.md` |
| `/search?...` | no | thin query page |
| `/inmate/[booking_id]` | no | privacy: per-record profiles at index scale are a legal liability |
| `/api/*`, `/admin`, `/login`, `/register`, `/dashboard`, `/forgot`, `/reset` | no | non-content |

**Content-eligible** means the county has enabled ingestion **or** verified facility contact data
(`records.facility_contact_details.verified_at IS NOT NULL`). Neither the directory alone nor
enabled-ingestion alone is sufficient — the first ships thin pages, the second leaves most counties
404-ing while their source is merely unbuilt.

## Files

- `src/app/robots.ts` — allow `/`, disallow `/api/ /admin /login /register /dashboard /inmate/ /forgot /reset`, point at sitemap.
- `src/app/sitemap.ts` — static entries (including `/jail-roster`) + state hubs + content-eligible counties. **It must query per-request and it must log its failures.** See the prerender trap below.
- `src/app/layout.tsx` — `metadataBase: new URL('https://jailmap.com')`, title template `'%s | JailMap'`. Per-page titles therefore must NOT append `| JailMap` themselves.
- `src/app/county/[state]/[county]/page.tsx` — county page: `generateMetadata` + canonical, BreadcrumbList + Dataset JSON-LD (Dataset REQUIRES a `distribution` array or Google rejects it), facility cards with 48h booking counts, prose section on how the data works, correction/name-removal links, source link `rel="nofollow"`.
- `src/app/jail-roster/page.tsx` — dedicated jail roster landing page with search form, state directory, FAQ schema, stats section. Title targets "jail roster search" keywords.

## The prerender trap (this bit the sitemap for real)

`docker build` runs `npm run build` with **no `DATABASE_URL`** — compose injects env at container
runtime, not build time. `src/lib/prisma.ts` throws `Map database is not configured` when it is
unset. So any DB-reading route that can be prerendered gets built with a *failed* query, and if the
catch is silent, the wrong output is frozen into the image and served forever.

Fix on the route:

```typescript
export const dynamic = 'force-dynamic'   // this route's whole job is live DB state
// ...and inside the query block:
} catch (error) {
  // Still don't 500 — but never swallow silently.
  console.error('[sitemap] county query failed:', error)
}
```

Do not rely on `revalidate` to rescue a prerendered route: `export const revalidate = 3600` on a
route whose data comes from the DB leaves a wrong answer live for an hour and depends on ISR firing
while the DB happens to be reachable. Deterministic beats eventual.

### Diagnosis recipe — "is this route actually querying?"

```bash
# 1. Does a baked body exist for the route?
docker compose exec -T web sh -c 'ls -la /app/.next/server/app/sitemap.xml*'
#    sitemap.xml.body  -> a prerendered file; sitemap.xml.meta -> cache-control + cache tags

# 2. Does requesting the route regenerate it? (unchanged mtime = handler never ran)
docker compose exec -T web stat -c '%y %n' /app/.next/server/app/sitemap.xml.body
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3109/sitemap.xml
docker compose exec -T web stat -c '%y %n' /app/.next/server/app/sitemap.xml.body

# 3. Does the DB path work at runtime at all? A server-rendered page proves it.
curl -s http://127.0.0.1:3109/state/MT | grep -oE 'href="/county/MT/[a-z-]+"' | sort -u | wc -l
```

If step 3 returns county links, Prisma and the schema are fine and the fault is prerendering — do
not go hunting for permissions, adapters, or connection strings.

## Conventions

- County slug: lowercase, strip a trailing `" County"`, then `replace(/[^a-z0-9]+/g,'-')`. Use the
  shared helper in `src/lib/county-slug.ts` — the directory stores `"Flathead County"` and
  jurisdictions store `"Flathead"`, so an unnormalized slug silently 404s a county whose data exists.
- State segment is the 2-letter abbreviation: `/county/MT/flathead`.
- State pages must server-render links to live county pages (internal linking is how county pages get discovered and ranked); sitemap alone is not enough.
- `lastModified` is computed per request (`new Date()`), so consecutive sitemap responses differ byte-for-byte. Harmless to crawlers, but it makes `lastmod` meaningless as a freshness signal. Pin it to real data freshness (e.g. the max `last_success_at` across the emitted jurisdictions) instead of the current time.

## Verification recipe

```bash
# robots + sitemap live on prod
curl -s https://jailmap.com/robots.txt
curl -s https://jailmap.com/sitemap.xml | grep -oE '<loc>[^<]+' | wc -l     # total URLs
curl -s https://jailmap.com/sitemap.xml | grep -c 'county/'                # must be > 0

# canonical + title on a state page
curl -s http://127.0.0.1:3109/state/MT | grep -oE '<title>[^<]*</title>|<link rel="canonical"[^>]*>'

# search stays noindexed
curl -s http://127.0.0.1:3109/search | grep -oE '<meta name="robots"[^>]*>'
# expect: noindex, nofollow

# county page renders (slugified county)
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3109/county/MT/flathead

# a county with no live data should 404, not render empty
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3109/county/MT/notarealcounty   # expect 404

# EVERY county URL the sitemap advertises must return 200. A sitemap pointing at
# 404s is worse than an empty one, and this is the only check that catches it.
curl -s https://jailmap.com/sitemap.xml | grep -oE '<loc>[^<]*county/[^<]*' | sed 's/<loc>//' \
  | while read -r u; do printf '%s %s\n' \
      "$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$u")" "$u"; done | sort | uniq -c

# advertised counties must not exceed what is content-eligible in the DB, or the
# sitemap has drifted from reality without anyone noticing
```

After Search Console verification: submit the sitemap, then request indexing on `/`, `/state/MT`,
`/state/ID`, `/state/GA` first — states with live data. Google winnable territory is long-tail
county/name queries, not head terms; do not promise head-term rankings.