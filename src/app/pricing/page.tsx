import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import Link from 'next/link'
import { ArrowRight, Check, Minus } from 'lucide-react'

export const metadata = {
  title: 'Plans & Pricing',
  description: 'JailMap offers free search and paid subscription tiers for alerts, exports, and API access. See plan details and pricing.',
  alternates: { canonical: '/pricing' },
  openGraph: {
    title: 'Plans & Pricing | JailMap',
    description: 'JailMap offers free search and paid subscription tiers for alerts, exports, and API access. See plan details and pricing.',
    url: 'https://jailmap.com/pricing',
    siteName: 'JailMap',
  },
}

const tiers = [
  {
    id: 'free',
    name: 'Free',
    price: '$0',
    period: 'forever',
    description: 'Search any participating jurisdiction and submit correction or removal requests at no charge.',
    features: [
      { text: 'Search all public bookings', included: true },
      { text: 'Filter by state and county', included: true },
      { text: 'Source-linked records', included: true },
      { text: 'Free correction requests', included: true },
      { text: 'Free removal requests', included: true },
      { text: 'Account with saved searches', included: true },
    ],
    cta: { href: '/register', label: 'Create free account' },
  },
  {
    id: 'basic',
    name: 'Basic Search / Alerts',
    price: '$9.99',
    period: '/ month',
    annualPrice: '$79.99/year',
    description: 'For general public, local observers, and families who want alerts and unlimited searches.',
    features: [
      { text: 'Everything in Free', included: true },
      { text: 'Unlimited site searches', included: true },
      { text: 'Up to 3 active inmate/facility tracking alerts', included: true },
      { text: 'Standard map overlay view', included: true },
      { text: 'Email notifications on roster changes', included: true },
      { text: 'CSV/JSON exports', included: false },
      { text: 'Advanced filtering', included: false },
    ],
    cta: { href: '/register?tier=basic', label: 'Subscribe' },
  },
  {
    id: 'pro',
    name: 'Pro / Investigator',
    price: '$49',
    period: '/ month',
    annualPrice: '$392/year',
    description: 'For bail bondsmen, legal assistants, and journalists who need exports and historical data.',
    features: [
      { text: 'Everything in Basic', included: true },
      { text: 'Unlimited facility alerts', included: true },
      { text: 'Historical timeline views', included: true },
      { text: 'CSV/JSON list exports (up to 1,000 records/mo)', included: true },
      { text: 'Advanced filtering (booking dates, charge classifications)', included: true },
      { text: 'API access', included: false },
    ],
    cta: { href: '/register?tier=pro', label: 'Subscribe' },
    featured: true,
  },
  {
    id: 'developer',
    name: 'Developer API (Starter)',
    price: '$149',
    period: '/ month',
    annualPrice: '$1,192/year',
    description: 'For local software apps and regional news outlets building on JailMap data.',
    features: [
      { text: 'Everything in Pro', included: true },
      { text: '25,000 API requests / month', included: true },
      { text: 'Real-time webhook notifications for roster changes', included: true },
      { text: 'Standard rate limits ($0.005 per additional call)', included: true },
      { text: 'Bulk data feeds', included: false },
      { text: 'Dedicated bandwidth', included: false },
    ],
    cta: { href: '/register?tier=developer', label: 'Subscribe' },
  },
  {
    id: 'enterprise',
    name: 'Enterprise / Data Stream',
    price: '$499',
    period: '/ month',
    annualPrice: '$3,992/year',
    description: 'For insurance, background screening, and enterprise customers with high-volume needs.',
    features: [
      { text: 'Everything in Developer', included: true },
      { text: '150,000+ API requests / month', included: true },
      { text: 'Full state or national bulk data feeds', included: true },
      { text: 'Dedicated bandwidth and SLA support', included: true },
      { text: 'Custom integrations', included: true },
      { text: 'Priority support', included: true },
    ],
    cta: { href: '/register?tier=enterprise', label: 'Contact us' },
  },
]

