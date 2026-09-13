import { database } from '@/lib/accounts/store'
export const dynamic = 'force-dynamic'
export async function GET() {
  try {
    database().prepare('SELECT 1').get()
    const base = process.env.RECORDS_API_URL
    if (!base) throw new Error('Records service not configured')
    const response = await fetch(new URL('/healthz', base), { cache: 'no-store', signal: AbortSignal.timeout(5000) })
    if (!response.ok) throw new Error('Records service unavailable')
    return Response.json({ status: 'ok' }, { headers: { 'Cache-Control': 'no-store' } })
  } catch {
    return Response.json({ status: 'unavailable' }, { status: 503, headers: { 'Cache-Control': 'no-store' } })
  }
}
