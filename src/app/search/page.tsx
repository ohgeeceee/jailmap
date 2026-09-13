import Link from 'next/link'
import { SearchRecords } from '@/components/records/SearchRecords'
import { Disclaimer } from '@/components/records/Disclaimer'
import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
export const metadata = { title: 'Search public bookings | JailMap', robots: { index: false, follow: false } }
export default async function SearchPage({ searchParams }: { searchParams: Promise<{ name?: string; state?: string; county?: string }> }) {
  const query = await searchParams
  const initial = { name: typeof query.name === 'string' ? query.name.slice(0,100) : '', state: typeof query.state === 'string' && /^[A-Z]{2}$/.test(query.state) ? query.state : '', county: typeof query.county === 'string' ? query.county.slice(0,100) : '' }
  return <div className="jm-theme"><PublicHeader /><main id="main-content" className="mx-auto w-full max-w-6xl px-5 py-12">
    <Link href="/" className="text-blue-700 underline">← JailMap</Link>
    <h1 className="mt-8 text-4xl font-bold">Search public booking records</h1>
    <p className="mt-3 text-lg">Search participating counties by name. Each result represents a booking.</p>
    <Disclaimer /><SearchRecords key={JSON.stringify(initial)} initial={initial} />
    <p className="mt-8 text-sm">Coverage depends on authorized sources. Records not refreshed within 48 hours are hidden. Open a booking to request a correction or removal at no charge.</p>
  </main><Footer /></div>
}
