import Link from 'next/link'
import { Brand } from './Brand'
export function Footer() {
  return <footer className="public-footer"><div className="site-width">
    <div className="footer-top">
      <div className="footer-brand-col">
        <Brand light />
        <p>Public records. Clearer context.</p>
        <p className="footer-tagline">Operating continuously since 2021. Independent service — not affiliated with any government agency.</p>
      </div>
      <nav aria-label="Product"><span className="footer-nav-label">Product</span><Link href="/search">Search records</Link><Link href="/new-bookings">New bookings</Link><Link href="/coverage">Coverage</Link><Link href="/leaderboard">Leaderboard</Link><Link href="/pricing">Pricing</Link></nav>
      <nav aria-label="Company"><span className="footer-nav-label">Company</span><Link href="/about">About</Link><Link href="/careers">Careers</Link><Link href="/enterprise">Enterprise</Link><Link href="/contact">Contact</Link><Link href="/press">Press</Link></nav>
      <nav aria-label="Resources"><span className="footer-nav-label">Resources</span><Link href="/help">Help center</Link><Link href="/api-docs">API access</Link><Link href="/status">System status</Link><Link href="/trust-safety">Trust &amp; safety</Link><Link href="/legal">Legal</Link></nav>
      <nav aria-label="Legal"><span className="footer-nav-label">Legal</span><Link href="/legal">Privacy policy</Link><Link href="/legal">Terms of service</Link><Link href="/legal">DMCA</Link><Link href="/legal">Data subject requests</Link></nav>
    </div>
    <div className="footer-badges">
      <span className="footer-badge">SOC 2 Type II — In Progress</span>
      <span className="footer-badge">CJIS Compliance — In Progress</span>
      <span className="footer-badge">CCPA / State Privacy Compliant</span>
    </div>
    <div className="footer-bottom"><span>© {new Date().getFullYear()} JailMap, Inc.</span><span>Great Falls, Montana · United States</span><span>Made with care for transparency.</span></div>
  </div></footer>
}