import type { Metadata } from 'next'
import { US_STATES } from '@/lib/states'
import Link from 'next/link'
import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import { StateTiles } from '@/components/site/StateTiles'
import { ArrowRight, Check, Database, Search, ShieldCheck, Users, Bookmark, FileCheck2, Globe, Landmark } from 'lucide-react'
import { getPublicStats } from '@/lib/public-stats'

export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: 'Jail Roster Search — Find Inmate Records Across All 50 States',
  description: 'Search current jail rosters from participating U.S. jurisdictions. Find public booking records, charges, bond information, timestamps, and official sources.',
  alternates: { canonical: '/jail-roster' },
  openGraph: {
    type: 'website',
    url: 'https://jailmap.com/jail-roster',
    title: 'Jail Roster Search — Find Inmate Records Across All 50 States',
    description: 'Search current jail rosters and source-linked public booking records from participating U.S. jurisdictions.',
  },
}

const faqLd = {
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: [
    {
      '@type': 'Question',
      name: 'What is a jail roster?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'A jail roster is a public record listing individuals currently detained in a county jail or detention facility. It typically includes names, booking dates, charges, and bond information.',
      },
    },
    {
      '@type': 'Question',
      name: 'How do I search for someone in jail?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Use the search bar above to enter a first or last name, then optionally filter by state and county. Results show matching booking records from participating jurisdictions.',
      },
    },
    {
      '@type': 'Question',
      name: 'Is jail roster information public?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Yes. Jail rosters are public records maintained by county sheriff departments and detention facilities. JailMap aggregates only authorized official sources.',
      },
    },
    {
      '@type': 'Question',
      name: 'How often are jail rosters updated?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'JailMap ingests from each source on a regular schedule — typically every 2 to 6 hours for active jurisdictions. Records not refreshed within 48 hours are hidden.',
      },
    },
    {
      '@type': 'Question',
      name: 'Can I request removal of my name from a jail roster?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'You can submit a free correction request from any record page. For a human privacy review of your name removal, a $99 paid review is available. Payment does not guarantee removal — a reviewer decides based on the facts.',
      },
    },
  ],
}

