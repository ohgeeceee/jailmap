import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import { CheckoutSuccess } from '@/components/records/NameRemoval'

export const metadata = { title: 'Payment status', robots: { index: false, follow: false } }

export default function NameRemovalSuccessPage() {
  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content" className="mx-auto w-full max-w-2xl px-5 py-12">
        <h1 className="text-3xl font-bold">Name removal request</h1>
        <div className="mt-6"><CheckoutSuccess /></div>
        <p className="mt-6 text-sm text-[var(--muted)]">Keep your Stripe receipt email — it contains your checkout reference.</p>
      </main>
      <Footer />
    </div>
  )
}
