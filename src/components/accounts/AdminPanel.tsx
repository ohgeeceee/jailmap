'use client'

import Link from 'next/link'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Activity, ArrowRight, Bookmark, ShieldCheck, Users, Database, FileText, MapPin, Coins } from 'lucide-react'
import type { Account, adminOverview } from '@/lib/accounts/store'
import { RecordsAdmin } from './RecordsAdmin'
import { CoveragePanel, IngestionPanel, PipelinePanel, RevenuePanel } from './OpsPanels'
import { CoverageGaps, FreshnessPanel, RunHistory } from './OpsExtras'
import { SupportInbox } from './SupportInbox'

type Overview = ReturnType<typeof adminOverview>

const HEADINGS: Record<string, { title: string; blurb: string; icon: React.ElementType }> = {
  overview: { title: 'Platform overview', blurb: 'A high-level view of the JailMap platform — users, records, coverage, and revenue.', icon: Activity },
  coverage: { title: 'National coverage', blurb: 'How much of the country\'s jail roster surface JailMap actually covers today.', icon: MapPin },
  ingestion: { title: 'Ingestion health', blurb: 'Whether enabled sources are still producing records, and why failures happened.', icon: Activity },
  pipeline: { title: 'Discovery pipeline', blurb: 'Sources moving from discovery toward a reviewed, enabled adapter.', icon: Database },
  revenue: { title: 'Removals & revenue', blurb: 'Paid removal-review sessions and the correction queue behind them.', icon: Coins },
  users: { title: 'User management', blurb: 'Manage access carefully. Changes revoke the affected user\'s sessions.', icon: Users },
  records: { title: 'Sources & reviews', blurb: 'Review source health and handle correction requests with care.', icon: FileText },
  activity: { title: 'Activity log', blurb: 'Recent account and access events, recorded by the server.', icon: Activity },
  inbox: { title: 'Support inbox', blurb: 'Read and respond to website support tickets and email in one place.', icon: FileText },
}

const TABS: Record<string, { stat?: string; statLabel?: string; href: string }> = {
  coverage: { stat: 'coverage', statLabel: 'of counties live', href: '/admin?tab=coverage' },
  ingestion: { stat: 'ingestion', statLabel: 'success rate', href: '/admin?tab=ingestion' },
  pipeline: { stat: 'pipeline', statLabel: 'in discovery queue', href: '/admin?tab=pipeline' },
  revenue: { stat: 'revenue', statLabel: 'paid removals', href: '/admin?tab=revenue' },
}

