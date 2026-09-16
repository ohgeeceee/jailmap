# Source scout checkpoint — 2026-09-13 18:25 UTC

status: NEEDS_REVIEW
files_changed: data/official-jail-source-leads.csv

- OK TX/Dallas: http_200, hits=[none], strategy=search_form
  source_evidence: https://www.dallascounty.org/jaillookup/ -> https://www.dallascounty.org/jaillookup/
  publication_risk: unchanged (staging_only); requires human review before adapter work
- OK TX/Tarrant: http_200, hits=[none], strategy=search_form
  source_evidence: https://inmatesearch.tarrantcounty.com/ -> https://inmatesearch.tarrantcounty.com/
  publication_risk: unchanged (staging_only); requires human review before adapter work
- OK TX/Bexar: http_200, hits=[civicplus], strategy=manual_discovery
  source_evidence: https://www.bexar.org/35/Justice -> https://www.bexar.org/35/Justice
  publication_risk: unchanged (staging_only); requires human review before adapter work
- OK FL/Miami-Dade: http_200, hits=[image_captcha], strategy=search_form
  source_evidence: https://www2.miamidade.gov/Apps/mdcr/InmateSearch/ -> https://www2.miamidade.gov/Apps/mdcr/InmateSearch/
  publication_risk: unchanged (staging_only); requires human review before adapter work
- OK FL/Broward: http_200, hits=[image_captcha], strategy=angular_search
  source_evidence: https://apps.sheriff.org/arrestsearch -> https://apps.sheriff.org/arrestsearch
  publication_risk: unchanged (staging_only); requires human review before adapter work
- OK FL/Palm Beach: http_200, hits=[pdf_roster,json_api], strategy=json_endpoint
  source_evidence: https://www.pbso.org/arrest-jail_menu -> https://www.pbso.org/arrest-jail_menu
  publication_risk: unchanged (staging_only); requires human review before adapter work
- OK CA/Riverside: http_200, hits=[civicplus], strategy=manual_discovery
  source_evidence: https://www.riversidesheriff.org/183/Corrections-Operations -> https://www.riversidesheriff.org/183/Corrections-Operations
  publication_risk: unchanged (staging_only); requires human review before adapter work

## Summary
- probed: 7, ok: 7, blocked: 0, with platform hits: 5
next_action: human reviews probed_ok leads; feed-builder may draft staging-only adapters for approved ones.
