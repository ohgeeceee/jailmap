import type { ReactNode } from 'react'
import Link from 'next/link'
import { Bell, Bookmark, LayoutDashboard, Search, Settings2, ShieldCheck, Users, Activity, ArrowUpRight, MapPin, Gauge, GitBranch, Coins, FileText, Inbox } from 'lucide-react'
import type { Account } from '@/lib/accounts/store'
import { Brand } from '@/components/site/Brand'
import { SignOut } from '@/components/site/SignOut'

export function Workspace({ user, admin = false, tab, children }: { user: Account; admin?: boolean; tab: string; children: ReactNode }) {
  const adminLinks = [
    { tab: 'overview', label: 'Overview', icon: LayoutDashboard, section: 'platform' },
    { tab: 'coverage', label: 'Coverage', icon: MapPin, section: 'data' },
    { tab: 'ingestion', label: 'Ingestion', icon: Gauge, section: 'data' },
    { tab: 'pipeline', label: 'Pipeline', icon: GitBranch, section: 'data' },
    { tab: 'revenue', label: 'Revenue', icon: Coins, section: 'operations' },
    { tab: 'inbox', label: 'Inbox', icon: Inbox, section: 'operations' },
    { tab: 'users', label: 'Users', icon: Users, section: 'operations' },
    { tab: 'records', label: 'Reviews', icon: FileText, section: 'operations' },
    { tab: 'activity', label: 'Activity', icon: Activity, section: 'operations' },
  ]
  const memberLinks = [
    { tab: 'overview', label: 'Overview', icon: LayoutDashboard, section: 'workspace' },
    { tab: 'saved', label: 'Saved searches', icon: Bookmark, section: 'workspace' },
    { tab: 'watchlists', label: 'Watchlists', icon: Bell, section: 'workspace' },
    { tab: 'settings', label: 'Settings', icon: Settings2, section: 'workspace' },
  ]
  const links = admin ? adminLinks : memberLinks
  const sections = [...new Set(links.map(l => l.section))]

  return <div className="workspace jm-theme"><aside className="workspace-sidebar admin-sidebar"><Brand /><span className="sidebar-section-label">{admin ? 'ADMINISTRATION' : 'YOUR WORKSPACE'}</span><nav aria-label="Workspace navigation">{sections.map(section => <div key={section} className="sidebar-section"><span className="sidebar-section-label">{section.toUpperCase()}</span>{links.filter(l => l.section === section).map(item => <Link key={item.tab} className={`side-link ${item.tab === tab ? 'selected' : ''}`} aria-current={item.tab === tab ? 'page' : undefined} href={`${admin ? '/admin' : '/dashboard'}?tab=${item.tab}`}><item.icon size={18} />{item.label}</Link>)}</div>)}<div className="sidebar-divider" /><Link className="side-link" href="/search"><Search size={18} />Search records<ArrowUpRight size={14} /></Link>{user.role === 'admin' && <Link className="side-link" href={admin ? '/dashboard' : '/admin'}><ShieldCheck size={18} />{admin ? 'Member workspace' : 'Administration'}</Link>}</nav><div className="sidebar-bottom"><div className="sidebar-note"><ShieldCheck size={20} /><p>{admin ? 'Review with care. Every access change is recorded.' : 'Public information deserves careful interpretation.'}</p></div><div className="sidebar-account"><span className="avatar">{user.name.slice(0, 1).toUpperCase()}</span><div><strong>{user.name}</strong><span>{admin ? 'Administrator' : 'Free account'}</span></div></div><SignOut /></div></aside><div className="workspace-body"><header className="workspace-topbar admin-topbar"><div><span className="breadcrumb-label">{admin ? 'Administration' : 'My workspace'}</span><span className="breadcrumb-separator">/</span><strong>{links.find(item => item.tab === tab)?.label}</strong></div><span className="account-pill"><span className="small-dot" />{admin ? 'Admin access' : 'Personal account'}</span></header><main id="main-content" className="workspace-main">{children}</main><footer className="workspace-footer">JailMap · Public records, clearer context. <Link href="/privacy">Privacy & responsible use</Link></footer></div></div>
}
