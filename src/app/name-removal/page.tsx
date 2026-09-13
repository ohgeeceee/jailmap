import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import { NameRemovalForm } from '@/components/records/NameRemoval'

export const metadata = { title: 'Request name removal | JailMap', robots: { index: false, follow: false } }

export default async function NameRemovalPage({ searchParams }: { searchParams: Promise<{ name?: string }> }) {
  const { name } = await searchParams
  const prefilled = typeof name === 'string' && name.length <= 120 ? name : undefined
  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content" className="mx-auto w-full max-w-2xl px-5 py-12">
        <h1 className="text-3xl font-bold">Request name removal</h1>
        <section className="mt-6 space-y-4 text-[15px] leading-6">
          <p>JailMap republishes booking data from official public sources. If a record naming you appears here, you can request a privacy review for a one-time <strong>$99</strong> fee.</p>
          <p>Payment covers a human privacy review of your request. <strong>Payment does not by itself remove a record.</strong> A reviewer approves redaction where appropriate (for example after dismissal, expungement, or where the law requires it) and the name is then withheld from public pages as &ldquo;Name withheld per privacy request&rdquo;. The underlying government record remains with its official source.</p>
          <p className="text-sm text-[var(--muted)]">Requests are handled in order; most reviews complete within 5 business days. The fee is retained for requests where redaction is not warranted, and covers the review itself.</p>
        </section>
        <section className="mt-8 rounded border border-[var(--line)] bg-white p-6">
          <h2 className="text-xl font-semibold">Submit your request</h2>
          <p className="mt-2 mb-4 text-sm text-[var(--muted)]">You will be redirected to Stripe&rsquo;s secure checkout. We never see your card details.</p>
          <NameRemovalForm prefilledName={prefilled} />
        </section>
      </main>
      <Footer />
    </div>
  )
}
