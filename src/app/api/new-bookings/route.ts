import { recordsGateway } from '@/lib/records-gateway'
export async function GET(request: Request) {
  const url = new URL(request.url)
  return recordsGateway(request, '/api/new-bookings' + url.search)
}
