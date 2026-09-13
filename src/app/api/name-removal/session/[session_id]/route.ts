import { recordsGateway } from '@/lib/records-gateway'
export async function GET(request: Request, { params }: { params: Promise<{ session_id: string }> }) {
  const { session_id } = await params
  return recordsGateway(request, `/api/name-removal/session/${encodeURIComponent(session_id)}`)
}
