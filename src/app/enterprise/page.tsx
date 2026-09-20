import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import Link from 'next/link'
import { ArrowRight, Building2, Check, Code2, Database, Mail, ShieldCheck } from 'lucide-react'

export const metadata = {
  title: 'Enterprise & Government',
  description: 'JailMap for enterprise and government — bulk data access, custom integrations, and research partnerships.',
  alternates: { canonical: '/enterprise' },
  openGraph: {
    title: 'Enterprise & Government | JailMap',
    description: 'JailMap for enterprise and government — bulk data access, custom integrations, and research partnerships.',
    url: 'https://jailmap.com/enterprise',
    siteName: 'JailMap',
  },
}

const testimonials = [
  { quote: "JailMap's normalized data feed cut our research time by weeks. The source attribution is a game-changer for legal citation.", author: "Policy Research Director", org: "National criminal justice nonprofit" },
  { quote: "Reliable, well-documented, and transparent. We use it daily for background verification on public records.", org: "Investigative newsroom" },
  { quote: "The only platform we've found that covers jurisdictions others miss. The API is clean and predictable.", org: "Legal technology firm" },
]

export default function EnterprisePage() {
  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content">
        <section className="site-width info-page">
          <span className="eyebrow"><span className="small-dot" />ENTERPRISE & GOVERNMENT</span>
          <h1>Built for organizations that need public records at scale.</h1>
          <p className="info-intro">From newsrooms to research institutions — JailMap provides reliable access to official booking records across all 50 states.</p>
        </section>

        {/* Compliance badges */}
        <section className="site-width" style={{ paddingBlock: '0 48px' }}>
          <div className="compliance-badges">
            <div className="compliance-badge"><ShieldCheck size={20} /><span>SOC 2 Type II</span><small>In progress — Expected 2027</small></div>
            <div className="compliance-badge"><ShieldCheck size={20} /><span>Criminal Justice Info Services (CJIS)</span><small>Compliance in progress</small></div>
            <div className="compliance-badge"><ShieldCheck size={20} /><span>State Privacy Laws</span><small>CCPA, CPRA, and 20+ state statutes</small></div>
            <div className="compliance-badge"><ShieldCheck size={20} /><span>FOIA-Aware Sourcing</span><small>Only authorized official sources</small></div>
          </div>
        </section>

        {/* Capabilities */}
        <section className="site-width" style={{ paddingBlock: '0 64px' }}>
          <div className="section-heading"><div><span className="eyebrow">CAPABILITIES</span><h2>What enterprise customers get.</h2></div></div>
          <div className="feature-grid">
            <article className="feature-card">
              <div className="feature-top"><Database size={25} /><span>01</span></div>
              <h3>Bulk data licensing</h3>
              <p>Structured, normalized data feeds with full source attribution. Historical archives available. Custom extracts for research use cases.</p>
            </article>
            <article className="feature-card">
              <div className="feature-top"><Code2 size={25} /><span>02</span></div>
              <h3>API & integrations</h3>
              <p>RESTful API with rate limits that match your use case. Webhooks for real-time updates. SDKs for Python and Node.js.</p>
            </article>
            <article className="feature-card">
              <div className="feature-top"><ShieldCheck size={25} /><span>03</span></div>
              <h3>Compliance-ready</h3>
              <p>Source-linked records, audit trails, and documented provenance for legal and research use. Data retention policies aligned with state requirements.</p>
            </article>
          </div>
        </section>

        {/* Who uses JailMap */}
        <section className="site-width" style={{ paddingBlock: '0 64px' }}>
          <div className="section-heading"><div><span className="eyebrow">TRUSTED BY</span><h2>Who uses JailMap</h2></div></div>
          <div className="feature-grid">
            <article className="feature-card">
              <div className="feature-top"><Building2 size={25} /><span>01</span></div>
              <h3>Newsrooms</h3>
              <p>Investigative journalists and news organizations tracking booking trends and verifying public records.</p>
            </article>
            <article className="feature-card">
              <div className="feature-top"><ShieldCheck size={25} /><span>02</span></div>
              <h3>Researchers</h3>
              <p>Academic and policy researchers studying criminal justice data with full source attribution.</p>
            </article>
            <article className="feature-card">
              <div className="feature-top"><Database size={25} /><span>03</span></div>
              <h3>Legal professionals</h3>
              <p>Attorneys and paralegals verifying custody status and booking details across jurisdictions.</p>
            </article>
          </div>
        </section>

        {/* Testimonials */}
        <section className="site-width" style={{ paddingBlock: '0 64px' }}>
          <div className="section-heading"><div><span className="eyebrow">WHAT CUSTOMERS SAY</span></div></div>
          <div className="testimonial-grid">
            {testimonials.map((t, i) => (
              <blockquote className="testimonial-card" key={i}>
                <p>"{t.quote}"</p>
                <footer>
                  {t.author && <strong>{t.author}</strong>}
                  <span>{t.org}</span>
                </footer>
              </blockquote>
            ))}
          </div>
        </section>

        <section className="site-width" style={{ paddingBlock: '0 80px' }}>
          <div className="responsibility-section">
            <div className="responsibility-icon"><Mail size={42} /></div>
            <div>
              <span className="eyebrow">TALK TO OUR TEAM</span>
              <h2>Custom pricing, data licensing, and integration support.</h2>
              <p>Tell us about your use case. We'll respond within one business day.</p>
              <a className="jm-button" href="mailto:getjailmap@gmail.com?subject=Enterprise%20Inquiry">Contact sales <ArrowRight size={18} /></a>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}
