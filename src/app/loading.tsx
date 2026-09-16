import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'

export default function Loading() {
  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content" className="mx-auto w-full max-w-3xl px-5 py-24 text-center">
        <p className="text-[var(--muted)]">Loading…</p>
      </main>
      <Footer />
    </div>
  )
}
