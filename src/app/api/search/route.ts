import { recordsGateway } from '@/lib/records-gateway'
import { cookies } from 'next/headers'
import { routeCheckCookie, routeClient, validRoutePermit } from '@/lib/search/route-check'
export async function GET(request: Request) {
  const permit = (await cookies()).get(routeCheckCookie)?.value
  if (!validRoutePermit(permit, routeClient(request.headers))) return Response.json({ detail: 'Complete the Route Check before searching.' }, { status: 428, headers: { 'Cache-Control': 'no-store' } })
  return recordsGateway(request, '/api/search' + new URL(request.url).search)
}