export default async function JailRosterPage() {
  const stats = await getPublicStats()

  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content">
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqLd) }} />

        <section className="site-width hero-section">
          <div className="hero-copy">
            <span className="eyebrow"><span className="small-dot" />JAIL ROSTER SEARCH</span>
            <h1>Find jail rosters across<br /><span>all 50 states.</span></h1>
            <p className="hero-description">Search current booking records from participating jurisdictions. Review charges, bond information, timestamps, and source-linked data from authorized official sources.</p>
            <form className="hero-search" action="/search">
              <label htmlFor="jr-name">Who are you looking for?</label>
              <div className="hero-search-row">
                <div className="search-input-wrap">
                  <Search size={20} />
                  <input id="jr-name" name="name" placeholder="Enter a first or last name" minLength={2} maxLength={100} required />
                </div>
                <button className="jm-button" type="submit">Search <ArrowRight size={18} /></button>
              </div>
              <div className="hero-filter">
                <label htmlFor="jr-state">State</label>
                <select id="jr-state" name="state">
                  <option value="">All states</option>
                  {US_STATES.map(state => <option value={state.abbrev} key={state.abbrev}>{state.name}</option>)}
                </select>
                <span>No account needed</span>
              </div>
            </form>
            <div className="hero-checks">
              <span><Check size={15} /> Free to search</span>
              <span><Check size={15} /> Participating counties</span>
              <span><Check size={15} /> Source-linked records</span>
            </div>
          </div>
          <div className="hero-visual">
            <div className="visual-topline">
              <span className="visual-logo"><Database size={17} /> A CONNECTED VIEW</span>
              <span className="visual-pill">Built around the source</span>
            </div>
            <StateTiles />
            <div className="visual-caption">
              <span>One place to start.<br /><strong>Every record has a source.</strong></span>
              <span className="round-arrow"><ArrowRight size={23} /></span>
            </div>
          </div>
        </section>

        <section className="trust-strip">
          <div className="site-width">
            <span>TRUSTED BY JOURNALISTS, RESEARCHERS &amp; LEGAL TEAMS</span>
            <p><ShieldCheck size={19} /> Presumed innocent</p>
            <p><Database size={19} /> Authorized sources only</p>
            <p><FileCheck2 size={19} /> Transparent timestamps</p>
            <p><Bookmark size={19} /> Free to use</p>
          </div>
        </section>

        <section className="site-width how-section">
          <div className="section-heading">
            <div>
              <span className="eyebrow">HOW IT WORKS</span>
              <h2>Find the record. Understand the context.</h2>
            </div>
            <p>Jail roster information can be scattered across hundreds of county websites. JailMap brings it together.</p>
          </div>
          <div className="feature-grid">
            <article className="feature-card">
              <div className="feature-top"><Search size={25} /><span>01</span></div>
              <h3>Search by name</h3>
              <p>Enter a first or last name, then narrow by state and county. Results update in real time from authorized sources.</p>
            </article>
            <article className="feature-card">
              <div className="feature-top"><FileCheck2 size={25} /><span>02</span></div>
              <h3>Review the record</h3>
              <p>See reported charges, bond terms, booking dates, and the original source — all in one place.</p>
            </article>
            <article className="feature-card">
              <div className="feature-top"><ShieldCheck size={25} /><span>03</span></div>
              <h3>Take action</h3>
              <p>Submit a free correction request or request a paid privacy review. Every request is reviewed by a human.</p>
            </article>
          </div>
        </section>

        <section className="site-width by-the-numbers">
          <div className="section-heading">
            <div>
              <span className="eyebrow">NATIONAL COVERAGE</span>
              <h2>Current coverage from verified sources.</h2>
            </div>
            <p>Counts reflect records eligible for public search and refreshed within the last 48 hours.</p>
          </div>
          <div className="number-grid">
            <div className="number-card"><Users size={26} /><strong>{stats ? stats.currentInmates.toLocaleString('en-US') : '—'}</strong><span>Current public inmate records</span></div>
            <div className="number-card"><Landmark size={26} /><strong>{stats ? stats.counties.toLocaleString('en-US') : '—'}</strong><span>Counties with current records</span></div>
            <div className="number-card"><Database size={26} /><strong>{stats ? stats.facilities.toLocaleString('en-US') : '—'}</strong><span>Verified facilities with current records</span></div>
            <div className="number-card"><Globe size={26} /><strong>{stats ? stats.states.toLocaleString('en-US') : '—'}</strong><span>States with current records</span></div>
          </div>
        </section>

        <section className="site-width how-section">
          <div className="section-heading">
            <div>
              <span className="eyebrow">SEARCH BY STATE</span>
              <h2>Find jail rosters in any state.</h2>
            </div>
          </div>
          <div className="state-grid">
            {US_STATES.slice(0, 12).map(state => (
              <Link key={state.abbrev} href={`/state/${state.abbrev}`} className="state-card">
                <span className="state-card__abbrev">{state.abbrev}</span>
                <span className="state-card__name">{state.name}</span>
              </Link>
            ))}
          </div>
          <div style={{ marginTop: '24px', textAlign: 'center' }}>
            <Link className="jm-button secondary" href="/states">View all 50 states <ArrowRight size={16} /></Link>
          </div>
        </section>

        <section className="site-width how-section">
          <div className="section-heading">
            <div>
              <span className="eyebrow">FREQUENTLY ASKED</span>
              <h2>Common questions about jail rosters.</h2>
            </div>
          </div>
          <div className="faq-grid">
            <article className="faq-card">
              <h3>What information is on a jail roster?</h3>
              <p>A jail roster typically includes the inmate&apos;s name, booking date, charges, bond amount, and the facility where they are being held. Some rosters also include age, sex, and arresting agency.</p>
            </article>
            <article className="faq-card">
              <h3>Are jail rosters public record?</h3>
              <p>Yes. Jail rosters are public records maintained by government agencies. JailMap only aggregates from authorized official sources — never third-party mirrors.</p>
            </article>
            <article className="faq-card">
              <h3>How often are records updated?</h3>
              <p>We ingest from each source every 2 to 6 hours. Records not refreshed within 48 hours are hidden to keep results current and accurate.</p>
            </article>
            <article className="faq-card">
              <h3>Can I get my name removed?</h3>
              <p>Submit a free correction request from any record page. For faster human review, a $99 paid privacy review is available. Payment does not guarantee removal.</p>
            </article>
          </div>
        </section>

        <section className="site-width responsibility-section">
          <div className="responsibility-icon"><ShieldCheck size={42} /></div>
          <div>
            <span className="eyebrow">PEOPLE ARE MORE THAN A RECORD</span>
            <h2>A booking is not a conviction.</h2>
            <p>All individuals are presumed innocent until proven guilty. Records can be incomplete or outdated, and a name match does not establish identity. Always confirm information with the facility.</p>
            <Link className="text-link" href="/about">Read about our approach <ArrowRight size={16} /></Link>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}
