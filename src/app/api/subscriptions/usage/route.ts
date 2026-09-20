import { recordsGateway } from '@/lib/records-gateway'
export async function GET(request: Request) { return recordsGateway(request, '/api/subscriptions/usage') }
