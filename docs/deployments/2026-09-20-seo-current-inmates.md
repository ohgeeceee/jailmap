# JailMap SEO and current-inmates deployment

- Date: 2026-09-20 11:39 UTC
- Approver: site owner, via “ok go” in the active Codex session
- Scope: public web container only; homepage and jail-roster SEO, live current-inmate statistics, sitemap/canonical corrections, and county route build compatibility
- Public data: read-only aggregate count of public records refreshed within 48 hours; no record publication, source enablement, schema change, or data mutation
- Authentication: no intended behavior change; anonymous admin API remained HTTP 401 after deployment
- Preflight: all containers healthy; `/`, `/jail-roster`, and `/api/health` returned HTTP 200; 66 GB disk free
- Backup: `backups/jailmap-20260920T042435Z.tar.gz.enc`; checksum verified; backup service exited successfully
- Previous image: `sha256:f46094ea573315f97296768bb77b6cb94fafb37006e41717b256ec2d186b491d`
- Rollback image: `jailmap-web:rollback-seo-20260920T113910Z`
- Deployment: rebuilt and recreated only the Compose `web` service; API, PostgreSQL, Redis, and Meilisearch were not recreated
- Verification: homepage showed 5,515 current public records and the expected title; public home, jail roster, and health returned 200; sitemap returned 72 URLs and omitted `/name-removal`; anonymous admin returned 401; startup logs were clean
- Rollback status: not required
- Follow-up access action: at the owner’s explicit request, promoted the existing
  `ohjoncurrie@gmail.com` account to active administrator through the audited operator command.
  Existing sessions were revoked by the promotion workflow; direct read-only verification returned
  `role=admin` and `status=active`. No password or account email was changed.
- Follow-up credential action: at the owner’s explicit request, reset the same account password
  through the application’s scrypt password-reset workflow. The workflow revoked existing sessions,
  and a direct application login check succeeded while preserving the active administrator role.
  The plaintext password is not recorded in this deployment record.

Rollback command:

```sh
docker tag jailmap-web:rollback-seo-20260920T113910Z jailmap-web:support-inbox-20260920-1040
docker compose up -d --no-deps web
```
