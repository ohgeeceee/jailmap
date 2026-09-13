#!/bin/bash
set -euo pipefail
exec 9>/run/lock/jailmap-tls.lock
flock -n 9 || exit 0
cd /root/jailmap
# Never request a certificate against parking/old servers. Both names must
# resolve exclusively to this VPS; no IPv6 is currently configured here.
for domain in jailmap.com www.jailmap.com; do
  for resolver in 1.1.1.1 8.8.8.8; do
    addresses=$(dig +short +time=3 +tries=1 "@$resolver" "$domain" A | grep -E '^[0-9.]+$' | sort -u || true)
    ipv6=$(dig +short +time=3 +tries=1 "@$resolver" "$domain" AAAA | grep ':' || true)
    if [[ "$addresses" != '74.208.64.42' || -n "$ipv6" ]]; then
      echo "Waiting for DNS: $domain must resolve to 74.208.64.42 without an obsolete AAAA record."
      exit 0
    fi
  done
done
if [[ ! -f /etc/letsencrypt/live/jailmap.com/fullchain.pem ]]; then
  certbot certonly --webroot -w /var/www/jailmap-acme --cert-name jailmap.com \
    -d jailmap.com -d www.jailmap.com --non-interactive --agree-tos --register-unsafely-without-email
fi
if ! cmp -s deploy/nginx-https.conf /etc/nginx/sites-available/jailmap.com; then
  cp /etc/nginx/sites-available/jailmap.com /root/jailmap/backups/nginx-before-tls.conf
  cp deploy/nginx-https.conf /etc/nginx/sites-available/jailmap.com
  if nginx -t; then
    systemctl reload nginx
  else
    cp /root/jailmap/backups/nginx-before-tls.conf /etc/nginx/sites-available/jailmap.com
    exit 1
  fi
fi
curl --fail --silent --resolve jailmap.com:443:127.0.0.1 https://jailmap.com/api/health
echo ' JailMap HTTPS is active.'
