import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import { NewBookingsFeed } from '@/components/records/NewBookingsFeed'
import { Activity, Radio } from 'lucide-react'

export const metadata = {
  title: 'New Bookings — Live Feed',
  robots: { index: false, follow: false },
}

export default function NewBookingsPage() {
  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content">
        <section className="new-bookings-hero">
          <div className="site-width">
            <div className="hero-badge">
              <Radio size={14} className="pulse" />
              <span>LIVE</span>
            </div>
            <h1>New Bookings</h1>
            <p>
              Real-time activity from authorized jurisdictions nationwide. 
              This feed refreshes every 15 seconds — bookings from the last 48 hours only.
            </p>
            <div className="hero-strip">
              <span><Activity size={14} /> Updates every 15 seconds</span>
              <span>All states</span>
              <span>Last 48 hours</span>
            </div>
          </div>
        </section>

        <section className="new-bookings-stage">
          <div className="site-width">
            <NewBookingsFeed />
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}
