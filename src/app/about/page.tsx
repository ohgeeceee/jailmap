import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import Link from 'next/link'
import { ArrowRight, Calendar, Database, FileCheck2, Globe, MapPin, ShieldCheck, Users } from 'lucide-react'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'About JailMap',
  description: 'JailMap brings authorized public booking records into one searchable place, with a clear route back to the source. Learn how the service works and what we publish.',
  alternates: { canonical: 'https://jailmap.com/about' },
  openGraph: {
    title: 'About JailMap | JailMap',
    description: 'JailMap brings authorized public booking records into one searchable place, with a clear route back to the source. Learn how the service works and what we publish.',
    url: 'https://jailmap.com/about',
    siteName: 'JailMap',
  },
}

const timeline = [
  { year: '2021', title: 'Founded in Montana', text: 'JailMap began as a single-county pilot in Great Falls, Montana, focused on making local jail rosters searchable.' },
  { year: '2022', title: 'First 100 counties', text: 'Expanded to 100 counties across 12 states. Built the first automated ingestion adapters for sheriff websites.' },
  { year: '2023', title: '1 million records', text: 'Crossed 1 million booking records in the archive. Launched the free correction request system.' },
  { year: '2024', title: '50 states covered', text: 'Achieved coverage in all 50 states and DC. Launched the paid privacy review program.' },
  { year: '2025', title: '10 million records', text: 'Surpassed 10 million records. Began SOC 2 Type II and CJIS compliance processes.' },
  { year: '2026', title: '14 million+ records', text: 'Operating continuously for over five years. Serving researchers, journalists, and legal teams nationwide.' },
]

const team = [
  { name: 'Jon', role: 'Founder & Lead Engineer', focus: 'Platform architecture, ingestion pipeline, operations' },
  { name: 'Engineering', role: 'Backend & Data Team', focus: 'Adapter development, data normalization, infrastructure' },
  { name: 'Privacy', role: 'Review & Compliance', text: 'Name-removal reviews, regulatory compliance, policy' },
  { name: 'Support', role: 'User Success', focus: 'Account help, correction requests, community' },
]

export default function AboutPage() {
  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content">
        <section className="site-width info-page">
          <span className="eyebrow"><span className="small-dot" />ABOUT JAILMAP</span>
          <h1>Five years of making public records accessible.</h1>
          <p className="info-intro">
            JailMap is a public-records platform built to make official booking information accessible — with transparency, accountability, and respect for the people behind every record.
          </p>
        </section>

        {/* By the numbers */}
        <section className="site-width" style={{ paddingBlock: '0 64px' }}>
          <div className="number-grid">
            <div className="number-card"><Calendar size={26} /><strong>2021</strong><span>Founded in Great Falls, MT</span></div>
            <div className="number-card"><MapPin size={26} /><strong>2,847</strong><span>Counties indexed</span></div>
            <div className="number-card"><Database size={26} /><strong>14.2M</strong><span>Booking records archived</span></div>
            <div className="number-card"><Globe size={26} /><strong>51</strong><span>States &amp; DC covered</span></div>
          </div>
        </section>

        {/* Mission / standards / team */}
        <section className="site-width" style={{ paddingBlock: '0 64px' }}>
          <div className="section-heading"><div><span className="eyebrow">WHAT DRIVES US</span><h2>Mission, standards, and the people behind the work.</h2></div></div>
          <div className="feature-grid">
            <article className="feature-card">
              <div className="feature-top"><Database size={25} /><span>01</span></div>
              <h3>Our mission</h3>
              <p>Make every official jail booking record in America searchable from one place — free, transparent, and linked back to the source. No third-party mirrors. No paywall on the public site.</p>
            </article>
            <article className="feature-card">
              <div className="feature-top"><ShieldCheck size={25} /><span>02</span></div>
              <h3>Our standards</h3>
              <p>We publish only from authorized official sources. Every record has a source link. PII is excluded. A paid privacy review exists for your own name — never an automatic removal.</p>
            </article>
            <article className="feature-card">
              <div className="feature-top"><Users size={25} /><span>03</span></div>
              <h3>Our team</h3>
              <p>JailMap is operated by a small, full-time team based in Montana. We build the adapters, run the infrastructure, and answer your emails ourselves. No call centers. No contractors.</p>
            </article>
          </div>
        </section>

        {/* Timeline */}
        <section className="site-width" style={{ paddingBlock: '0 64px' }}>
          <div className="section-heading"><div><span className="eyebrow">OUR HISTORY</span><h2>Five years of continuous operation.</h2></div></div>
          <div className="timeline">
            {timeline.map((item) => (
              <div className="timeline-row" key={item.year}>
                <div className="timeline-year">{item.year}</div>
                <div className="timeline-line"><span className="timeline-dot" /></div>
                <div className="timeline-content">
                  <h3>{item.title}</h3>
                  <p>{item.text}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Team */}
        <section className="site-width" style={{ paddingBlock: '0 64px' }}>
          <div className="section-heading"><div><span className="eyebrow">THE TEAM</span><h2>Small, focused, and experienced.</h2></div></div>
          <div className="team-grid">
            {team.map((member) => (
              <div className="team-card" key={member.name}>
                <div className="avatar">{member.name[0]}</div>
                <strong>{member.name}</strong>
                <span>{member.role}</span>
                <p>{member.focus || member.text}</p>
              </div>
            ))}
          </div>
        </section>

        {/* What we do differently */}
        <section className="site-width" style={{ paddingBlock: '0 64px' }}>
          <div className="section-heading"><div><span className="eyebrow">WHAT WE DO DIFFERENTLY</span><h2>Principles that guide every decision.</h2></div></div>
          <div className="feature-grid">
            <article className="feature-card">
              <div className="feature-top"><FileCheck2 size={25} /><span>01</span></div>
              <h3>Source-linked, every time</h3>
              <p>Every booking record links directly to the official source — the sheriff's website, the detention facility, the open-data portal. We never copy without attribution.</p>
            </article>
            <article className="feature-card">
              <div className="feature-top"><ShieldCheck size={25} /><span>02</span></div>
              <h3>Free search, always</h3>
              <p>Public booking records are free to search. Correction and removal requests are free to submit. The only paid product is a human privacy review of your own name — and that review never guarantees removal.</p>
            </article>
            <article className="feature-card">
              <div className="feature-top"><Users size={25} /><span>03</span></div>
              <h3>Presumed innocent</h3>
              <p>A booking is not a conviction. Records can be incomplete, outdated, or wrong. We surface the facts — not judgment.</p>
            </article>
          </div>
        </section>

        <section className="site-width" style={{ paddingBlock: '0 80px' }}>
          <div className="responsibility-section">
            <div className="responsibility-icon"><ShieldCheck size={42} /></div>
            <div>
              <span className="eyebrow">PEOPLE ARE MORE THAN A RECORD</span>
              <h2>Want to work with us?</h2>
              <p>We're always looking for people who understand public records, transparency, and building tools that matter.</p>
              <Link className="jm-button" href="/careers">See open roles <ArrowRight size={18} /></Link>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}