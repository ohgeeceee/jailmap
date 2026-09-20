export interface PublicStats {
  currentInmates: number
  counties: number
  facilities: number
  states: number
}

export async function getPublicStats(): Promise<PublicStats | null> {
  try {
    const { prisma } = await import('@/lib/prisma')
    const [row] = await prisma.$queryRawUnsafe<Array<{
      current_inmates: bigint
      counties: bigint
      facilities: bigint
      states: bigint
    }>>(`
      SELECT
        count(i.id) AS current_inmates,
        count(DISTINCT (j.state, j.county)) AS counties,
        count(DISTINCT j.id) AS facilities,
        count(DISTINCT j.state) AS states
      FROM records.inmates i
      JOIN records.jurisdictions j ON j.id = i.jurisdiction_id
      WHERE i.visibility = 'public'
        AND j.enabled
        AND j.review_status = 'verified'
        AND i.observed_at > now() - interval '48 hours'
    `)

    return {
      currentInmates: Number(row.current_inmates),
      counties: Number(row.counties),
      facilities: Number(row.facilities),
      states: Number(row.states),
    }
  } catch (error) {
    console.error('[public-stats] live statistics query failed:', error)
    return null
  }
}
