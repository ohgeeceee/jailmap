import { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { prisma } from '@/lib/prisma'
import { getStateByAbbrev } from '@/lib/states'
import { StatePageClient } from './StatePageClient'

interface Props {
  params: Promise<{ abbrev: string }>
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { abbrev } = await params
  const state = getStateByAbbrev(abbrev)
  if (!state) return { title: 'State Not Found' }
  
  return {
    title: `${state.name} Jails & Inmate Rosters`,
    description: `Search all jails and detention facilities in ${state.name}. View inmate rosters, booking details, and facility information by county.`,
    alternates: { canonical: `/state/${state.abbrev}` },
  }
}

export default async function StatePage({ params }: Props) {
  const { abbrev } = await params
  const stateInfo = getStateByAbbrev(abbrev)
  
  if (!stateInfo) {
    notFound()
  }

  const state = await prisma.state.findUnique({
    where: { abbrev: stateInfo.abbrev },
    include: {
      counties: {
        include: {
          _count: { select: { jails: true } },
        },
        orderBy: { name: 'asc' },
      },
      _count: { select: { jails: true, counties: true } },
    },
  })

  if (!state) {
    notFound()
  }

  // Counties with live, enabled JailMap jurisdictions — these get real
  // internal links to /county/<state>/<county> pages (indexable ranking
  // targets) instead of only the static county directory.
  const participating = await prisma.$queryRawUnsafe<{ state: string; county: string; facilities: bigint; bookings: bigint }[]>(
    `SELECT j.state, j.county,
       count(DISTINCT j.id) AS facilities,
       (SELECT count(*) FROM records.inmates i
          JOIN records.jurisdictions jj ON jj.id = i.jurisdiction_id
         WHERE jj.state = j.state AND jj.county = j.county AND i.visibility='public'
           AND i.booking_date > now() - interval '48 hours') AS bookings
     FROM records.jurisdictions j
     WHERE j.enabled AND j.state = $1
     GROUP BY j.state, j.county ORDER BY j.county`,
    stateInfo.abbrev,
  )

  return <StatePageClient state={state} counties={state.counties} totalJails={state._count.jails} participating={participating.map((p) => ({ county: p.county, facilities: Number(p.facilities), bookings: Number(p.bookings) }))} />
}