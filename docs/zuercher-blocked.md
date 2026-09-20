# Zuercher Vendor Portals — IP Blocked

**Status:** All `*.zuercherportal.com` endpoints return HTTP 500 (IP rate-limited).
This affects both MT counties (Ravalli, Jefferson) and newly discovered counties (AL, IL, IA, SC, SD).

**Mitigation:**
- Disable Zuercher jurisdictions in `records.jurisdictions` (`enabled=false`)
- Use a proxy or wait 24 hours for Zuercher to lift the block
- Alternative: run ingest from a different IP (e.g., Montana Blotter VPS has different IP)
- Consider Playwright with residential proxy for high-volume vendor vendors

**Affected jurisdictions:**
- MT Jefferson, Ravalli
- AL Limestone, IL Menard, IL Rock Island, IA Marshall, SC Laurens, SD Lincoln
