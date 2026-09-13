import { AuthPage } from '@/components/accounts/AuthPage'
export const metadata = { title: 'Log in | JailMap', robots: { index: false, follow: false } }
export default function Login() { return <AuthPage mode="login" /> }
