import { recordsGateway } from '@/lib/records-gateway'
export async function DELETE(request: Request, { params }: { params: Promise<{ key_prefix: string }> }) {
  const { key_prefix } = await params
  return recordsGateway(request, `/api/subscriptions/keys/${key_prefix}`)
}
