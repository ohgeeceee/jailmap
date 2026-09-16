import { database, hashPassword, emailValue } from '../src/lib/accounts/store.ts'
const email = process.argv[2]
const password = process.argv[3]
if (!email || !password) { console.error('Usage: node --experimental-strip-types scripts/reset-password.ts EMAIL NEWPASSWORD'); process.exit(1) }
const hash = await hashPassword(password)
const db = database()
const result = db.prepare('UPDATE accounts SET password_hash=? WHERE email=?').run(hash, emailValue(email))
if (!result.changes) { console.error('No account found for ' + email); process.exit(1) }
db.prepare('DELETE FROM sessions WHERE account_id=(SELECT id FROM accounts WHERE email=?)').run(emailValue(email))
db.prepare("DELETE FROM rate_limits WHERE key LIKE 'auth-email:%'").run()
console.log('Password reset complete. Sign in again to continue.')