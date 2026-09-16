# site-operator - site health

Generated 2026-09-14 05:13Z by `bots/site_health.py`.

Green tier: read-only health checks.

```
# Site operator health digest — 2026-09-14 05:13 UTC

## Containers
```
jailmap-web-1	Up About a minute (healthy)
jailmap-api-1	Up 25 minutes (healthy)
jailmap-web-run-75011c77e3ce	Up About an hour (healthy)
jailmap-postgres-1	Up 20 hours (healthy)
jailmap-redis-1	Up 20 hours (healthy)
jailmap-meili-1	Up 20 hours
dispatch-postgres-1	Up 20 hours (healthy)
dispatch-redis-1	Up 20 hours (healthy)
```

## Backups
- OK: `/root/jailmap/backups/jailmap-20260913T042149Z.tar.gz.enc` (24.9h old)
- OK: `/root/jailmap/backups/sitemap.ts.bak-20260914-050306` (0.2h old)
- OK: `/root/jailmap/backups/jailmap-20260913T042149Z.sha256` (24.9h old)
- OK: `/root/jailmap/backups/sitemap.ts.precontentgate-20260914-051014` (0.0h old)
- OK: `/root/jailmap/backups/jailmap-20260914T042150Z.tar.gz.enc` (0.9h old)
- OK: `/root/jailmap/backups/jailmap-20260914T042150Z.sha256` (0.9h old)
- OK: `/root/jailmap/backups/config/root-crontab-before-jailmap-cleanup-20260913T053458Z.txt` (23.6h old)

## TLS
- jailmap.com cert: 83 days remaining — OK

## Disk
```
/dev/vda1       232G  164G   68G  71% /
/dev/vda1       232G  164G   68G  71% /
```

```