export function AdminPanel({ user, data, tab }: { user: Account; data: Overview; tab: string }) {
  const router = useRouter()
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const heading = HEADINGS[tab] || HEADINGS.overview
  const HeadingIcon = heading.icon

  return (
    <>
      <div className="workspace-title admin-title">
        <div>
          <span className="eyebrow">PLATFORM OPERATIONS</span>
          <h1>{heading.title}</h1>
          <p>{heading.blurb}</p>
        </div>
        <span className="admin-label"><ShieldCheck size={16} />Administrator</span>
      </div>

      {message && <p className="form-success" role="status">{message}</p>}

      {tab === 'overview' && (
        <>
          <div className="stat-grid four">
            <div className="stat-card"><Users size={20} /><span>Registered users</span><strong>{data.total}</strong><p>All account statuses</p></div>
            <div className="stat-card"><Activity size={20} /><span>Active accounts</span><strong>{data.active}</strong><p>Enabled to sign in</p></div>
            <div className="stat-card"><ShieldCheck size={20} /><span>Administrators</span><strong>{data.admins}</strong><p>Active privileged accounts</p></div>
            <div className="stat-card"><Bookmark size={20} /><span>Saved searches</span><strong>{data.searches}</strong><p>Across member workspaces</p></div>
          </div>

          <div className="quick-links">
            <Link href="/admin?tab=coverage" className="quick-link-card">
              <MapPin size={22} />
              <div>
                <strong>National coverage</strong>
                <span>View the county-by-county breakdown of live roster ingestion.</span>
              </div>
              <ArrowRight size={18} />
            </Link>
            <Link href="/admin?tab=ingestion" className="quick-link-card">
              <Activity size={22} />
              <div>
                <strong>Ingestion health</strong>
                <span>Monitor source failures and stale jurisdictions.</span>
              </div>
              <ArrowRight size={18} />
            </Link>
            <Link href="/admin?tab=revenue" className="quick-link-card">
              <Coins size={22} />
              <div>
                <strong>Revenue & removals</strong>
                <span>Review paid privacy requests and correction queue.</span>
              </div>
              <ArrowRight size={18} />
            </Link>
            <Link href="/admin?tab=records" className="quick-link-card">
              <FileText size={22} />
              <div>
                <strong>Source reviews</strong>
                <span>Audit correction requests and source health.</span>
              </div>
              <ArrowRight size={18} />
            </Link>
          </div>

          <div className="dashboard-banner">
            <div className="banner-icon"><ShieldCheck size={26} /></div>
            <div>
              <h2>Responsible records start with review.</h2>
              <p>Check source health and review pending correction requests.</p>
            </div>
            <Link className="jm-button secondary" href="/admin?tab=records">Open review desk <ArrowRight size={16} /></Link>
          </div>
        </>
      )}

      {(tab === 'overview' || tab === 'users') && (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>{tab === 'overview' ? 'Community accounts' : 'Accounts'}</h2>
              <p>Showing up to 25 users per page. Your own access is protected.</p>
            </div>
          </div>
          <div className="table-scroll">
            <table className="admin-table">
              <caption className="sr-only">Registered user accounts</caption>
              <thead>
                <tr><th scope="col">User</th><th scope="col">Joined</th><th scope="col">Role</th><th scope="col">Status</th><th scope="col">Access</th></tr>
              </thead>
              <tbody>
                {data.users.map(account => (
                  <tr key={account.id}>
                    <td><strong>{account.name}{account.id === user.id && ' (you)'}</strong><span>{account.email}</span></td>
                    <td>{new Date(account.created_at * 1000).toISOString().slice(0, 10)}</td>
                    <td><span className={`status-badge ${account.role === 'admin' ? 'admin' : ''}`}>{account.role}</span></td>
                    <td><span className={`status-badge ${account.status === 'suspended' ? 'warning' : ''}`}>{account.status}</span></td>
                    <td>
                      {account.id === user.id ? (
                        <span>Current account</span>
                      ) : (
                        <form className="access-form" onSubmit={async event => {
                          event.preventDefault(); setBusy(true); setMessage('')
                          const values = new FormData(event.currentTarget)
                          try {
                            const response = await fetch(`/api/account/admin/users/${account.id}`, { method: 'PATCH', headers: { 'content-type': 'application/json' }, body: JSON.stringify(Object.fromEntries(values)) })
                            const result = await response.json()
                            if (!response.ok) throw new Error(result.error)
                            setMessage('Access updated. The user must sign in again.')
                            router.refresh()
                          } catch (error) { setMessage(error instanceof Error ? error.message : 'Update failed.') } finally { setBusy(false) }
                        }}>
                          <select name="role" defaultValue={account.role} aria-label={`Role for ${account.name}`}><option value="member">Member</option><option value="admin">Admin</option></select>
                          <select name="status" defaultValue={account.status} aria-label={`Status for ${account.name}`}><option value="active">Active</option><option value="suspended">Suspended</option></select>
                          <button className="jm-button secondary compact" disabled={busy}>Apply</button>
                        </form>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {data.total > 25 && (
            <div className="pagination">
              <span>Page {data.page}</span>
              {data.page > 1 && <Link href={`/admin?tab=users&page=${data.page - 1}`}>Previous</Link>}
              {data.page * 25 < data.total && <Link href={`/admin?tab=users&page=${data.page + 1}`}>Next</Link>}
            </div>
          )}
        </section>
      )}

      {tab === 'records' && <RecordsAdmin />}
      {tab === 'coverage' && <><CoveragePanel /><CoverageGaps /></>}
      {tab === 'ingestion' && <><IngestionPanel /><RunHistory /><FreshnessPanel /></>}
      {tab === 'pipeline' && <PipelinePanel />}
      {tab === 'revenue' && <RevenuePanel />}
      {tab === 'inbox' && <SupportInbox />}

      {(tab === 'activity' || tab === 'overview') && (
        <section className="panel">
          <div className="panel-heading"><div><h2>Recent account activity</h2><p>Latest 20 events. Passwords and search terms are never included.</p></div></div>
          <div className="activity-list">
            {data.audit.map(event => (
              <div className="activity-row" key={String(event.id)}>
                <span className="activity-dot" />
                <div><strong>{String(event.action).replaceAll('.', ' ')}</strong><p>Target: {String(event.target_id || 'System')} · Actor: {String(event.actor_id || 'Local operator')}</p></div>
                <time>{new Date(Number(event.created_at) * 1000).toISOString().replace('T', ' ').slice(0, 16)} UTC</time>
              </div>
            ))}
          </div>
        </section>
      )}
    </>
  )
}
