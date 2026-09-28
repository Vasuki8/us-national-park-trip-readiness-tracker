# ParkReadiness — U.S. National Park Trip Readiness Tracker

An independent, light-theme planning pilot for Yosemite, Rocky Mountain, Yellowstone, Zion and Grand Canyon. This is a development foundation, **not a live conditions service or a completed public release**.

## This increment

A searchable five-park directory, static park pages, source-backed entry checks for Yosemite and Rocky Mountain, a self-reported trip checklist, and explicit coverage/freshness labels. The other three parks have official planning links but no reviewed entry determination yet. Reviews expire after seven days; unsupported years and areas never inherit an exemption.

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

`npm run preview` serves the built static site. Windows users can run these commands in PowerShell. No API key is required to build the committed development snapshot.

## Explicit local collection — not connected to publication

Obtain your own NPS API key and set `NPS_API_KEY` only in your local shell or private CI secret. Never commit a key or use a public/frontend-prefixed variable. The repository's secret configuration has not been inspected.

```sh
uv run --frozen python -m tracker --park yose --data-dir data/alerts
npm run validate:data
```

A failed request exits nonzero and retains last-good records with failure metadata. A suspicious record drop is quarantined rather than treated as closure removal. Live transport/schema compatibility must be verified before enabling schedules. Do not publish newly collected records without the remaining evidence, rights and publication review gates.

## Handoff

Read `PROJECT_STATUS.md` first, then `docs/DEVELOPMENT.md`. The approved product design is in `docs/superpowers/specs/2026-09-28-national-park-trip-readiness-design.md`; this increment is scoped in `docs/superpowers/plans/2026-09-28-pilot-foundation.md`.

No blanket licence is assigned to source material. Source and media rights must be reviewed separately. No unreviewed photos or NPS arrowhead marks are included.
