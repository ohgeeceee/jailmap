import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const includeCounts = searchParams.get('includeCounts') === 'true'

    const states = await prisma.state.findMany({
      include: {
        _count: includeCounts ? { select: { counties: true, jails: { where: { isActive: true } } } } : false,
      },
      orderBy: { name: 'asc' },
    })

    return NextResponse.json({ data: states })
  } catch (error) {
    console.error('Error fetching states:', error)
    return NextResponse.json({ error: 'Failed to fetch states' }, { status: 500 })
  }
}
