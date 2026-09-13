import { recordsGateway } from '@/lib/records-gateway'
export async function POST(request: Request) { return recordsGateway(request, '/api/name-removal/checkout') }
