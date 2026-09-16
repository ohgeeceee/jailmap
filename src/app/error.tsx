'use client'

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="jm-theme">
      <header className="public-header">
        <div className="site-width header-row">
          <a href="/" className="brand">
            <span className="brand-mark">JM</span>
            <span> Jail<span className="brand-dot">·</span>Map</span>
          </a>
        </div>
      </header>
      <main id="main-content" className="mx-auto w-full max-w-3xl px-5 py-24 text-center">
        <p className="eyebrow">Something went wrong</p>
        <h1 className="mt-4 text-4xl font-bold">An error occurred</h1>
        <p className="mt-3 text-[var(--muted)]">
          {error?.message || 'An unexpected error occurred.'}
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-4">
          <button className="jm-button" onClick={reset}>Try again</button>
          <a className="jm-button secondary" href="/">Back to homepage</a>
        </div>
      </main>
    </div>
  )
}
