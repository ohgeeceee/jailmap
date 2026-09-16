import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { Brand } from '@/components/site/Brand'
import { ResetForm } from '@/components/accounts/ResetForm'
export const metadata = { title: 'Choose a new password', robots: { index: false, follow: false } }
export default async function Reset({ searchParams }: { searchParams: Promise<{ token?: string }> }) {
  const { token } = await searchParams
  return <main className="auth-page jm-theme"><aside className="auth-story"><Brand light /><p className="auth-story-foot">A record is one part of a story. Never the whole person.</p></aside><section className="auth-main"><Link className="back-link" href="/login"><ArrowLeft size={16} /> Back to log in</Link><div className="auth-form-wrap"><span className="eyebrow">PASSWORD RESET</span><h1>Choose a new password.</h1><p className="auth-intro">Enter a new passphrase (15–128 characters).</p><ResetForm token={token ?? null} /></div></section></main>
}