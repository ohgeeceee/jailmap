import { requireAccount } from '@/lib/accounts/session'
import { getDashboard } from '@/lib/accounts/store'
import { Workspace } from '@/components/accounts/Workspace'
import { MemberPanel } from '@/components/accounts/MemberPanel'
export const metadata = { title: 'My workspace', robots: { index: false, follow: false } }
export default async function Dashboard({ searchParams }: { searchParams: Promise<{ tab?: string }> }) {
  const user = await requireAccount(), query = await searchParams
  const tab = ['overview', 'saved', 'settings'].includes(query.tab || '') ? query.tab! : 'overview'
  return <Workspace user={user} tab={tab}><MemberPanel user={user} {...getDashboard(user.id)} tab={tab} /></Workspace>
}
