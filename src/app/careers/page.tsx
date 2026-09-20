import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import Link from 'next/link'
import { ArrowRight, Check, Clock, Heart, Home, Laptop, MapPin, ShieldCheck, Users } from 'lucide-react'

export const metadata = {
  title: 'Careers',
  description: 'Join the JailMap team — help build the most comprehensive public-records platform in the United States.',
  alternates: { canonical: '/careers' },
  openGraph: {
    title: 'Careers | JailMap',
    description: 'Join the JailMap team — help build the most comprehensive public-records platform in the United States.',
    url: 'https://jailmap.com/careers',
    siteName: 'JailMap',
  },
}

const openings = [
  {
    title: 'Senior Backend Engineer',
    location: 'Remote (US)',
    type: 'Full-time',
    description: 'Build and maintain the ingestion pipeline that processes booking records from thousands of jurisdictions across all 50 states.',
    tags: ['Python', 'FastAPI', 'PostgreSQL', 'Redis'],
  },
  {
    title: 'Data Engineer',
    location: 'Remote (US)',
    type: 'Full-time',
    description: 'Design and run the data pipeline that normalizes, deduplicates, and indexes millions of booking records.',
    tags: ['Python', 'ETL', 'Data Modeling', 'Meilisearch'],
  },
  {
    title: 'Frontend Engineer',
    location: 'Remote (US)',
    type: 'Full-time',
    description: 'Build the public-facing web application that makes public records accessible and understandable.',
    tags: ['TypeScript', 'Next.js', 'React', 'Tailwind CSS'],
  },
  {
    title: 'Privacy Review Specialist',
    location: 'Remote (US)',
    type: 'Full-time',
    description: 'Review name-removal requests with care, consistency, and respect for the people behind every record.',
    tags: ['Privacy', 'Legal Research', 'Documentation'],
  },
]

const benefits = [
  { icon: Heart, title: 'Health coverage', text: 'Medical, dental, and vision for you and your dependents.' },
  { icon: Home, title: 'Remote-first', text: 'Work from anywhere in the US. We meet up a few times a year.' },
  { icon: Clock, title: 'Flexible hours', text: 'We care about output, not hours logged. Async-first culture.' },
  { icon: Laptop, title: 'Equipment budget', text: 'New laptop on arrival, plus home office stipend.' },
  { icon: ShieldCheck, title: 'Paid time off', text: 'Generous PTO plus paid holidays and a winter break.' },
  { icon: Users, title: 'Small team', text: 'No bureaucracy. Your work ships directly to users who need it.' },
]

export default function CareersPage() {
  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content">
        <section className="site-width info-page">
          <span className="eyebrow"><span className="small-dot" />JOIN JAILMAP</span>
          <h1>Help build the most comprehensive public-records platform in the United States.</h1>
          <p className="info-intro">
            A small team, real problems, work that matters. We've been operating continuously since 2021 — and we're just getting started.
          </p>
        </section>

        {/* Benefits */}
        <section className="site-width" style={{ paddingBlock: '0 64px' }}>
          <div className="section-heading"><div><span className="eyebrow">WHY JAILMAP</span><h2>Good work, good benefits, good people.</h2></div></div>
          <div className="feature-grid">
            {benefits.map((b) => (
              <article className="feature-card" key={b.title}>
                <div className="feature-top"><b.icon size={25} /><span>0{benefits.indexOf(b) + 1}</span></div>
                <h3>{b.title}</h3>
                <p>{b.text}</p>
              </article>
            ))}
          </div>
        </section>

        {/* How we work */}
        <section className="site-width" style={{ paddingBlock: '0 64px' }}>
          <div className="responsibility-section">
            <div className="responsibility-icon"><Users size={42} /></div>
            <div>
              <span className="eyebrow">HOW WE WORK</span>
              <h2>Small team, high trust, real impact.</h2>
              <p>We're a fully remote team based in Montana. We communicate asynchronously, default to transparency, and ship work that directly serves the public. No layers of management. No hand-offs to contractors. If you build it, you'll see it in production.</p>
            </div>
          </div>
        </section>

        {/* Open positions */}
        <section className="site-width" style={{ paddingBlock: '0 64px' }}>
          <div className="section-heading"><div><span className="eyebrow">OPEN POSITIONS</span><h2>We're hiring.</h2></div></div>
          <div className="openings-list">
            {openings.map((role) => (
              <article className="opening-card" key={role.title}>
                <div className="opening-info">
                  <h3>{role.title}</h3>
                  <p>{role.description}</p>
                  <div className="opening-tags">
                    {role.tags.map((tag) => <span key={tag} className="opening-tag">{tag}</span>)}
                  </div>
                </div>
                <div className="opening-meta">
                  <span><MapPin size={14} /> {role.location}</span>
                  <span><Clock size={14} /> {role.type}</span>
                  <a className="jm-button compact" href={`mailto:getjailmap@gmail.com?subject=Application: ${encodeURIComponent(role.title)}`}>Apply <ArrowRight size={14} /></a>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="site-width" style={{ paddingBlock: '0 80px' }}>
          <div className="responsibility-section">
            <div className="responsibility-icon"><ArrowRight size={42} /></div>
            <div>
              <span className="eyebrow">DON'T SEE A ROLE THAT FITS?</span>
              <h2>We're always interested in hearing from people who care about public records.</h2>
              <p>Send us a note — we read every message.</p>
              <a className="jm-button" href="mailto:getjailmap@gmail.com?subject=Careers%20Inquiry">Get in touch <ArrowRight size={18} /></a>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}
