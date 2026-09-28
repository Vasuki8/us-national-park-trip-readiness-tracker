# ParkReadiness — U.S. National Park Trip Readiness Tracker

An independent, light-theme planning pilot for Yosemite, Rocky Mountain, Yellowstone, Zion and Grand Canyon. This is a development foundation, **not a live conditions service or a completed public release**.

## Current pilot

A searchable five-park directory, static park pages, source-backed dated entry checks for Yosemite and Rocky Mountain, a self-reported trip checklist, and data-derived coverage/freshness labels. Yellowstone, Zion and Grand Canyon now have reviewed general-entry source observations, but their cited statements do not publish effective date ranges. These notes remain undated and do not grant exemptions through the date checker.

Reviews expire after seven days; unsupported years and areas never inherit an exemption. Directory age labels update in the browser without a new build. Stored source reviews, dated rules and recent successful alert checks are counted separately.

The Python NPS alerts collector has conservative pagination, retry limits, response validation, last-good retention, clock checks and atomic writes. All committed alert snapshots are `never_checked`: no live NPS request has been verified and collection is not scheduled. Removed notices never imply a reopening.

There are no ads, accounts, analytics, paid APIs, booking inventory or weather forecasts. All pages are `noindex, nofollow` and robots are disallowed until the production gates are met. The pilot is not affiliated with the National Park Service.

## Local development

Use Node.js 24, npm and Python 3.12+ with `uv`.

```sh
npm ci
npm run dev
```

```sh
npm test
uv run --frozen python -m unittest discover -s tests -p 'test_*.py' -v
npm run check
npm run build
npm run test:site
npx playwright install chromium
npm run test:browser
```

`npm run preview` serves the built static site. Windows users can run these commands in PowerShell. No API key is required to build the committed development snapshot. The Astro build validates undated source notes separately from the dated-rule and alert schema checks.

## Read-only integration preflight first

Obtain your own NPS API key and provide `NPS_API_KEY` privately, not in command arguments, committed files or a public/frontend-prefixed variable.

```sh
uv run --frozen python -m tracker.preflight
```

The initial GitHub preflight received an empty key and reported **not_configured / gate_passed=false**. This is a blocked integration gate, even though the diagnostic job completed. Add `NPS_API_KEY` as a repository Actions secret and rerun the existing preflight. See `docs/NPS_PREFLIGHT.md`. The diagnostic never publishes or writes park snapshots.

## Explicit local collection — not connected to publication

Only after reviewing a successful preflight, collection can be tested locally:

```sh
uv run --frozen python -m tracker --park yose --data-dir data/alerts
npm run validate:data
npm run build
```

A failed request exits nonzero and retains last-good records with failure metadata. A suspicious record drop is quarantined rather than treated as closure removal. Live compatibility, durable evidence and publication safeguards must be verified before enabling schedules. Do not publish newly collected records without the remaining evidence, rights and publication reviews.

## Handoff

Read `PROJECT_STATUS.md` first, then `docs/DEVELOPMENT.md`. The approved design is in `docs/superpowers/specs/2026-09-28-national-park-trip-readiness-design.md`. Implementation plans are in `docs/superpowers/plans/`; the latest continuation is `2026-09-28-source-readiness.md`. Source-scope decisions are documented in `docs/ENTRY_SOURCE_REVIEW.md`.

No blanket licence is assigned to source material. Source and media rights must be reviewed separately. No unreviewed photos or NPS arrowhead marks are included.
