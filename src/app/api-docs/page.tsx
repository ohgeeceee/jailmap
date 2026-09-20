import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import Link from 'next/link'
import { ArrowRight, Check, Code2, Database, Key, ShieldCheck } from 'lucide-react'

export const metadata = {
  title: 'API Access',
  description: 'Programmatic access to JailMap booking records for verified researchers and organizations.',
  alternates: { canonical: '/api-docs' },
  openGraph: {
    title: 'API Access | JailMap',
    description: 'Programmatic access to JailMap booking records for verified researchers and organizations.',
    url: 'https://jailmap.com/api-docs',
    siteName: 'JailMap',
  },
}

export default function ApiDocsPage() {
  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content">
        <section className="mx-auto w-full max-w-4xl px-5 py-16">
          <h1 className="text-4xl font-bold">API access</h1>
          <p className="mt-3 text-lg text-[var(--muted)]">
            Read-only programmatic access to public booking records. Available for verified researchers, journalists, and organizations.
          </p>
        </section>

        <section className="mx-auto w-full max-w-5xl px-5 pb-20">
          <div className="grid gap-8 md:grid-cols-3">
            <article className="flex flex-col">
              <Key size={28} className="text-[var(--green)]" />
              <h2 className="mt-4 text-xl font-semibold">API keys</h2>
              <p className="mt-2 text-[var(--muted)]">Authenticate with a bearer token. Rate-limited per key. No card required for read access.</p>
            </article>
            <article className="flex flex-col">
              <Database size={28} className="text-[var(--green)]" />
              <h2 className="mt-4 text-xl font-semibold">Public projection</h2>
              <p className="mt-2 text-[var(--muted)]">The API exposes the same public fields as the website — DOB and mugshots excluded.</p>
            </article>
            <article className="flex flex-col">
              <ShieldCheck size={28} className="text-[var(--green)]" />
              <h2 className="mt-4 text-xl font-semibold">Attribution required</h2>
              <p className="mt-2 text-[var(--muted)]">You must link back to JailMap and the original source when publishing data.</p>
            </article>
          </div>
        </section>

        <section className="mx-auto w-full max-w-4xl px-5 pb-20">
          <h2 className="text-2xl font-semibold">Endpoints</h2>
          <div className="mt-6 space-y-4">
            <article className="rounded-lg border border-[var(--line)] bg-white p-6">
              <div className="flex items-center gap-2">
                <span className="rounded bg-green-100 px-2 py-1 text-xs font-mono text-green-800">GET</span>
                <code className="font-mono text-sm">/api/v1/records</code>
              </div>
              <p className="mt-2 text-[var(--muted)]">Search booking records. Query parameters: name, state, county, booking_date, limit.</p>
            </article>
            <article className="rounded-lg border border-[var(--line)] bg-white p-6">
              <div className="flex items-center gap-2">
                <span className="rounded bg-green-100 px-2 py-1 text-xs font-mono text-green-800">GET</span>
                <code className="font-mono text-sm">/api/v1/records/{'{id}'}</code>
              </div>
              <p className="mt-2 text-[var(--muted)]">Retrieve a single booking record by ID with source attribution.</p>
            </article>
            <article className="rounded-lg border border-[var(--line)] bg-white p-6">
              <div className="flex items-center gap-2">
                <span className="rounded bg-green-100 px-2 py-1 text-xs font-mono text-green-800">GET</span>
                <code className="font-mono text-sm">/api/v1/jurisdictions</code>
              </div>
              <p className="mt-2 text-[var(--muted)]">List participating jurisdictions with source metadata.</p>
            </article>
          </div>
        </section>

        <section className="mx-auto w-full max-w-4xl px-5 pb-20">
          <div className="rounded-lg bg-white border border-[var(--line)] p-8 text-center">
            <h2 className="text-2xl font-semibold">Request access</h2>
            <p className="mt-3 text-[var(--muted)]">API access is currently limited to verified accounts. Apply below and we'll get back to you.</p>
            <a href="mailto:getjailmap@gmail.com?subject=API%20Access%20Request" className="jm-button mt-6 inline-flex">Apply for API access <ArrowRight size={18} className="ml-2" /></a>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}
