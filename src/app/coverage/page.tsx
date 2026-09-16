import Link from 'next/link'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Coverage & Data Sources',
  description: "Which states and counties are live on JailMap. This page lists every participating jurisdiction and the official source it pulls from.",
  alternates: { canonical: '/coverage' },
}

interface Jurisdiction {
  state: string
  county: string
  facility_name: string
  source_url: string
  last_success_at: string | null
}

interface StateSummary {
  state: string
  counties: number
  facilities: number
  recent_bookings: number
}

async function getJurisdictions(): Promise<Jurisdiction[]> {
  const { prisma } = await import('@/lib/prisma')
  return prisma.$queryRawUnsafe<Jurisdiction[]>(`
    SELECT j.state, j.county, j.facility_name, j.source_url, j.last_success_at
    FROM records.jurisdictions j
    WHERE j.enabled AND j.review_status = 'verified'
    ORDER BY j.state, j.county, j.facility_name
  `)
}

async function getSummary(): Promise<{ total: number; states: StateSummary[]; records: number }> {
  const { prisma } = await import('@/lib/prisma')
  const total = await prisma.$queryRawUnsafe<{ n: bigint }[]>(`
    SELECT count(*) AS n FROM records.jurisdictions WHERE enabled AND review_status = 'verified'
  `)
  const records = await prisma.$queryRawUnsafe<{ n: bigint }[]>(`
    SELECT count(*) AS n FROM records.inmates WHERE visibility = 'public'
  `)
  const states = await prisma.$queryRawUnsafe<StateSummary[]>(`
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
  return {
    total: Number(total[0]?.n ?? 0),
    records: Number(records[0]?.n ?? 0),
    states: states.map((s) => ({ ...s, counties: Number(s.counties), facilities: Number(s.facilities), recent_bookings: Number(s.recent_bookings) })),
  }
}

export default async function CoveragePage() {
  const [jurisdictions, summary] = await Promise.all([getJurisdictions(), getSummary()])
  const byState = new Map<string, Jurisdiction[]>()
  for (const j of jurisdictions) {
    if (!byState.has(j.state)) byState.set(j.state, [])
    byState.get(j.state)!.push(j)
  }

  return (
    <div className="jm-theme">
      <main id="main-content" className="mx-auto w-full max-w-5xl px-5 py-16">
        <h1 className="text-4xl font-bold">Coverage &amp; Data Sources</h1>
        <p className="mt-3 text-lg text-[var(--muted)]">
          {summary.states.reduce((n, s) => n + s.facilities, 0)} participating facilities across {summary.states.length} states · {summary.records.toLocaleString()} public booking records.
        </p>

        <section className="mt-8 grid gap-4 sm:grid-cols-3">
          {summary.states.map((s) => (
            <Link
              key={s.state}
              href={`/state/${s.state}`}
              className="rounded border border-[var(--line)] bg-white p-4 hover:border-[var(--green)] transition-colors"
            >
              <span className="text-2xl font-bold">{s.state}</span>
              <span className="block mt-1 text-sm text-[var(--muted)]">
                {s.counties} {s.counties === 1 ? 'county' : 'counties'} · {s.facilities} {s.facilities === 1 ? 'facility' : 'facilities'}
              </span>
              {s.recent_bookings > 0 && (
                <span className="block mt-1 text-sm text-[var(--muted)]">
                  {s.recent_bookings} booking{s.recent_bookings === 1 ? '' : 's'} in last 48h
                </span>
              )}
            </Link>
          ))}
        </section>

        <section className="mt-12 space-y-8">
          {[...byState.entries()].map(([state, items]) => (
            <div key={state}>
              <h2 className="text-2xl font-semibold border-b border-[var(--line)] pb-2">{state}</h2>
              <table className="mt-4 w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-[var(--line)]">
                    <th className="py-2 pr-4 font-semibold">County</th>
                    <th className="py-2 pr-4 font-semibold">Facility</th>
                    <th className="py-2 pr-4 font-semibold">Source</th>
                    <th className="py-2 font-semibold">Last refreshed</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((j) => (
                    <tr key={j.facility_name + j.county} className="border-b border-[var(--line)]/50">
                      <td className="py-2 pr-4">
                        <Link href={`/county/${state}/${j.county.toLowerCase().replace(/\s+/g, '-')}`} className="underline">
                          {j.county}
                        </Link>
                      </td>
                      <td className="py-2 pr-4 text-[var(--muted)]">{j.facility_name}</td>
                      <td className="py-2 pr-4">
                        <a href={j.source_url} rel="nofollow noreferrer" target="_blank" className="text-blue-700 underline truncate block max-w-xs">
                          {new URL(j.source_url).hostname}
                        </a>
                      </td>
                      <td className="py-2 text-[var(--muted)]">
                        {j.last_success_at ? new Date(j.last_success_at).toISOString().slice(0, 10) : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </section>

        <section className="mt-12 rounded border border-[var(--line)] bg-white p-6">
          <h2 className="text-xl font-semibold">How coverage works</h2>
          <p className="mt-3 text-[var(--muted)]">
            JailMap only publishes data from official, authorized sources — county sheriffs, detention facilities, and their official vendors.
            Every record links back to the original source. Records not refreshed within 48 hours are hidden so results stay current.
          </p>
          <p className="mt-3 text-[var(--muted)]">
            If your county isn't listed, it means we don't yet have a working integration with an official source.
            You can request that your county publish a machine-readable roster — many already do.
          </p>
        </section>
      </main>
    </div>
  )
}
