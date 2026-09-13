import 'server-only'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { getSession } from './store'
export const SESSION_COOKIE = process.env.NODE_ENV === 'production' ? '__Host-jailmap_session' : 'jailmap_session'
export async function currentAccount() {
  return getSession((await cookies()).get(SESSION_COOKIE)?.value)
}
export async function requireAccount(admin = false) {
  const account = await currentAccount()
  if (!account) redirect('/login')
  if (admin && account.role !== 'admin') redirect('/dashboard')
  return account
}
