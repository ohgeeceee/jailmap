import { AuthPage } from '@/components/accounts/AuthPage'
export const metadata = { title: 'Log in', robots: { index: false, follow: false } }
export default function Login() { return <AuthPage mode="login" /> }
