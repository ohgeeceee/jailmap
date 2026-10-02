# JailMap

JailMap is a public search surface for official jail-custody records, built around responsible source review, privacy safeguards, and a human approval step before publication.

The project uses official county, sheriff, city, jail, court, and open-data sources. It excludes juveniles and protected records, avoids publishing raw personal identifiers, and maintains a correction/removal path.

## Local development

```bash
npm install
npm run dev
```

Useful commands:

```bash
npm run lint
npm run build
npm run test:route-check
```

## Project areas

- `src/` and `backend/` — application and ingestion code
- `prisma/` — data schema
- `tests/` — application and source-receipt tests
- `references/` and `ingestion/` — source-review and ingestion documentation
- `MISSION.md` — publication, privacy, and agent operating rules

## Responsible data use

Source enablement and publication require human review. See `MISSION.md` for the project’s privacy and operational guardrails.
