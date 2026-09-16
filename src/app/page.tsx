import { NewBookingsPopup } from '@/components/records/NewBookingsPopup'
import Link from 'next/link'
import { ArrowRight, Bookmark, Check, Database, FileCheck2, Search, ShieldCheck } from 'lucide-react'
import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import { StateTiles } from '@/components/site/StateTiles'
import { US_STATES } from '@/lib/states'

const organizationLd = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  name: 'JailMap',
  url: 'https://jailmap.com',
  description:
    'Find public booking records from participating jurisdictions across the United States. Review charges, bond information and original sources.',
  sameAs: ['https://www.montanablotter.com'],
}

export default function HomePage() {
  return <div className="jm-theme"><PublicHeader /><main id="main-content">
    <NewBookingsPopup />
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationLd) }} />
    <section className="site-width hero-section">
      <div className="hero-copy"><span className="eyebrow"><span className="small-dot" />PUBLIC RECORDS, WITH PERSPECTIVE</span>
        <h1>Find the record.<br /><span>Understand<br className="desktop-break" /> the context.</span></h1>
        <p className="hero-description">A simpler way to find public booking information. Search participating jurisdictions, review the details, and go straight to the source.</p>
        <form className="hero-search" action="/search"><label htmlFor="home-name">Who are you looking for?</label><div className="hero-search-row"><div className="search-input-wrap"><Search size={20} /><input id="home-name" name="name" placeholder="Enter a first or last name" minLength={2} maxLength={100} required /></div><button className="jm-button" type="submit">Search <ArrowRight size={18} /></button></div><div className="hero-filter"><label htmlFor="home-state">Location</label><select id="home-state" name="state"><option value="">All supported states</option>{US_STATES.map(state => <option value={state.abbrev} key={state.abbrev}>{state.name}</option>)}</select><span>No account needed to search</span></div></form>
        <div className="hero-checks"><span><Check size={15} /> Source-linked records</span><span><Check size={15} /> Free correction requests</span></div>
      </div>
      <div className="hero-visual"><div className="visual-topline"><span className="visual-logo"><Database size={17} /> A CONNECTED VIEW</span><span className="visual-pill">Built around the source</span></div><StateTiles /><div className="visual-caption"><span>One place to start.<br /><strong>Every record has a source.</strong></span><span className="round-arrow"><ArrowRight size={23} /></span></div><div className="source-card"><div className="source-card-icon"><FileCheck2 size={24} /></div><div><strong>Details that matter</strong><p>Booking · Charges · Bond · Source</p></div><ShieldCheck size={21} className="source-shield" /></div><p className="coverage-note">State tiles are navigation, not a coverage map.<br />Available records depend on participating sources.</p></div>
    </section>
    <section className="trust-strip"><div className="site-width"><span>CLARITY COMES FIRST</span><p><ShieldCheck size={19} /> Presumed innocent</p><p><Database size={19} /> Authorized sources</p><p><FileCheck2 size={19} /> Transparent timestamps</p><p><Bookmark size={19} /> A workspace of your own</p></div></section>
    <section id="how-it-works" className="site-width how-section"><div className="section-heading"><div><span className="eyebrow">LESS SEARCHING. MORE UNDERSTANDING.</span><h2>A clear path to the details.</h2></div><p>Information can be scattered.<br />Your next step shouldn't be.</p></div><div className="feature-grid">{[
      { icon: Search, title: 'Start with a name', text: 'Search by first or last name, then narrow your results by state and county.' },
      { icon: FileCheck2, title: 'See the whole record', text: 'Review reported charges, individual bond terms, booking dates and the original source.' },
      { icon: Bookmark, title: 'Pick up where you left off', text: 'Create a free account to save search filters and keep your research organized.' },
    ].map((feature, index) => <article className="feature-card" key={feature.title}><div className="feature-top"><feature.icon size={25} /><span>0{index + 1}</span></div><h3>{feature.title}</h3><p>{feature.text}</p></article>)}</div></section>
    <section className="site-width responsibility-section"><div className="responsibility-icon"><ShieldCheck size={42} /></div><div><span className="eyebrow">PEOPLE ARE MORE THAN A RECORD</span><h2>A booking is not a conviction.</h2><p>All individuals are presumed innocent until proven guilty. Records can be incomplete or outdated, and a name match does not establish identity. Always confirm information with the facility.</p><Link className="text-link" href="/about">Read about our approach <ArrowRight size={16} /></Link></div></section>
    <section className="site-width account-cta"><div><span className="eyebrow">YOUR RESEARCH, ORGANIZED</span><h2>A little less starting over.</h2><p>Save searches. Manage your account. Return when you're ready.</p></div><Link className="jm-button" href="/register">Create your free account <ArrowRight size={18} /></Link></section>
  </main><Footer /></div>
}
