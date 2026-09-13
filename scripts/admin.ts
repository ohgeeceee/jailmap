import { promoteAdmin } from '../src/lib/accounts/store.ts'
const email = process.argv[2]
if (!email) { console.error('Usage: node --experimental-strip-types scripts/admin.ts EMAIL'); process.exit(1) }
try { promoteAdmin(email); console.log('Administrator access granted. Sign in again to continue.') }
catch (error) { console.error(error instanceof Error ? error.message : 'Promotion failed'); process.exit(1) }
