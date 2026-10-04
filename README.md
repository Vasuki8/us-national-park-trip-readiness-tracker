# National Park Explorer & Trip Planner — ParkReadiness repository

This repository develops National Park Explorer & Trip Planner for Yosemite, Rocky Mountain, Yellowstone, Zion and Grand Canyon. The [permanent owner instructions](docs/PROJECT_INSTRUCTIONS.md) define the broader park-discovery and trip-planning product, engineering responsibilities, architecture principles and phased priorities. Readiness is one part of that experience.

The current implementation is an independent, light-theme planning pilot. The [public pilot is live](https://vasuki8.github.io/us-national-park-trip-readiness-tracker/) with stored guidance and manually collected alert snapshots. The revised scope is a development direction; the current pilot features and verified deployment below remain the implementation facts.

## Current pilot

A searchable five-park directory, static park pages, source-backed dated entry checks for Yosemite and Rocky Mountain, a self-reported trip checklist, and data-derived coverage/freshness labels. Yellowstone, Zion and Grand Canyon now have reviewed general-entry source observations, but their cited statements do not publish effective date ranges. These notes remain undated and do not grant exemptions through the date checker.

Reviews expire after seven days; unsupported years and areas never inherit an exemption. Directory age labels update in the browser without a new build. Stored source reviews, dated rules and recent successful alert checks are counted separately.

The Python NPS alerts collector has conservative pagination, retry limits, response validation, last-good retention, clock checks and atomic writes. All five parks have owner-approved successful baselines containing 17 retained notices. Durable private review and separate-backup recovery were verified before promotion. Collection is not scheduled; alert freshness expires after four hours. Empty feeds and removed notices never imply an all-clear or reopening.

There are no ads, accounts, analytics, paid APIs, booking inventory or weather forecasts. All pages retain `noindex, nofollow` and the project robots file disallows crawling until the separate indexed-release gates are met. The pilot is not affiliated with the National Park Service.

## Local development

Clone `main` to retain Git history for subsequent pulls and pushes:

```sh
git clone --branch main https://github.com/Vasuki8/us-national-park-trip-readiness-tracker.git
cd us-national-park-trip-readiness-tracker
```

You can also [download the main ZIP](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/archive/refs/heads/main.zip) and extract it. A ZIP does not include Git history. Open the extracted project folder containing `package.json`, `pyproject.toml`, `AGENTS.md` and `PROJECT_STATUS.md`, rather than its parent folder or generated output.

Use Node.js 24, npm and Python 3.12+ with `uv`.

```sh
npm ci
uv sync --frozen
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

`npm run dev` prints the local website URL. `npm run preview` serves the root build. `npm run preview:pages` serves the GitHub project build at `/us-national-park-trip-readiness-tracker/` on port 4324. Use a POSIX/WSL shell for the full command list. Native Windows can run the frontend preview, but the private evidence tools and full suite rely on POSIX permissions; use WSL and its Linux filesystem for those workflows. Run ordinary development tests with `umask 022`; the separate private operator session uses `umask 077`. No API key is required to build the committed development snapshot. The Astro build validates undated source notes separately from the dated-rule and alert schema checks.

Open this repository root in Codex. `AGENTS.md` requires reading the complete permanent policy in `docs/PROJECT_INSTRUCTIONS.md`, then the current handoff in `PROJECT_STATUS.md` and the development/operator guides. Codex handles routine engineering and authorized operations; the owner makes consequential product, cost, rights, privacy and strategic decisions. Keep any NPS key and real private evidence outside the project folder.

GitHub Pages release/rollback remains manual and uses an already verified artifact matching the configured hosting path. The live pilot passed deployment, older-version rollback and restoration checks against the exact hosted pages/assets, plus actual browser interaction checks. See `docs/PAGES_RELEASE.md` for release evidence and rollback preparation, and `docs/RELEASE_READINESS.md` for how external evidence differs from the conservative automated report.

The read-only readiness report defaults to an ad-free, unindexed pilot. Use `--target indexed` or `--target advertising` to include the corresponding later-release gates. Source review, public alert data, backup, source rights and hosting/rollback remain required for every target. Detected ads or changed pilot indexing controls still require review.

## Read-only integration preflight first

Obtain your own NPS API key and provide `NPS_API_KEY` privately, not in command arguments, committed files or a public/frontend-prefixed variable.

```sh
uv run --frozen python -m tracker.preflight
```

The successful keyed GitHub preflight is run `36628434444`: all five parks passed with `gate_passed:true`. See `docs/NPS_PREFLIGHT.md`. The diagnostic never publishes or writes park snapshots; rerun it with your privately supplied key when checking provider compatibility.

## Durable private collection

The complete first-session sequence is in [the durable collection runbook](docs/DURABLE_COLLECTION_SESSION.md), including separate verified backups, human review, alert staging and recovery checkpoints.

The separate [park-profile promotion workflow](docs/PROFILE_PROMOTION.md) binds
the exact five-park projection to a new text-rights review and immutable approval
bundle, then prepares/rechecks a paired public-file patch. The five-park profile
pair and its Overview/When to Visit consumers are implemented; their original
source clocks are retained. Existing guidance/alert approvals and backups do
not cover profiles.

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

After private collection and preview, the offline [alert-data candidate preparer](docs/ALERT_DATA_PROMOTION.md) can write a reviewable patch outside the checkout. Its optional `--archive-dir` check verifies continuity against the complete private archive when observations or changes are omitted from the bounded preview. A read-only `--check` mode compares the recorded candidate hash and exact patch against all six current public base files before an authorized application. It preserves paired snapshots/history and performs no public-data write or approval. Applying real data remains a separate operator decision.

## Handoff

Read `AGENTS.md` and the complete [permanent project instructions](docs/PROJECT_INSTRUCTIONS.md), then `PROJECT_STATUS.md` and `docs/DEVELOPMENT.md`. The initial pilot design in `docs/superpowers/specs/2026-09-28-national-park-trip-readiness-design.md` and implementation plans in `docs/superpowers/plans/` are historical where they conflict with the revised scope. The project Pages increment is `2026-09-30-pages-base-path.md`; existing source-scope decisions are documented in `docs/ENTRY_SOURCE_REVIEW.md`. Follow the current Phase 1 milestone and [recorded foundation assessment](docs/FOUNDATION_ASSESSMENT.md).

The separate [private profile collection guide](docs/PROFILE_COLLECTION.md)
documents five-park checkpoints, offline verification/restore and unapproved
review exports. Promotion and source-backed park overview consumers are
implemented separately; these private commands do not deploy the live pilot.

The separate [private activity collection guide](docs/ACTIVITY_COLLECTION.md)
documents bounded header-authenticated `/thingstodo` requests, immutable
five-park checkpoints, offline recovery and unapproved review exports. This
tooling is verified with synthetic sources. The separate
[reviewed activity promotion workflow](docs/ACTIVITY_PROMOTION.md) now binds
complete inventories or a versioned minimal catalog to exact text-rights review
and private approval/recovery,
prepares and rechecks a paired public-file patch, and validates the pair at build
and release-readiness boundaries. The owner-approved version 2 public pair now
contains 129 exact NPS titles, official links and source category views, with
seven explicitly withheld listings among 136 retained source summaries.
The reviewed bundle passed private upload, fresh remote download and restore
verification before paired promotion. Original source clocks are preserved;
private prose, quotations, tracking links, media and marks are excluded.
See the [activity source review](docs/ACTIVITY_SOURCE_REVIEW.md) and current
handoff. Availability and unsupported planning fields remain unverified or
unknown. Next build Things to Do from the validated catalog; this data promotion
adds no visitor renderer or live deployment.

No blanket licence is assigned to source material. Source and media rights must be reviewed separately. No unreviewed photos or NPS arrowhead marks are included.
