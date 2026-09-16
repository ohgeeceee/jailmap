#!/usr/bin/env bash
# Redeploy JailMap api + web containers with the current RELEASE_TAG images.
set -euo pipefail
cd /root/jailmap
export RELEASE_TAG=national-20260907
docker compose up -d --no-deps api web
