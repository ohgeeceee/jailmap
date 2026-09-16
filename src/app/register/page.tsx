import { AuthPage } from '@/components/accounts/AuthPage'
export const metadata = { title: 'Create an account', robots: { index: false, follow: false } }
export default function Register() { return <AuthPage mode="register" /> }
