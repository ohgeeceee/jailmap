import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Terms of Service',
  description: 'JailMap is a starting point for public-record research. Records may be incomplete or outdated — verify with the original source before relying on them.',
  alternates: { canonical: 'https://jailmap.com/terms' },
  openGraph: {
    title: 'Terms of Service | JailMap',
    description: 'JailMap is a starting point for public-record research. Records may be incomplete or outdated — verify with the original source before relying on them.',
    url: 'https://jailmap.com/terms',
    siteName: 'JailMap',
  },
}

export default function TermsPage() {
  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content" className="mx-auto w-full max-w-4xl px-5 py-16">
        <h1 className="text-4xl font-bold">Terms of Service</h1>
        <p className="mt-3 text-lg text-[var(--muted)]">Last updated: September 2026</p>

        <div className="mt-12 space-y-12 text-base leading-relaxed text-[var(--ink)]">
          <section>
            <h2 className="text-2xl font-semibold">About these terms</h2>
            <p className="mt-3">By using JailMap, you agree to these terms. If you don't agree, please don't use the service. These terms are written to be clear — not to bury anything.</p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold">The service</h2>
            <p className="mt-3">JailMap provides access to public booking records from official government sources across the United States. We aggregate, normalize, and publish records that are already public — with direct links to the original source.</p>
            <p className="mt-3">We are not a government agency. We are not affiliated with any sheriff's office, detention facility, or court. We do not create the records we display.</p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold">Responsible use</h2>
            <ul className="mt-3 list-disc list-inside space-y-2">
              <li>You may search and view public records for personal, journalistic, or research purposes</li>
              <li>You may not use the service to harass, stalk, discriminate against, or harm any individual</li>
              <li>You may not scrape, bulk-download, or systematically harvest records without written permission</li>
              <li>You may not misrepresent the source or accuracy of any record</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold">Privacy review payments</h2>
            <p className="mt-3">The $99 privacy review fee covers a human review of your name removal request. Payment does not guarantee removal — a reviewer assesses each request on its merits. If redaction is not warranted, the fee is retained for the review work performed.</p>
            <p className="mt-3">Refunds are available only if the review was not completed within the stated timeframe. Payment is processed by Stripe; we never see your card details.</p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold">Accuracy and limitations</h2>
            <p className="mt-3">We work hard to display records accurately, but we cannot guarantee completeness, timeliness, or correctness. Records are sourced from third parties and may contain errors. A name match does not establish identity.</p>
            <p className="mt-3">Always confirm information with the official source or the facility before taking action.</p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold">Accounts</h2>
            <p className="mt-3">You're responsible for keeping your account credentials secure. Notify us immediately if you suspect unauthorized access. We may suspend accounts that violate these terms.</p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold">Changes to these terms</h2>
            <p className="mt-3">We may update these terms. Material changes will be communicated via email or a prominent notice on the site. Continued use after changes means you accept the new terms.</p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold">Contact</h2>
            <p className="mt-3">Questions about these terms? Contact us at <a className="text-[var(--green)] hover:underline" href="mailto:getjailmap@gmail.com?subject=Terms%20and%20Legal%20Question">getjailmap@gmail.com</a>.</p>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  )
}
