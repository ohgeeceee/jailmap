# Source Receipt capability

## Capability

A visitor viewing a public booking can inspect a compact, copyable receipt that
states where the displayed record came from, when JailMap last observed it,
which categories the source supplied, and a stable fingerprint that changes when
the public substance of the record changes. The outcome is easier verification
and safer citation without implying that JailMap knows whether an allegation is
true or whether two similar names identify the same person.

## Constraints

- The receipt uses only fields already present in the public booking projection.
- It never includes dates of birth, addresses, contact details, hidden source
  fields, reviewer notes, or internal ingestion data.
- Missing means “not supplied in this public source response,” never “none exists.”
- Freshness describes elapsed time since observation and is not an accuracy score.
- The SHA-256 fingerprint detects changes to the public projection. It is not a
  signature, proof of authenticity, or assertion that the source is correct.
- Suppressed, stale, released, or otherwise unavailable records remain unavailable;
  the receipt cannot bypass publication gates.
- The official source remains authoritative and is always linked.

## Implementation contract

- Actor: any visitor who can already view the public booking.
- Surface: the booking detail page beneath the reported charge and bond sections.
- States: preparing fingerprint, ready, or fingerprint unavailable. The booking
  itself remains usable in every state.
- Inputs: booking number/date, public name, facility/location, charges, bonds,
  source URL, and observation timestamp.
- Outputs: source hostname, observation age, supplied/missing categories, charge
  and bond counts, a shortened SHA-256 fingerprint, and copyable plain text.
- Canonicalization sorts charge and bond projections so ordering-only source
  changes do not alter the fingerprint.
- No new database table, external request, cookie, analytics event, or public API
  field is introduced in the first version.

## Non-goals

- Scoring guilt, identity, source trustworthiness, or factual accuracy.
- Replacing the source record, correction process, or human review.
- Preserving historical versions; a future snapshot ledger may compare receipts.
- Making the fingerprint independently verifiable after the record is unavailable.

## Open questions

- Whether future receipts should be retained as an auditable public change ledger.
- Whether jurisdictions need source-specific completeness categories.
- Whether a signed server receipt should be offered for newsroom/legal workflows.

## Handoff

The first version is ready for direct implementation and focused unit/UI testing.
Historical retention or signed receipts require privacy and architecture review.
