import { pool } from '@/lib/db'

export const dynamic = 'force-dynamic'

export async function GET() {
  const states = await pool.query(`
    SELECT j.state, COUNT(DISTINCT j.county) AS covered, COUNT(i.id) AS records
    FROM records.jurisdictions j
    JOIN records.inmates i ON i.jurisdiction_id = j.id
    WHERE j.enabled = true
      AND j.review_status = 'verified'
      AND i.visibility = 'public'
      AND i.observed_at > now() - interval '48 hours'
    GROUP BY j.state ORDER BY j.state
  `)
  const normalized = states.rows.map(state => ({
    state: state.state,
    covered: Number(state.covered),
    records: Number(state.records),
  }))
  const total = normalized.reduce((sum, state) => sum + state.records, 0)
  return Response.json({ states: normalized, total })
}
