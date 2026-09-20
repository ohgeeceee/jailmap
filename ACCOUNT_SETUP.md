# JailMap site and account workspaces

## Run locally

Use Node.js 24 and install dependencies with `npm install`.

```sh
npm run dev
```

Open `/` for the landing page, `/register` to create an account, `/login` to
sign in, and `/dashboard` for the member workspace. Account creation uses a real
password hash and persistent server-side session. There are no seeded/default
credentials and registration always creates a member, never an administrator.

Local account data is stored in `.data/accounts.sqlite` (gitignored). This is a
small, single-host account store separate from the PostgreSQL public-records
schema and from the earlier Prisma `User` model. Accounts from that unused model
are not automatically imported. The UI does not depend on a running records API
to register or sign in. Saved searches store filters, not cached inmate profiles.

## Create the first administrator

Register your own account in the browser, then run locally:

```sh
npm run admin:promote -- your-email@example.com
```

This promotes that existing account and revokes its old sessions. Log in again
to open `/admin`. Never run this command for an identity you have not verified.
Subsequent role/status changes are available in Admin → User management. Users
cannot change their own privileged access from the admin panel. Access changes
revoke the target user's sessions and append a server-side audit event.

## Available features

- Responsive public landing page, state navigation and name/location search.
- Registration, login, logout, secure random session tokens and seven-day expiry.
- Member overview, up to 25 saved searches, profile-name editing, password changes
  and revocation of other sessions. Running a saved search prefills and submits
  the public search page.
- Admin overview with real account counts, paginated user management and recent
  account audit history. User search terms are not exposed in the admin overview.
- Source-health and correction-review panels, connected to the existing FastAPI
  service when configured. Review approval suppresses the record and enqueues
  search-index deletion transactionally; rejection records the operator's note.
- About, privacy and responsible-use pages describing current behavior.

Email verification, email-based password recovery, MFA, email changes, account
deletion self-service and outbound notifications are not implemented. No account
emails are sent. Do not present submitted email addresses as verified identities.

## Records backend

Follow `ARCHITECTURE.md` for PostgreSQL, Redis, Meilisearch and FastAPI setup.
Set `RECORDS_API_URL` and matching `RECORDS_API_TOKEN` in the Next.js server
environment. Restart the Python API to load its new admin routes. Admin record
requests require both the private gateway credential and a server-asserted admin
identity. Browser-provided role headers are never forwarded.

No public records service, production database or live ingestion source was
configured as part of this work. The admin panel displays a truthful connection
unavailable state until the records API is connected. Source enablement remains
an operator task; the UI does not permit arbitrary ingestion URLs.

## Deployment constraints

The account implementation deliberately runs locally without infrastructure.
SQLite is **single-host only**; do not deploy it on ephemeral serverless storage
or share a database file over a network filesystem. For a single persistent host,
set all of these server-side environment variables:

```text
AUTH_DATABASE_PATH=/absolute/persistent/private/path/accounts.sqlite
AUTH_SINGLE_INSTANCE=true
APP_ORIGIN=https://your-jailmap-host.example
```

On Windows, use an absolute Windows path for `AUTH_DATABASE_PATH`. Restrict the
database directory to the service account and use encrypted storage/backups.
Production account access fails closed without the explicit persistence settings.
Production mutation requests also require `APP_ORIGIN`; cookies use HttpOnly,
Secure, SameSite=Lax and the `__Host-` prefix. Test production builds over HTTPS
when verifying authentication cookies.

For a scaled national service, replace the isolated account-store module with
PostgreSQL or a managed identity service, migrate existing hashes/sessions, add
MFA and verification/recovery, and centralize rate limiting before adding replicas.
Do not run multiple account stores with inconsistent user roles.

The account API uses 15–128-character passphrases and Node scrypt with N=131072,
r=8, p=1 and random salts. Session tokens contain 256 random bits; only their
SHA-256 digest is stored. Current roles/status are read from the database on every
protected request. Password changes revoke existing sessions. Mutation bodies are
limited to 8 KiB with same-origin checks. SQLite rate-limit counters persist
across server restarts; expensive hashing is bounded to two concurrent operations
per process. Credentials never appear in server logs.

