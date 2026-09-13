import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ jailId: string }> }
) {
  try {
    const { jailId } = await params
    const { searchParams } = new URL(request.url)
    const search = searchParams.get('search') || ''
    const page = parseInt(searchParams.get('page') || '1')
    const limit = parseInt(searchParams.get('limit') || '50')
    const skip = (page - 1) * limit

    const jail = await prisma.jail.findUnique({
      where: { id: jailId },
      include: { county: true, state: true },
    })

    if (!jail) {
      return NextResponse.json({ error: 'Jail not found' }, { status: 404 })
    }

    const where = {
      jailId,
      ...(search && {
        OR: [
          { inmateName: { contains: search, mode: 'insensitive' as const } },
          { bookingNumber: { contains: search, mode: 'insensitive' as const } },
        ],
      }),
    }

    const [rosters, total] = await Promise.all([
      prisma.roster.findMany({
        where,
        orderBy: { scrapeDate: 'desc' },
        skip,
        take: limit,
      }),
      prisma.roster.count({ where }),
    ])

    return NextResponse.json({
      data: rosters,
      meta: {
        total,
        page,
        limit,
        totalPages: Math.ceil(total / limit),
        jail: {
          id: jail.id,
          name: jail.name,
          county: jail.county.name,
          state: jail.state.abbrev,
        },
      },
    })
  } catch (error) {
    console.error('Error fetching roster:', error)
    return NextResponse.json({ error: 'Failed to fetch roster' }, { status: 500 })
  }
}