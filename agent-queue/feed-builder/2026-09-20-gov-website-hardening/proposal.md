# Proposed adapter changes

Target: `backend/adapters/gov_website.py`

This is a review specification, not an executable patch.

1. Import `ZoneInfo`, define `SOURCE_TIMEZONE = ZoneInfo("America/Chicago")`, and attach that zone
   in `_parse_date`. Do not label a local Arkansas timestamp as UTC.
2. Require a parseable age of at least 18. Fail closed on an unknown/unparseable age unless the
   source review establishes another adult-eligibility signal.
3. Require both a stable booking number and valid booking date. Never substitute `pulled_at` for a
   malformed booking date.
4. Set `mugshot_url` to `None`; do not extract or retain the image URL without source-specific
   approval.
5. Parse `first_page_html` directly. Iterate only `page_urls[1:]` for subsequent requests so page
   one is not downloaded twice.
6. Remove the `try/except ... break` around later-page requests. Any advertised-page failure must
   fail the complete snapshot.
7. Treat `MAX_ROWS` as a hard failure rather than silently truncating a roster.
8. Reject duplicate booking numbers after assembling all pages.
9. Preserve the existing host authorization check, maximum page count, maximum row count, and
   staging-only registration throughout review.
