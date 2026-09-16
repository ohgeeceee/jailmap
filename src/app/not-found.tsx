import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'

export default function NotFound() {
  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content" className="mx-auto w-full max-w-3xl px-5 py-24 text-center">
        <p className="eyebrow">404</p>
        <h1 className="mt-4 text-4xl font-bold">Page not found</h1>
        <p className="mt-3 text-[var(--muted)]">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-4">
          <a className="jm-button" href="/">Back to homepage</a>
          <a className="jm-button secondary" href="/search">Search records</a>
        </div>
      </main>
      <Footer />
    </div>
  )
}
