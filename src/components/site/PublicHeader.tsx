import Link from 'next/link'
import { currentAccount } from '@/lib/accounts/session'
import { Brand } from './Brand'
export async function PublicHeader() {
  const user = await currentAccount()
  return <header className="public-header"><div className="site-width header-row"><Brand /><nav aria-label="Main navigation" className="public-nav"><Link href="/new-bookings">New bookings</Link><Link href="/search">Search records</Link><Link href="/coverage" className="hide-small">Coverage</Link><Link href="/#how-it-works" className="hide-small">How it works</Link><Link href="/about" className="hide-small">Our approach</Link></nav><div className="header-actions">{user ? <Link className="jm-button compact" href={user.role === 'admin' ? '/admin' : '/dashboard'}>My workspace</Link> : <><Link className="login-link" href="/login">Log in</Link><Link className="jm-button compact" href="/register">Create account <span aria-hidden="true">↗</span></Link></>}</div></div></header>
}
