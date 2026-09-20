import Link from 'next/link'
import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import { SearchGate } from '@/components/records/SearchGate'
import { Disclaimer } from '@/components/records/Disclaimer'
export const metadata = { title: 'Search public bookings', robots: { index: false, follow: false } }
export default async function SearchPage({ searchParams }: { searchParams: Promise<{ name?: string; state?: string; county?: string }> }) {
  const query = await searchParams
  const initial = { name: typeof query.name === 'string' ? query.name.slice(0,100) : '', state: typeof query.state === 'string' && /^[A-Z]{2}$/.test(query.state) ? query.state : '', county: typeof query.county === 'string' ? query.county.slice(0,100) : '' }
  return <div className="jm-theme"><PublicHeader /><main id="main-content" className="site-width search-page">
    <Link href="/" className="back-link">← JailMap</Link>
    <h1>Search public booking records</h1>
    <p className="search-intro">Search participating counties by name. Each result represents a booking.</p>
    <Disclaimer /><SearchGate key={JSON.stringify(initial)} initial={initial} />
    <p className="search-footnote">Coverage depends on authorized sources. Records not refreshed within 48 hours are hidden. Open a booking to request a correction or removal at no charge.</p>
  </main><Footer /></div>
}
