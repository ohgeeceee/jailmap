import { createHmac } from 'node:crypto'

export async function recordsGateway(request: Request, path: string, adminId?: string) {
  const base = process.env.RECORDS_API_URL
  const token = process.env.RECORDS_API_TOKEN
  if (!base || !token || token.length < 32) return Response.json({ detail: 'Records service is not configured' }, { status: 503 })
  // Set only behind a trusted edge that OVERWRITES this header and blocks direct access.
  // Without that configuration all visitors safely share one rate-limit bucket.
  const header = process.env.RECORDS_TRUSTED_CLIENT_HEADER
  const client = header ? (request.headers.get(header) ?? 'shared') : 'shared'
  try {
    let body: string | undefined
    if (request.method === 'POST') {
      const origin = process.env.APP_ORIGIN || `${new URL(request.url).protocol}//${request.headers.get('host')}`
      if (request.headers.get('origin') !== origin) return Response.json({ detail: 'Invalid origin' }, { status: 403 })
      if (!request.headers.get('content-type')?.startsWith('application/json')) return Response.json({ detail: 'JSON required' }, { status: 415 })
      const reader = request.body?.getReader()
      const chunks: Uint8Array[] = []
      let length = 0
      if (reader) while (true) {
        const { value, done } = await reader.read()
        if (done) break
        length += value.length
        if (length > 16384) { await reader.cancel(); return Response.json({ detail: 'Request too large' }, { status: 413 }) }
        chunks.push(value)
      }
      body = Buffer.concat(chunks).toString('utf8')
    }
    const response = await fetch(new URL(path, base), {
      method: request.method, cache: 'no-store', signal: AbortSignal.timeout(15000), body,
      headers: { 'content-type': 'application/json', 'x-gateway-token': token,
        ...(adminId ? { 'x-records-admin': adminId } : {}),
        'x-records-client': createHmac('sha256', token).update(client).digest('hex') },
    })
    return new Response(await response.text(), { status: response.status,
      headers: { 'content-type': 'application/json', 'cache-control': 'no-store',
        'x-robots-tag': 'noindex, noarchive', ...(response.headers.has('retry-after') ? { 'retry-after': response.headers.get('retry-after')! } : {}) } })
  } catch {
    return Response.json({ detail: 'Records service temporarily unavailable' }, { status: 503 })
  }
}
