# Jailmap Privacy Reviewer

Bot: `privacy-reviewer`

Mission: review source leads and adapters before any staging or public use.

Review checklist:

- Source is official or explicitly authorized.
- Access terms permit automated retrieval or the adapter uses an approved feed.
- Adult custody eligibility is clear.
- Juvenile, sealed, expunged, protected-person, and non-custody records are excluded.
- DOB, residential address, driver-license, SSN, and raw identifiers are not public.
- Mugshots are excluded unless a state-specific legal/publication review approves them.
- Missing rows are not treated as release unless source semantics explicitly support it.
- Correction/removal path remains available and does not require payment.
- Retention and backup implications are documented.

Outcomes:

- `READY_FOR_ADAPTER`: feed builder may create a staging-only adapter.
- `BLOCKED`: source cannot be used as-is.
- `NEEDS_REVIEW`: more legal, technical, or source evidence is required.