By default all visitors share a conservative client rate-limit bucket. Set
`AUTH_TRUSTED_CLIENT_HEADER` only behind an edge proxy that overwrites that header
and blocks direct access. Do not trust arbitrary `X-Forwarded-For` values. Place
request/connection limits at the edge as well. Establish operator contact details,
account/audit retention and privacy processes before a public launch.

## Support inbox

The administrator Inbox combines private tickets submitted through `/contact`
with the latest messages in a Gmail inbox. Ticket data is stored in the same
single-host SQLite file as account data. Configure Gmail with an app password;
never place the normal Google account password in this project:

```text
SUPPORT_EMAIL_USER=getjailmap@gmail.com
SUPPORT_EMAIL_APP_PASSWORD=replace-with-google-app-password
SUPPORT_IMAP_HOST=imap.gmail.com
SUPPORT_IMAP_PORT=993
SUPPORT_SMTP_HOST=smtp.gmail.com
SUPPORT_SMTP_PORT=465
SUPPORT_MAIL_FROM=getjailmap@gmail.com
```

The app password and mailbox contents are server-only. Gmail email is read on
demand and is not copied into the application database. Website tickets retain
the sender name, email, subject, message, status, and timestamps; include this
table in the approved support-data retention and deletion policy. Replies require
an authenticated administrator, a same-origin request, and are rate limited.
Run `npm run test:support` to verify ticket validation and lifecycle behavior.

Deployment record: on 2026-09-20, the site owner approved production release
`jailmap-web:support-inbox-20260920-1040`. The web container alone was recreated;
PostgreSQL, Redis, Meilisearch, and the records API were not restarted. Verification
covered the container health check, public `/api/health`, public contact/privacy
content, admin-inbox authorization, and presence of the support environment inside
the container. The pre-release image `jailmap-web:20260916-0057` is retained as
the rollback target. The encrypted 2026-09-20 backup was present before release.

## Prisma compatibility repair

The pre-existing project combines Prisma Platform CLI 8 with Prisma Client 7 and
classic `.prisma` models. A separately aliased `prisma-legacy` generator now matches
Client 7.10, while the Platform CLI and its config remain available. Run
`npm run db:generate`; builds do so automatically. `prisma.legacy.config.ts` is the
classic ORM config. `@prisma/adapter-pg` supplies the required PostgreSQL adapter.
The map client initializes lazily, so a missing map DB does not break site builds.
Index syntax and the invalid state filter were fixed without applying migrations.

## Validation

```sh
npm run test:accounts
# With local dev server running; runner and server must use the same AUTH_DATABASE_PATH:
npm run test:accounts:http
npm run lint
npx tsc --noEmit
npm run build
python -m unittest backend.test_normalize
```

Unit coverage includes password rejection, duplicate signup, role-injection
rejection, login failures, hashed session storage, cross-user search ownership,
session expiry/revocation, password rotation, suspension, admin self-protection
and persistent rate limiting. HTTP coverage exercises the real Next.js handlers,
cookies, CSRF rejection, registration, protected pages, authorization, saved
searches, profile edits, suspension and logout. Tests use synthetic accounts and
delete only their own fixture rows; unit tests use a disposable database.

The production build, full TypeScript check and full lint passed. Local browser checks cover
desktop/mobile landing pages, login, the member dashboard, saved-search creation,
logout, registration layout, administrator routing/overview and the records-service
unavailable state. Synthetic browser accounts were removed after testing.
The live PostgreSQL review transaction and ingestion/search services remain
unverified without their infrastructure. Dependency audit results need review
before deployment; installing the compatibility generator does not constitute a
security clearance for the existing dependency tree. The current npm audit reports
16 findings (11 high, 5 moderate), concentrated in Prisma tooling and its transitive
dependencies; some proposed fixes require major-version changes. These were not
blindly forced as part of the UI/account build.

Password parameters follow [OWASP password-storage guidance](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html).
