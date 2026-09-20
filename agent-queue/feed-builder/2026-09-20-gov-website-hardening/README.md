# GovernmentWebsite roster hardening draft

Status: `IMPLEMENTED_LOCALLY` — tests and source dry runs pass; not deployed and not approved for publication.

## Scope and evidence

Two official Arkansas sheriff sources use `gov_website_staging`:

| Source | 2026-09-20 dry run | Private snapshot after refresh |
| --- | ---: | ---: |
| Carroll County Sheriff | 83 validated | 83 staged |
| Poinsett County Sheriff | 100 validated | 100 staged |

Aggregate review of the previous private snapshots found zero missing ages, zero rows under 18,
zero missing booking identifiers/dates, and zero rows without charges. No personal row data was
printed or copied into this review.

## Release blockers found

1. `fetch()` catches a later-page failure and returns a partial roster. In a complete-snapshot
   system, committing that result could make absent people appear to have left custody.
2. The first page is downloaded twice.
3. Booking timestamps are labeled UTC even though both Arkansas sources display local time.
4. The generic adapter collects mugshot URLs although no Arkansas-specific mugshot review exists.
5. Adult eligibility is parsed but not enforced by the adapter.
6. A malformed/missing booking date is silently replaced with fetch time, manufacturing freshness.

## Proposed change

The reviewed items in `proposal.md` are implemented in the working tree with focused regression
tests. Both official sources were rerun in dry-run mode with unchanged valid counts.
Keep both jurisdictions `enabled=false, staging_only=true` until a human reviews sampled source rows,
official access terms, retention/correction policy, and the before/after dry-run counts.

Required tests:

- first page is parsed from the already-fetched response and is not requested twice;
- any pagination request failure fails the complete snapshot;
- duplicate or missing booking numbers fail the snapshot;
- malformed booking dates fail the snapshot rather than using fetch time;
- Arkansas timestamps use `America/Chicago`, including DST;
- ages below 18 and missing/unparseable ages are excluded or fail closed under the approved policy;
- mugshot URLs remain absent;
- pagination and row limits stay bounded.

## Rollback

No runtime change was made. If this draft is later applied, rollback is the prior
`backend/adapters/gov_website.py` plus its prior API image. Staged rows can be refreshed from the
last reviewed adapter; public tables must remain untouched throughout review.
