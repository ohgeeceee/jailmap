import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Privacy Policy',
  description: 'How JailMap handles account information, saved searches, and public booking data. We exclude dates of birth and mugshot URLs from the public API by default.',
  alternates: { canonical: 'https://jailmap.com/privacy' },
  openGraph: {
    title: 'Privacy Policy | JailMap',
    description: 'How JailMap handles account information, saved searches, and public booking data. We exclude dates of birth and mugshot URLs from the public API by default.',
    url: 'https://jailmap.com/privacy',
    siteName: 'JailMap',
  },
}

export default function PrivacyPage() {
  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content" className="mx-auto w-full max-w-4xl px-5 py-16">
        <h1 className="text-4xl font-bold">Privacy Policy</h1>
        <p className="mt-3 text-lg text-[var(--muted)]">Last updated: September 2026</p>

        <div className="mt-12 space-y-12 text-base leading-relaxed text-[var(--ink)]">
          <section>
            <h2 className="text-2xl font-semibold">What we collect</h2>
            <p className="mt-3">We collect information you voluntarily provide when you create an account, save a search, create a watchlist, opt in to watchlist alerts, or submit a removal request. This includes your email address, name, saved names and location filters, and the details of any privacy review request you submit.</p>
            <p className="mt-3">If you make a payment for a privacy review, payment processing is handled by Stripe. We never store your credit card number, bank account, or other payment credentials.</p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold">How we use it</h2>
            <ul className="mt-3 list-disc list-inside space-y-2">
              <li>To provide the service — account authentication, saved searches, watchlists, optional alerts, and privacy review processing</li>
              <li>To communicate with you about your requests and opted-in watchlist alerts (no marketing without consent)</li>
              <li>To improve site reliability, security, and performance</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold">What we don&apos;t do</h2>
            <ul className="mt-3 list-disc list-inside space-y-2">
              <li>We don&apos;t sell your personal information</li>
              <li>We don&apos;t share your data with advertisers</li>
              <li>We don&apos;t scrape or aggregate your data from third-party sources</li>
              <li>We don&apos;t use your data to build marketing profiles</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold">Data you see on JailMap</h2>
            <p className="mt-3">Booking records displayed on JailMap are public records from official government sources — sheriff&apos;s offices, detention facilities, and their authorized vendors. We do not create this data. We display only what is already public, with direct links back to the source.</p>
            <p className="mt-3">We exclude date of birth, mugshots, residential address, and other sensitive identifiers from public display. A paid privacy review exists if you want your own name withheld from public pages.</p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold">Cookies</h2>
            <p className="mt-3">We use essential cookies to keep you logged in and to remember your preferences. We do not use tracking cookies, third-party analytics scripts, or advertising cookies.</p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold">Data retention</h2>
            <p className="mt-3">Account data is retained as long as your account is active. You can request deletion of your account and associated data at any time by contacting us. Payment records are retained as required by law.</p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold">Your rights</h2>
            <ul className="mt-3 list-disc list-inside space-y-2">
              <li>Access the personal data we hold about you</li>
              <li>Correct inaccurate information</li>
              <li>Delete your account and associated data</li>
              <li>Submit a correction or removal request for any record — free of charge</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold">Contact</h2>
            <p className="mt-3">For privacy questions, data deletion requests, or to exercise your rights, contact us at <a className="text-[var(--green)] hover:underline" href="mailto:getjailmap@gmail.com?subject=Privacy%20Request">getjailmap@gmail.com</a>.</p>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  )
}
