import { prisma } from '@/lib/prisma'
import Link from 'next/link'

export const dynamic = 'force-dynamic'

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
  // Use raw query since Prisma doesn't know about records.jurisdiction schema
  const coverage = await prisma.$queryRawUnsafe(`
    SELECT j.state, COUNT(DISTINCT j.county) AS covered_counties, COUNT(i.id)::int AS records
    FROM records.jurisdictions j
    LEFT JOIN records.inmates i ON i.jurisdiction_id = j.id
    WHERE j.enabled = true
    GROUP BY j.state
    ORDER BY j.state
  `) as { state: string; covered_counties: bigint; records: number }[]

  const totalRecords = coverage.reduce((s, c) => s + c.records, 0)
  const totalCovered = coverage.reduce((s, c) => s + Number(c.covered_counties), 0)

  return (
    <div className="jm-theme">
      <main className="mx-auto max-w-4xl px-5 py-12">
        <h1 className="text-3xl font-bold">Coverage</h1>
        <p className="mt-2 text-[var(--muted)]">
          JailMap aggregates booking data from {totalCovered} counties across {coverage.length} states.
          {totalRecords.toLocaleString()} public records — more added daily.
        </p>

        <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
          {coverage.map((c) => (
            <Link key={c.state} href={`/state/${c.state}`}
              className="rounded border border-[var(--line)] p-3 hover:border-[var(--green)] transition-colors">
              <div className="text-lg font-semibold">{c.state}</div>
              <div className="text-sm text-[var(--muted)]">{STATE_NAMES[c.state]}</div>
              <div className="mt-1 text-xs">
                <span className="font-medium text-[var(--green)]">{Number(c.covered_counties)}</span> counties
                <span className="text-[var(--muted)]"> · {c.records.toLocaleString()} records</span>
              </div>
            </Link>
          ))}
        </div>

        {coverage.length < 51 && (
          <section className="mt-12">
            <h2 className="text-xl font-semibold">Coming soon</h2>
            <p className="mt-2 text-sm text-[var(--muted)]">
              We&rsquo;re actively discovering and verifying official roster sources for all 3,143 U.S. counties.
              States not yet listed are in the source-discovery queue.
            </p>
          </section>
        )}
      </main>
    </div>
  )
}
