import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ countyId: string }> }
) {
  try {
    const { countyId } = await params
    const { searchParams } = new URL(request.url)
    const includeCounts = searchParams.get('includeCounts') === 'true'
    const search = searchParams.get('search') || ''
    const page = parseInt(searchParams.get('page') || '1')
    const limit = parseInt(searchParams.get('limit') || '20')
    const skip = (page - 1) * limit

    const county = await prisma.county.findUnique({
      where: { id: countyId },
    })

    if (!county) {
      return NextResponse.json({ error: 'County not found' }, { status: 404 })
    }

    const [jails, total] = await Promise.all([
      prisma.jail.findMany({
        where: {
          countyId,
          isActive: true,
          name: { contains: search, mode: 'insensitive' },
        },
        include: {
          _count: includeCounts ? { select: { rosters: true } } : false,
        },
        orderBy: { name: 'asc' },
        skip,
        take: limit,
      }),
      prisma.jail.count({
        where: {
          countyId,
          isActive: true,
          name: { contains: search, mode: 'insensitive' },
        },
      }),
    ])

    return NextResponse.json({
      data: jails,
      meta: {
        total,
        page,
        limit,
        totalPages: Math.ceil(total / limit),
      },
    })
  } catch (error) {
    console.error('Error fetching jails:', error)
    return NextResponse.json({ error: 'Failed to fetch jails' }, { status: 500 })
  }
}