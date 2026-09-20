import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'

export const metadata = {
  title: 'Legal & Compliance',
  description: 'JailMap legal information — DMCA, data subject requests, and regulatory compliance.',
  alternates: { canonical: '/legal' },
  openGraph: {
    title: 'Legal & Compliance | JailMap',
    description: 'JailMap legal information — DMCA, data subject requests, and regulatory compliance.',
    url: 'https://jailmap.com/legal',
    siteName: 'JailMap',
  },
}

export default function LegalPage() {
  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content" className="mx-auto w-full max-w-4xl px-5 py-16">
        <h1 className="text-4xl font-bold">Legal & Compliance</h1>
        <p className="mt-3 text-lg text-[var(--muted)]">DMCA, data subject requests, and how JailMap complies with applicable laws.</p>

        <div className="mt-12 space-y-12 text-base leading-relaxed text-[var(--ink)]">
          <section>
            <h2 className="text-2xl font-semibold">DMCA & copyright</h2>
            <p className="mt-3">JailMap respects intellectual property rights. If you believe content on JailMap infringes your copyright, send a DMCA notice to our designated agent including: identification of the copyrighted work, the infringing material's URL, your contact information, and a good-faith statement.</p>
            <p className="mt-3">DMCA Agent: <a className="text-[var(--green)] hover:underline" href="mailto:getjailmap@gmail.com?subject=DMCA%20Notice">getjailmap@gmail.com</a></p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold">Data subject requests</h2>
            <p className="mt-3">Under applicable state laws (including California's CCPA/CPRA and similar statutes), you have the right to know what personal information we hold, request deletion, and opt out of data sales (we don't sell data).</p>
            <p className="mt-3">Submit requests to: <a className="text-[var(--green)] hover:underline" href="mailto:getjailmap@gmail.com?subject=Data%20Subject%20Request">getjailmap@gmail.com</a></p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold">Public records disclaimer</h2>
            <p className="mt-3">Booking records displayed on JailMap are public records from official government sources. We do not create this data. We display only what is already public, with attribution.</p>
            <p className="mt-3">If you believe a record is inaccurate, you can submit a free correction request directly from the record page. For removal of your own name, see our <a className="text-[var(--green)] hover:underline" href="/name-removal">privacy review</a> page.</p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold">State-specific compliance</h2>
            <p className="mt-3">We comply with state-specific public records and privacy laws across all 50 states. This includes redaction requirements, retention limits, and reporting obligations. Our privacy review process handles state-specific name removal requests.</p>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  )
}
