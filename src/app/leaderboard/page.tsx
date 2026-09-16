import { PublicHeader } from '@/components/site/PublicHeader'
import { Footer } from '@/components/site/Footer'
import { LeaderboardClient } from '@/components/records/LeaderboardClient'

export const metadata = {
  title: 'Repeat Booking Leaderboard',
  description:
    'Repeat booking counts observed across authorized jurisdictions. Name matches are not confirmed to be the same individual.',
  robots: { index: false, follow: false },
}

export default function LeaderboardPage() {
  return (
    <div className="jm-theme">
      <PublicHeader />
      <main id="main-content">
        <LeaderboardClient />
      </main>
      <Footer />
    </div>
  )
}
