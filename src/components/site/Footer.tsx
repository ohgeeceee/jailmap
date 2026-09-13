import Link from 'next/link'
import { Brand } from './Brand'
export function Footer() {
  return <footer className="public-footer"><div className="site-width"><div className="footer-top"><div><Brand /><p>Public records. Clearer context.</p></div><nav aria-label="Footer navigation"><Link href="/about">About JailMap</Link><Link href="/privacy">Privacy</Link><Link href="/terms">Responsible use</Link><Link href="/search">Find a record</Link></nav></div><div className="footer-bottom"><span>© {new Date().getFullYear()} JailMap</span><span>Independent service. Not affiliated with a government agency.</span></div></div></footer>
}