export default function PricingPage() {
  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content">
        <section className="site-width info-page">
          <span className="eyebrow"><span className="small-dot" />PLANS & PRICING</span>
          <h1>Free search. Paid alerts & API.</h1>
          <p className="info-intro">
            Search is always free. Subscribe for alerts, exports, and programmatic access.
          </p>
        </section>

        <section className="site-width" style={{ paddingBlock: '0 48px' }}>
          <div className="pricing-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))' }}>
            {tiers.map((tier) => (
              <article key={tier.id} className={`pricing-card${tier.featured ? ' featured' : ''}`}>
                {tier.featured && <div className="pricing-popular">MOST POPULAR</div>}
                <div className="pricing-head">
                  <span className="eyebrow">{tier.name}</span>
                  <h2>{tier.name}</h2>
                  <div className="pricing-amount">
                    <span className="price">{tier.price}</span>
                    <span className="period">{tier.period}</span>
                  </div>
                  {tier.annualPrice && (
                    <p style={{ fontSize: '0.85rem', color: 'var(--jm-text-secondary)', margin: '4px 0 0' }}>
                      or {tier.annualPrice} (20% off)
                    </p>
                  )}
                  <p>{tier.description}</p>
                </div>
                <ul className="pricing-features">
                  {tier.features.map((feature, i) => (
                    <li key={i}>
                      {feature.included ? <Check size={14} /> : <Minus size={14} />}
                      {feature.text}
                    </li>
                  ))}
                </ul>
                <Link href={tier.cta.href} className="jm-button full">{tier.cta.label}</Link>
              </article>
            ))}
          </div>
        </section>

        {/* Comparison table */}
        <section className="site-width" style={{ paddingBlock: '0 64px' }}>
          <div className="section-heading"><div><span className="eyebrow">COMPARE PLANS</span><h2>Everything you get.</h2></div></div>
          <div className="comparison-table">
            <table>
              <thead>
                <tr>
                  <th>Feature</th>
                  <th>Free</th>
                  <th className="popular-col">Basic</th>
                  <th>Pro</th>
                  <th>Developer</th>
                  <th>Enterprise</th>
                </tr>
              </thead>
              <tbody>
                <tr><td>Public booking search</td><td><Check size={14} /></td><td><Check size={14} /></td><td><Check size={14} /></td><td><Check size={14} /></td><td><Check size={14} /></td></tr>
                <tr><td>Filter by state / county</td><td><Check size={14} /></td><td><Check size={14} /></td><td><Check size={14} /></td><td><Check size={14} /></td><td><Check size={14} /></td></tr>
                <tr><td>Source-linked records</td><td><Check size={14} /></td><td><Check size={14} /></td><td><Check size={14} /></td><td><Check size={14} /></td><td><Check size={14} /></td></tr>
                <tr><td>Saved searches & account</td><td><Check size={14} /></td><td><Check size={14} /></td><td><Check size={14} /></td><td><Check size={14} /></td><td><Check size={14} /></td></tr>
                <tr><td>Correction requests</td><td><Check size={14} /></td><td><Check size={14} /></td><td><Check size={14} /></td><td><Check size={14} /></td><td><Check size={14} /></td></tr>
                <tr><td>Tracking alerts (email)</td><td>—</td><td><Check size={14} /></td><td><Check size={14} /></td><td><Check size={14} /></td><td><Check size={14} /></td></tr>
                <tr><td>Historical timeline views</td><td>—</td><td>—</td><td><Check size={14} /></td><td><Check size={14} /></td><td><Check size={14} /></td></tr>
                <tr><td>CSV/JSON exports</td><td>—</td><td>—</td><td><Check size={14} /></td><td><Check size={14} /></td><td><Check size={14} /></td></tr>
                <tr><td>Advanced filtering</td><td>—</td><td>—</td><td><Check size={14} /></td><td><Check size={14} /></td><td><Check size={14} /></td></tr>
                <tr><td>API access</td><td>—</td><td>—</td><td>—</td><td><Check size={14} /></td><td><Check size={14} /></td></tr>
                <tr><td>Bulk data feeds</td><td>—</td><td>—</td><td>—</td><td>—</td><td><Check size={14} /></td></tr>
                <tr><td>Dedicated bandwidth & SLA</td><td>—</td><td>—</td><td>—</td><td>—</td><td><Check size={14} /></td></tr>
                <tr><td>Cost</td><td>$0</td><td>$9.99/mo</td><td>$49/mo</td><td>$149/mo</td><td>$499/mo</td></tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* API Overage Rates */}
        <section className="site-width" style={{ paddingBlock: '0 64px' }}>
          <div className="section-heading"><div><span className="eyebrow">API OVERAGE RATES</span><h2>Pay for what you use.</h2></div></div>
          <div className="panel">
            <div className="panel-content">
              <p>Developer and Enterprise tiers include a base API request allowance. Additional requests are billed at tiered overage rates:</p>
              <table style={{ width: '100%', marginTop: '16px', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', padding: '8px', borderBottom: '1px solid var(--jm-border)' }}>Tier</th>
                    <th style={{ textAlign: 'left', padding: '8px', borderBottom: '1px solid var(--jm-border)' }}>Included</th>
                    <th style={{ textAlign: 'left', padding: '8px', borderBottom: '1px solid var(--jm-border)' }}>Overage Rate</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style={{ padding: '8px', borderBottom: '1px solid var(--jm-border)' }}>Developer</td>
                    <td style={{ padding: '8px', borderBottom: '1px solid var(--jm-border)' }}>25,000 requests/mo</td>
                    <td style={{ padding: '8px', borderBottom: '1px solid var(--jm-border)' }}>$0.005/request (under 50k), $0.003/request (above 100k)</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', borderBottom: '1px solid var(--jm-border)' }}>Enterprise</td>
                    <td style={{ padding: '8px', borderBottom: '1px solid var(--jm-border)' }}>150,000+ requests/mo</td>
                    <td style={{ padding: '8px', borderBottom: '1px solid var(--jm-border)' }}>$0.003/request (above 100k)</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* FAQ */}
        <section className="site-width" style={{ paddingBlock: '0 80px' }}>
          <div className="section-heading"><div><span className="eyebrow">FREQUENTLY ASKED</span><h2>Common questions.</h2></div></div>
          <div className="faq-grid">
            <article className="faq-card">
              <h3>Is search really free?</h3>
              <p>Yes. Searching public booking records and submitting a correction or removal request costs nothing. There is no paywall on the public site.</p>
            </article>
            <article className="faq-card">
              <h3>What do I get with a paid subscription?</h3>
              <p>Paid tiers add tracking alerts, CSV/JSON exports, historical timeline views, advanced filtering, and API access depending on the tier.</p>
            </article>
            <article className="faq-card">
              <h3>How does annual billing work?</h3>
              <p>Annual subscriptions receive a 20% discount. For example, Basic is $79.99/year instead of $9.99/month, and Pro is $392/year instead of $49/month.</p>
            </article>
            <article className="faq-card">
              <h3>What happens if I exceed my API request limit?</h3>
              <p>Additional requests are billed at the overage rate for your tier. Developer tier: $0.005/request under 50k, $0.003/request above 100k. Enterprise: $0.003/request above 100k.</p>
            </article>
            <article className="faq-card">
              <h3>Can I cancel anytime?</h3>
              <p>Yes. Monthly subscriptions can be cancelled at any time and remain active until the end of the billing period. Annual subscriptions are non-refundable after 30 days.</p>
            </article>
            <article className="faq-card">
              <h3>Do you sell data?</h3>
              <p>No. JailMap does not sell or license personal data. We are a free public service for transparency and accountability.</p>
            </article>
          </div>
        </section>

        <section className="site-width" style={{ paddingBlock: '0 80px' }}>
          <div className="responsibility-section">
            <div className="responsibility-icon"><ArrowRight size={42} /></div>
            <div>
              <span className="eyebrow">READY TO GET STARTED?</span>
              <h2>Search now or create a free account.</h2>
              <p>No credit card required. Start searching public records in seconds.</p>
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '16px' }}>
                <Link className="jm-button" href="/search">Search records</Link>
                <Link className="jm-button secondary" href="/register">Create free account</Link>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}
