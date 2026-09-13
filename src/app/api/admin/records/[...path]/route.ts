import { currentAccount } from '@/lib/accounts/session'
import { recordsGateway } from '@/lib/records-gateway'
export const runtime = 'nodejs'
async function handle(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const user = await currentAccount()
  if (!user) return Response.json({ detail: 'Please sign in.' }, { status: 401 })
  if (user.role !== 'admin') return Response.json({ detail: 'Administrator access required.' }, { status: 403 })
  const path = (await context.params).path.join('/')
  if ((request.method === 'GET' && path === 'overview') || (request.method === 'POST' && /^corrections\/[0-9a-f-]{36}$/.test(path))) return recordsGateway(request, '/api/admin/' + path, user.id)
  return Response.json({ detail: 'Not found.' }, { status: 404 })
}
export { handle as GET, handle as POST }
