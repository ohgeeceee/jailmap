import { recordsGateway } from '@/lib/records-gateway'
export async function GET(request: Request, context: { params: Promise<{ booking_id: string }> }) {
  const { booking_id } = await context.params
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(booking_id)) return Response.json({ detail: 'Invalid booking ID' }, { status: 400 })
  return recordsGateway(request, '/api/inmate/' + booking_id)
}
