# Idaho Jail Roster Source Discovery

## Scope
All 44 Idaho counties. Discovery completed via official county domains, sheriff pages, and public search results. Results were written to `data/idaho-jail-sources.csv`.

## Summary

### Tier 1 — High volume / best targets
- Ada: public roster/report pages on `apps.adacounty.id.gov`; parse HTML, daily refresh.
- Canyon: public jail roster at `jailroster.canyoncounty.id.gov`; hourly update cadence.
- Kootenai: official PDF current inmate list hosted on county map domain; good PDF parse target.
- Bonneville: public jail inmate list page; hourly updates; strong HTML parse target.
- Blaine: public detention roster page; good CivicPlus-style HTML target.
- Bannock: public jail roster page exists, but roster is now in sheriff app; may need app/HTML review.

### Tier 2 — Medium volume / mostly actionable
- Bonner, Jefferson, Cassia, Jerome, Idaho County: confirmed public roster/report pages or PDFs.
- Elmore: roster/app maintenance noted; monitor for public page return.
- Valley, Custer: need direct page inspection for hidden roster/PDF links.

### Tier 3 — Rural / limited public access
- Franklin and Power have confirmed public roster pages and should be early Tier 3 adapters.
- Madison appears to have sheriff/jail search surfaces worth confirming.
- Oneida and Teton are effectively no-local-jail cases; use contracting county sources if policy allows.
- Many remaining rural counties show sheriff contact pages only, with no confirmed public roster.

## Next actions
1. Verify ambiguous counties by direct fetch of suspected roster pages/PDFs.
2. Build per-county adapters for confirmed HTML/PDF sources.
3. For app-only counties, determine whether a scrape path is allowable or whether manual outreach is required.
4. Decide policy for inmates housed in neighboring counties.
