#!/bin/bash
set -euo pipefail
umask 077
cd /root/jailmap
# Preserve the exact running filesystem even when its original image tag is gone.
# Docker export excludes mounted account data; encrypted database/account backups
# are separate. Import intentionally supplies only non-secret runtime settings.
docker export jailmap-web-1 > backups/web-pre-national-20260907.tar
docker import --change 'USER node' --change 'WORKDIR /app' \
 --change 'ENV NODE_ENV=production PORT=3000 HOSTNAME=0.0.0.0 PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin' \
 --change 'CMD ["node","server.js"]' \
 backups/web-pre-national-20260907.tar jailmap-web:pre-national-20260907
docker image tag jailmap-api:20260907-initial jailmap-api:pre-national-20260907
tar -czf backups/source-pre-national-web-20260907.tar.gz src deploy/Dockerfile.web deploy/Dockerfile.api compose.yaml
