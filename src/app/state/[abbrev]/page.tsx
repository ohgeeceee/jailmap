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
    title: `${state.name} Jails & Inmate Rosters | JailMap`,
    description: `Search all jails and detention facilities in ${state.name}. View inmate rosters, booking details, and facility information by county.`,
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

  return <StatePageClient state={state} counties={state.counties} totalJails={state._count.jails} />
}