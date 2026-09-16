import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { Brand } from '@/components/site/Brand'
import { ForgotForm } from '@/components/accounts/ForgotForm'
export const metadata = { title: 'Reset password', robots: { index: false, follow: false } }
export default function Forgot() {
  return <main className="auth-page jm-theme"><aside className="auth-story"><Brand light /><p className="auth-story-foot">A record is one part of a story. Never the whole person.</p></aside><section className="auth-main"><Link className="back-link" href="/login"><ArrowLeft size={16} /> Back to log in</Link><div className="auth-form-wrap"><span className="eyebrow">PASSWORD RESET</span><h1>Forgot your password?</h1><p className="auth-intro">Enter your account email and we'll send you a link to set a new password.</p><ForgotForm /></div></section></main>
}