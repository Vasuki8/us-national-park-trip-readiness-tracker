# ParkReadiness — U.S. National Park Trip Readiness Tracker

An independent, light-theme planning pilot for Yosemite, Rocky Mountain, Yellowstone, Zion and Grand Canyon. This is a development foundation, **not a live conditions service or a completed public release**.

## Current pilot

A searchable five-park directory, static park pages, source-backed dated entry checks for Yosemite and Rocky Mountain, a self-reported trip checklist, and data-derived coverage/freshness labels. Yellowstone, Zion and Grand Canyon now have reviewed general-entry source observations, but their cited statements do not publish effective date ranges. These notes remain undated and do not grant exemptions through the date checker.

Reviews expire after seven days; unsupported years and areas never inherit an exemption. Directory age labels update in the browser without a new build. Stored source reviews, dated rules and recent successful alert checks are counted separately.

The Python NPS alerts collector has conservative pagination, retry limits, response validation, last-good retention, clock checks and atomic writes. A keyed read-only preflight has passed for all five parks. All committed alert snapshots remain `never_checked`; durable private collection, review and publication are still pending. Collection is not scheduled. Removed notices never imply a reopening.

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
npm run build:pages
npm run test:site:pages
npm run test:browser:pages
```

`npm run preview` serves the root build. `npm run preview:pages` serves the GitHub project build at `/us-national-park-trip-readiness-tracker/` on port 4324. Use a POSIX/WSL shell for the full command list. No API key is required to build the committed development snapshot. The Astro build validates undated source notes separately from the dated-rule and alert schema checks.

GitHub Pages release/rollback remains manual and uses an already verified artifact matching the configured hosting path. The website is not live. See `docs/PAGES_RELEASE.md` for the deployment contract and `docs/RELEASE_READINESS.md` for the remaining gates.

The read-only readiness report defaults to an ad-free, unindexed pilot. Use `--target indexed` or `--target advertising` to include the corresponding later-release gates. Source review, public alert data, backup, source rights and hosting/rollback remain required for every target. Detected ads or changed pilot indexing controls still require review.

## Read-only integration preflight first

Obtain your own NPS API key and provide `NPS_API_KEY` privately, not in command arguments, committed files or a public/frontend-prefixed variable.

```sh
uv run --frozen python -m tracker.preflight
```

The successful keyed GitHub preflight is run `36628434444`: all five parks passed with `gate_passed:true`. See `docs/NPS_PREFLIGHT.md`. The diagnostic never publishes or writes park snapshots; rerun it with your privately supplied key when checking provider compatibility.

## Durable private collection

The entry-page capture command can check private storage setup offline before a live run:

```sh
uv run --frozen python -m tracker.entry_review_live --check-only --store /absolute/private/entry-review --packet-output-dir /absolute/private/review-packets --expected-revision empty
```

Both private parent directories must already exist with owner-only permissions. Use the exact current ledger revision for later checks. This command makes no requests or writes and does not approve source guidance. See `docs/PERSISTENT_ENTRY_CAPTURE.md` for the subsequent explicit live-capture/review path.

After reviewing a successful preflight, collect into owner-controlled durable private POSIX/WSL storage outside the repository:

```sh
uv run --frozen python -m tracker.stage collect --live --park all --staging-dir /absolute/private/alert-staging
uv run --frozen python -m tracker.stage status --park all --staging-dir /absolute/private/alert-staging
```

A failed request retains last-good records with failure metadata. A suspicious record drop is quarantined rather than treated as closure removal. The batch can have partial committed progress; inspect status and recover pending receipts before retrying. These commands do not publish or back up data. See `docs/STAGING_COLLECTION.md`. Durable evidence, backup and review remain required before public collection or schedules.

## Handoff

Read `PROJECT_STATUS.md` first, then `docs/DEVELOPMENT.md`. The approved product design is in `docs/superpowers/specs/2026-09-28-national-park-trip-readiness-design.md`. Implementation plans are in `docs/superpowers/plans/`; the project Pages increment is `2026-09-30-pages-base-path.md`. Source-scope decisions are documented in `docs/ENTRY_SOURCE_REVIEW.md`.

No blanket licence is assigned to source material. Source and media rights must be reviewed separately. No unreviewed photos or NPS arrowhead marks are included.
