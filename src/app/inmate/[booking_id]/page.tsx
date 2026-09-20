import Link from 'next/link'
import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import { BookingProfile } from '@/components/records/BookingProfile'
import { Disclaimer } from '@/components/records/Disclaimer'
export const metadata = { title: 'Booking details', robots: { index: false, follow: false } }
export default async function InmatePage({ params }: { params: Promise<{ booking_id: string }> }) {
  const { booking_id } = await params
  return <div className="jm-theme"><PublicHeader /><main id="main-content" className="site-width booking-page">
    <Link href="/" className="back-link">← JailMap</Link>
    <Disclaimer />
    <BookingProfile id={booking_id} />
  </main><Footer /></div>
}