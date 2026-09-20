import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import Link from 'next/link'
import { ArrowRight, Mail, ShieldCheck, Scale, FileWarning } from 'lucide-react'

export const metadata = {
  title: 'Trust & Safety',
  description: 'JailMap trust and safety policies — how we protect public records, handle abuse, and ensure responsible use.',
  alternates: { canonical: '/trust-safety' },
  openGraph: {
    title: 'Trust & Safety | JailMap',
    description: 'JailMap trust and safety policies — how we protect public records, handle abuse, and ensure responsible use.',
    url: 'https://jailmap.com/trust-safety',
    siteName: 'JailMap',
  },
}

export default function TrustSafetyPage() {
  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content">
        <section className="mx-auto w-full max-w-4xl px-5 py-16">
          <h1 className="text-4xl font-bold">Trust & Safety</h1>
          <p className="mt-3 text-lg text-[var(--muted)]">
            Public records, published responsibly. Our policies on data handling, abuse prevention, and responsible use.
          </p>
        </section>

        <section className="mx-auto w-full max-w-5xl px-5 pb-20">
          <div className="grid gap-8 md:grid-cols-3">
            <article className="flex flex-col">
              <ShieldCheck size={28} className="text-[var(--green)]" />
              <h2 className="mt-4 text-xl font-semibold">Data integrity</h2>
              <p className="mt-2 text-[var(--muted)]">We publish only from authorized official sources. Every record links to the original. We never alter, editorialize, or anonymize records — we present them as they appear on the source.</p>
            </article>
            <article className="flex flex-col">
              <Scale size={28} className="text-[var(--green)]" />
              <h2 className="mt-4 text-xl font-semibold">Responsible use</h2>
              <p className="mt-2 text-[var(--muted)]">Our terms prohibit using JailMap for employment, housing, credit, or insurance decisions. Harassment, stalking, discrimination, and circumventing access controls are forbidden.</p>
            </article>
            <article className="flex flex-col">
              <FileWarning size={28} className="text-[var(--green)]" />
              <h2 className="mt-4 text-xl font-semibold">Abuse prevention</h2>
              <p className="mt-2 text-[var(--muted)]">We rate-limit searches, block scrapers, and monitor for bulk harvesting. Violations result in account suspension and may be reported to law enforcement.</p>
            </article>
          </div>
        </section>

        <section className="mx-auto w-full max-w-4xl px-5 pb-20">
          <h2 className="text-2xl font-semibold">Our commitments</h2>
          <div className="mt-6 space-y-4">
            <article className="rounded-lg border border-[var(--line)] bg-white p-6">
              <h3 className="font-semibold">No PII in public records</h3>
              <p className="mt-2 text-[var(--muted)]">Date of birth, residential address, driver's license, SSN, and mugshots are excluded from public display by default.</p>
            </article>
            <article className="rounded-lg border border-[var(--line)] bg-white p-6">
              <h3 className="font-semibold">Free correction path</h3>
              <p className="mt-2 text-[var(--muted)]">Anyone can request a correction or removal — free, no account required. Every request is reviewed by a human.</p>
            </article>
            <article className="rounded-lg border border-[var(--line)] bg-white p-6">
              <h3 className="font-semibold">Presumption of innocence</h3>
              <p className="mt-2 text-[var(--muted)]">A booking is not a conviction. We display records without editorial judgment. We encourage users to verify with the source.</p>
            </article>
          </div>
        </section>

        <section className="mx-auto w-full max-w-4xl px-5 pb-20">
          <div className="rounded-lg bg-white border border-[var(--line)] p-8 text-center">
            <h2 className="text-2xl font-semibold">Report a concern</h2>
            <p className="mt-3 text-[var(--muted)]">See something that shouldn't be here? Have a safety concern? Contact us directly.</p>
            <a href="mailto:getjailmap@gmail.com?subject=Trust%20and%20Safety" className="jm-button mt-6 inline-flex">Contact Trust & Safety <ArrowRight size={18} className="ml-2" /></a>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}
