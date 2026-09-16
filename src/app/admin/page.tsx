import { requireAccount } from '@/lib/accounts/session'
import { adminOverview } from '@/lib/accounts/store'
import { Workspace } from '@/components/accounts/Workspace'
import { AdminPanel } from '@/components/accounts/AdminPanel'
export const metadata = { title: 'Administration', robots: { index: false, follow: false } }
export default async function Admin({ searchParams }: { searchParams: Promise<{ tab?: string; page?: string }> }) {
  const user = await requireAccount(true), query = await searchParams
  const tab = ['overview', 'users', 'records', 'activity', 'coverage', 'ingestion', 'pipeline', 'revenue'].includes(query.tab || '') ? query.tab! : 'overview'
  const page = Math.max(1, Math.min(10000, Math.floor(Number(query.page) || 1)))
  return <Workspace user={user} admin tab={tab}><AdminPanel user={user} data={adminOverview(page)} tab={tab} /></Workspace>
}
