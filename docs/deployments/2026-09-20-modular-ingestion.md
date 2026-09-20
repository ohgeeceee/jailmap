# Modular ingestion staging rollout — 2026-09-20

- Owner: JailMap operations
- Scope: additive `records.adapter_bookings_staging` and `records.adapter_failures` schema; isolated ingestion worker image; first Minnehaha County adapter execution.
- Approval: explicitly approved by the site owner in the active operations session.
- Backup: `backups/jailmap-20260920T042435Z.tar.gz.enc`; SHA-256 verification passed before migration.
- Migration verification: the complete migration first succeeded inside a transaction that was rolled back. It was then committed with `ON_ERROR_STOP=1`.
- Worker artifact: `jailmap-ingestion:20260920`, running as non-root with dropped capabilities and `no-new-privileges`.
- Source verification: official Minnehaha County roster. The adapter filtered `facility=Jail`; 26 electronic-monitoring entries were excluded.
- Initial ingestion correction: the generic table parser mismatched a nine-column body with seven visible headers. All 623 initial staged rows were deleted before publication. No public table was affected.
- Corrected ingestion result: a dedicated nine-column parser staged 621 unique booking keys for facility `census-landmark-1104474475994`. All rows remained `publication_state=staged`; zero non-jail rows, zero missing booking dates, and one source row with no charge text.
- Identity verification: File ID is read from the source's fourth body cell; electronic-monitoring rows are excluded using the source facility field.
- Publication impact: none. The new staging table is not consumed by a public API or search index.
- Scheduling impact: none. No cron or persistent ingestion service was enabled.
- Rollback: stop using the manual ingestion profile, retain/export any review decisions if present, then remove the two additive tables through an approved reverse migration. The verified encrypted backup is the recovery fallback. Existing public tables require no rollback because they were not modified.
