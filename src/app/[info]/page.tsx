import { notFound } from 'next/navigation'
import Link from 'next/link'
import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
const pages = {
  about: { title: 'Public records. Human context.', intro: 'JailMap brings authorized public booking records into one searchable place, with a clear route back to the source.', sections: [
    ['A source-first approach', 'Coverage is limited to participating, authorized sources. Records display observation times and source links. We hide bookings that have not been refreshed within 48 hours; confirm custody and bond information directly with the facility.'],
    ['People are more than a record', 'A booking is not a conviction. All individuals are presumed innocent until proven guilty. Similar names may belong to different people, and a name match does not establish identity.'],
    ['A way to correct the record', 'Open a booking profile to submit a free correction or removal request. Requests are reviewed by a person. Approval withholds the record while source information is verified.'],
  ] },
  privacy: { title: 'Your information, explained.', intro: 'This notice describes the current JailMap application. Public booking information and private account information serve different purposes.', sections: [
    ['Account information', 'We store your name, email, password hash, saved search filters and server-side session records. Session cookies keep you signed in. Administrators can manage account access and see account audit events. Passwords are not stored in readable form.'],
    ['Saved searches', 'Saved searches belong to your account. They store names and location filters, not copies of booking profiles. You can remove them from your workspace. Saving a search does not activate monitoring or email alerts.'],
    ['Public records and correction requests', 'The public API excludes dates of birth and mugshot URLs by default. Correction requests store your contact email and explanation for review. Do not include Social Security numbers, full birth dates or identity documents in a request.'],
    ['Current service limits', 'Email verification, password recovery by email and account deletion self-service are not available in this release. This application does not send account emails. A public launch requires an operator contact, retention schedule and jurisdiction-specific privacy review.'],
  ] },
  terms: { title: 'Use information responsibly.', intro: 'JailMap is a starting point for public-record research. It is not a determination of identity, guilt, custody or eligibility.', sections: [
    ['Verify before relying', 'Records may be incomplete or outdated. Check the original source and contact the facility before relying on charges, release status or bond terms. A booking is not a conviction.'],
    ['Prohibited uses', 'Do not use this service for employment, housing, credit or insurance decisions. Do not use it to harass, stalk, threaten or discriminate against anyone, or to circumvent access controls and rate limits.'],
    ['Corrections are free', 'Anyone may request a correction or removal from a booking profile without paying or registering. Submission does not automatically change the record. A reviewer must verify the request.'],
    ['Service availability', 'Coverage depends on authorized data providers. Search results may change or become unavailable as data is updated, released, withheld or becomes stale.'],
  ] },
} as const
export async function generateMetadata({ params }: { params: Promise<{ info: string }> }) { const { info } = await params; return { title: info in pages ? `${pages[info as keyof typeof pages].title}` : 'Page not found' } }
export default async function InfoPage({ params }: { params: Promise<{ info: string }> }) {
  const { info } = await params; if (!(info in pages)) notFound(); const page = pages[info as keyof typeof pages]
  return <div className="jm-theme"><PublicHeader /><main className="site-width info-page"><span className="eyebrow">THE JAILMAP APPROACH</span><h1>{page.title}</h1><p className="info-intro">{page.intro}</p>{page.sections.map(([title, text]) => <section key={title}><h2>{title}</h2><p>{text}</p></section>)}<Link className="jm-button" href="/search">Search public records</Link></main><Footer /></div>
}
