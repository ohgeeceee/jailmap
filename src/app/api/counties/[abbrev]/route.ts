import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ abbrev: string }> }
) {
  try {
    const { abbrev } = await params
    const { searchParams } = new URL(request.url)
    const includeCounts = searchParams.get('includeCounts') === 'true'
    const search = searchParams.get('search') || ''

    const state = await prisma.state.findUnique({
      where: { abbrev: abbrev.toUpperCase() },
    })

    if (!state) {
      return NextResponse.json({ error: 'State not found' }, { status: 404 })
    }

    const counties = await prisma.county.findMany({
      where: {
        stateId: state.id,
        name: { contains: search, mode: 'insensitive' },
      },
      include: {
        _count: includeCounts ? { select: { jails: { where: { isActive: true } } } } : false,
      },
      orderBy: { name: 'asc' },
    })

    return NextResponse.json({ data: counties })
  } catch (error) {
    console.error('Error fetching counties:', error)
    return NextResponse.json({ error: 'Failed to fetch counties' }, { status: 500 })
  }
}
