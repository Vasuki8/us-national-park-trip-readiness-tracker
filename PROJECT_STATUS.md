# Project status and handoff

Updated: 2026-09-28. Milestone: **M1 foundation implemented; M1 release incomplete**.

## Owner-approved direction

AdSense-first eventual public product, light theme, no paid data dependency. Pilot five parks before expanding to 20. Trustworthy displayed data precedes traffic expansion, monetization and production indexing. No safety scores or all-clear claims.

## Implemented

- Static Astro directory and five park pages, search/state filters, responsive light design, source/methodology and disclosure pages.
- Three official-page-reviewed 2026 entry rules: Yosemite, Rocky Mountain rest-of-park, Rocky Mountain Bear Lake Road. Review evidence includes an exact excerpt hash and observation time, not a falsely attributed source-update time.
- One-day first-entry private-vehicle guidance with park-local date/time inputs, area-specific rules, annual bounds, conservative exact-end-time handling, unresolved exceptions, and seven-day review expiration.
- Self-reported checklist with reset when trip details change; no persistent storage or booking verification.
- Five explicit never-collected alert snapshots; no live operational condition claims.
- Python collector and runtime/build validation with bounded paging/retries, private API-key header, redirects disabled, source/park validation, suspicious-drop quarantine, retained last-good values and atomic writes.
- Read-only PR CI with unit tests, Astro type checking/build, static route tests, Chromium interaction/mobile/no-JavaScript checks and verification artifacts.

## Verification before remote build

34 Node core/data tests and 20 Python collector/transport tests passed in the editing session. Standalone browser-script TypeScript checking and inventory validation passed. Regression failures were reproduced before fixes for impossible date normalization, cross-park notice URLs, incoherent previous snapshot timestamps and credential-like URL queries.

Full Astro build, generated-HTML checks (18 tests) and browser checks (6 tests) require the repository CI result. They were not executable locally because external dependency downloads are unavailable in the editing environment. Do not describe them as passed without reading a subsequent CI run. Node dependencies are pinned; the initial npm lockfile is generated on a remote runner, not hand-fabricated.

## Not activated / not verified

No production deployment, scheduled collection, advertising, analytics, accounts or paid service. No live NPS API request verified. Repository secrets were not inspected: no claim about whether the owner has configured an API key. No weather integration, complete roads/facilities coverage, publication history or automated editorial review. All pages remain noindex.

Yellowstone, Zion and Grand Canyon entry rules are deliberately not filled in. The two reviewed parks do not constitute a complete park readiness audit. This increment is not the full source-backed M1 release.

## Next coherent task

First read the feature PR and current CI results; fix failures and preserve newer changes. Then verify the NPS transport against a real key in a private environment without publishing, audit pilot alert source shapes and add a live-response fixture stripped of secrets. Review entry/permit source coverage for the remaining three parks and establish an evidence retention/change-review workflow. Only after data, rights and publication checks pass should hosting be configured and the development noindex gate reconsidered.

## Guardrails

Never advance source-update or publication timestamps from build/collection clocks. Never infer opening status from a missing/removed notice. Never carry a 2026 rule into 2027. Never make generated content indexable merely to add more search pages. Never put private keys into site JSON, generated JavaScript, commit messages or logs. No purchases, external hosting changes or monetization activation are part of this increment.
