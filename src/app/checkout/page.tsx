import { Suspense } from 'react'
import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import { CheckoutForm } from '@/components/subscriptions/CheckoutForm'

export default function CheckoutPage() {
  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content">
        <section className="site-width info-page">
          <span className="eyebrow"><span className="small-dot" />SUBSCRIPTION CHECKOUT</span>
          <h1>Choose your plan</h1>
          <p className="info-intro">
            Select a tier and billing cycle. You can cancel anytime.
          </p>
        </section>

        <section className="site-width" style={{ paddingBlock: '0 48px' }}>
          <Suspense fallback={<div className="panel" style={{ maxWidth: 600, margin: '0 auto' }}><p className="panel-content">Loading checkout…</p></div>}><CheckoutForm /></Suspense>
        </section>
      </main>
      <Footer />
    </div>
  )
}
