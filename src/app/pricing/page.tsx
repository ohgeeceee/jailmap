import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import Link from 'next/link'

export const metadata = {
  title: 'Plans & Pricing',
  description: 'JailMap offers free search, free correction requests, and a paid privacy review for name removal. See plan details and pricing.',
}

export default function PricingPage() {
  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content">
        <section className="mx-auto w-full max-w-4xl px-5 py-16">
          <h1 className="text-4xl font-bold">Plans & Pricing</h1>
          <p className="mt-3 text-lg text-[var(--muted)]">
            Free search and free correction requests. A paid option exists only if you want your own name reviewed for removal.
          </p>
        </section>

        <section className="mx-auto w-full max-w-5xl px-5 pb-20">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {/* Free tier */}
            <article className="rounded-lg border border-[var(--line)] bg-white p-6 flex flex-col">
              <span className="eyebrow">Free</span>
              <h2 className="mt-2 text-2xl font-semibold">Search & corrections</h2>
              <p className="mt-3 text-3xl font-bold">$0</p>
              <p className="mt-3 text-[var(--muted)]">Search any participating jurisdiction and submit correction or removal requests at no charge.</p>
              <ul className="mt-6 space-y-2 text-sm text-[var(--ink)]">
                <li className="flex gap-2"><span>✓</span> Search all public bookings</li>
                <li className="flex gap-2"><span>✓</span> Filter by state and county</li>
                <li className="flex gap-2"><span>✓</span> Source-linked records</li>
                <li className="flex gap-2"><span>✓</span> Free correction requests</li>
                <li className="flex gap-2"><span>✓</span> Free removal requests</li>
                <li className="flex gap-2"><span>✓</span> Account with saved searches</li>
              </ul>
              <div className="mt-auto pt-6">
                <Link href="/register" className="jm-button full">Create free account</Link>
              </div>
            </article>

            {/* Paid tier */}
            <article className="rounded-lg border-2 border-[var(--green)] bg-white p-6 flex flex-col">
              <span className="eyebrow">One-time</span>
              <h2 className="mt-2 text-2xl font-semibold">Privacy review</h2>
              <p className="mt-3 text-3xl font-bold">$99</p>
              <p className="mt-3 text-[var(--muted)]">A human privacy review of your name removal request. Payment does not by itself remove a record.</p>
              <ul className="mt-6 space-y-2 text-sm text-[var(--ink)]">
                <li className="flex gap-2"><span>✓</span> Everything in Free</li>
                <li className="flex gap-2"><span>✓</span> Expedited privacy review</li>
                <li className="flex gap-2"><span>✓</span> Human reviewer assessment</li>
                <li className="flex gap-2"><span>✓</span> Name withheld from public pages where warranted</li>
                <li className="flex gap-2"><span>✓</span> Review completes in ~5 business days</li>
                <li className="flex gap-2"><span>−</span> Fee retained if redaction not warranted</li>
              </ul>
              <div className="mt-auto pt-6">
                <Link href="/name-removal" className="jm-button full">Request privacy review</Link>
              </div>
            </article>

            {/* API tier */}
            <article className="rounded-lg border border-[var(--line)] bg-white p-6 flex flex-col">
              <span className="eyebrow">Coming soon</span>
              <h2 className="mt-2 text-2xl font-semibold">API access</h2>
              <p className="mt-3 text-3xl font-bold">TBA</p>
              <p className="mt-3 text-[var(--muted)]">Programmatic access to booking records for verified researchers and organizations. Not available yet.</p>
              <ul className="mt-6 space-y-2 text-sm text-[var(--ink)]">
                <li className="flex gap-2"><span>•</span> Read-only API access</li>
                <li className="flex gap-2"><span>•</span> Rate-limited endpoints</li>
                <li className="flex gap-2"><span>•</span> Same public projection as the website</li>
                <li className="flex gap-2"><span>•</span> DOB and mugshots excluded</li>
              </ul>
              <div className="mt-auto pt-6">
                <span className="jm-button secondary full cursor-default">Notify me at launch</span>
              </div>
            </article>
          </div>
        </section>

        <section className="mx-auto w-full max-w-3xl px-5 pb-16">
          <h2 className="text-2xl font-semibold">Frequently asked questions</h2>
          <div className="mt-6 space-y-6">
            <div>
              <h3 className="font-semibold">Is search really free?</h3>
              <p className="mt-2 text-[var(--muted)]">Yes. Searching public booking records and submitting a correction or removal request costs nothing. There is no paywall on the public site.</p>
            </div>
            <div>
              <h3 className="font-semibold">Does paying remove my record?</h3>
              <p className="mt-2 text-[var(--muted)]">No. Payment covers a human privacy review. A reviewer decides whether to withhold your name from public pages based on the facts of your request. The underlying government record remains with its official source.</p>
            </div>
            <div>
              <h3 className="font-semibold">Where does the data come from?</h3>
              <p className="mt-2 text-[var(--muted)]">JailMap only aggregates records from authorized, official sources — county sheriff departments, detention facilities, and their official vendors. Every record links back to the original source.</p>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}
