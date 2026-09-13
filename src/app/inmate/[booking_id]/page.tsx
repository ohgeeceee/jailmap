import Link from 'next/link'
import { notFound } from 'next/navigation'
import { BookingProfile } from '@/components/records/BookingProfile'
import { Disclaimer } from '@/components/records/Disclaimer'
export const metadata = { title: 'Booking details | JailMap', robots: { index: false, follow: false } }
export default async function ProfilePage({ params }: { params: Promise<{ booking_id: string }> }) {
  const { booking_id } = await params
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(booking_id)) notFound()
  return <main className="mx-auto w-full max-w-3xl px-5 py-12"><Link href="/search" className="text-blue-700 underline">← Search bookings</Link><Disclaimer /><BookingProfile id={booking_id} /></main>
}
