import Link from 'next/link'
import { redirect } from 'next/navigation'
import { Bookmark, ShieldCheck, ArrowLeft } from 'lucide-react'
import { currentAccount } from '@/lib/accounts/session'
import { Brand } from '@/components/site/Brand'
import { AuthForm } from './AuthForm'
export async function AuthPage({ mode }: { mode: 'register' | 'login' }) {
  const user = await currentAccount()
  if (user) redirect(user.role === 'admin' ? '/admin' : '/dashboard')
  return <main className="auth-page jm-theme"><aside className="auth-story"><Brand light /><div><span className="eyebrow">YOUR PLACE TO MAKE SENSE OF IT</span><h2>Clear information.<br /><em>A calmer search.</em></h2><p>Keep your searches organized and return to the details that matter to you.</p><div className="auth-benefit"><Bookmark size={20} /><span>Saved searches, ready when you are</span></div><div className="auth-benefit"><ShieldCheck size={20} /><span>Your own secure, private workspace</span></div></div><p className="auth-story-foot">A record is one part of a story. Never the whole person.</p></aside><section className="auth-main"><Link className="back-link" href="/"><ArrowLeft size={16} /> Back to JailMap</Link><div className="auth-form-wrap"><span className="eyebrow">{mode === 'register' ? 'A FRESH START' : 'GOOD TO SEE YOU'}</span><h1>{mode === 'register' ? 'Make yourself at home.' : 'Welcome back.'}</h1><p className="auth-intro">{mode === 'register' ? 'Create your free account. Keep your research in one place.' : 'Log in to your JailMap workspace.'}</p><AuthForm mode={mode} /><p className="auth-note">Public record searches and correction requests are available without an account.</p></div><div className="auth-bottom"><Link href="/privacy">Privacy</Link><Link href="/terms">Responsible use</Link></div></section></main>
}
