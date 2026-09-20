import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import { NameRemovalForm } from '@/components/records/NameRemoval'

export const metadata = {
  title: 'Request name removal',
  description: 'Request a privacy review of a booking record on JailMap. A $99 human review determines whether a name is withheld from public pages.',
  alternates: { canonical: 'https://jailmap.com/name-removal' },
  openGraph: {
    title: 'Request name removal | JailMap',
    description: 'Request a privacy review of a booking record on JailMap. A $99 human review determines whether a name is withheld from public pages.',
    url: 'https://jailmap.com/name-removal',
  },
}

export default async function NameRemovalPage({ searchParams }: { searchParams: Promise<{ name?: string }> }) {
  const { name } = await searchParams
  const prefilled = typeof name === 'string' && name.length <= 120 ? name : undefined
  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content" className="site-width name-removal-page">
        <h1>Request name removal</h1>
        <section className="info-section">
          <p>JailMap republishes booking data from official public sources. If a record naming you appears here, you can request a privacy review for a one-time <strong>$99</strong> fee.</p>
          <p>Payment covers a human privacy review of your request. <strong>Payment does not by itself remove a record.</strong> A reviewer approves redaction where appropriate (for example after dismissal, expungement, or where the law requires it) and the name is then withheld from public pages as "Name withheld per privacy request". The underlying government record remains with its official source.</p>
          <p className="field-hint">Requests are handled in order; most reviews complete within 5 business days. The fee is retained for requests where redaction is not warranted, and covers the review itself.</p>
        </section>
        <section className="form-section">
          <h2>Submit your request</h2>
          <p className="field-hint">You will be redirected to Stripe's secure checkout. We never see your card details.</p>
          <NameRemovalForm prefilledName={prefilled} />
        </section>
      </main>
      <Footer />
    </div>
  )
}