# Pilot Foundation Implementation Plan

> Executed inline under the owner's development authorization. Exact checks are recorded in PROJECT_STATUS.md. This increment is implemented and CI-verified; the full M1 release still has separate source/integration gates.

**Goal:** A usable five-park development pilot that never presents missing live data as operating conditions.
**Architecture:** Astro static HTML, small TypeScript browser scripts, pure clock-injected readiness decisions, Python/uv collectors producing validated snapshots.
**Tech stack:** Astro 7.3.5, TypeScript 6.0.3, Node 24 in CI, Python 3.12+, uv. No paid services or browser API keys.
**Spec:** `docs/superpowers/specs/2026-09-28-national-park-trip-readiness-design.md`.

## Global constraints

Light theme. Five pilots, not a claimed visitation ranking. No safety scores, all-clear inference, live inventory, accounts, tracking, active ads or paid dependencies. Alerts stale after four hours. Entry reviews expire after 168 hours. Rules never extrapolate to another year. No schedule, deployment or production indexing. Keep source review, collection, effective, build and publication clocks distinct.

## Review focus

Test malformed and leap dates, exact boundaries, unknown area/time, exception handling, source conflicts, clock rollback, pagination, suspicious dropouts, credential leakage, no-JavaScript behavior and mobile overflow. Every unknown needs a visible interpretation; no missing field may grant an exemption.

## Task 1 — Reviewed inventory and readiness engine

**Files:** `data/parks.json`, `data/rules.json`, `data/alerts/*.json`, `src/lib/readiness.ts`, `scripts/validate-data.ts`, Node tests.
**Interfaces:** `evaluateEntry(rules, trip, now) -> Decision`; `freshness(checkedAt, hours, now) -> missing/fresh/stale/invalid`; `parkLocalDate(now, timezone) -> YYYY-MM-DD`.

- [x] Write failing tests for dates, year boundaries, areas, times, conflicts and missing/stale evidence.
- [x] Implement the pure engine and reviewed Yosemite/Rocky Mountain guidance; leave three parks unreviewed.
- [x] Validate source allowlists, excerpt hashes and snapshot contracts.
- [x] Run Node tests and retain regressions for invalid date normalization.

## Task 2 — Conservative alerts collector, not enabled automation

**Files:** `tracker/alerts.py`, `tracker/__main__.py`, `pyproject.toml`, `uv.lock`, Python tests.
**Interfaces:** `collect(park_code, previous, now, fetch_page) -> snapshot`; `request_page(park_code, start, key)`; `write_snapshot(path, snapshot)`.

- [x] Write synthetic tests for complete pagination, empty success versus failure, bad URLs, duplicate IDs, mismatched parks, record drops and preserved clocks.
- [x] Implement fixed-host private-header transport, bounded retries, redirects disabled and atomic writes.
- [x] Run 20 Python tests, including query-secret rejection and previous-clock consistency regressions.
- [ ] Verify a real NPS response with an owner-controlled private key before claiming live integration. This is a later release gate, not completed by synthetic tests.

## Task 3 — Static interface and complete verification

**Files:** Astro pages/components/layout, browser scripts, CSS, static/browser tests, CI, documentation.
**Interfaces:** UI consumes Task 1 inventory/rules and Task 2 snapshot schema; selections remain in page memory; checklist resets on trip changes.

- [x] Write generated-HTML and browser assertions before the interface implementation.
- [x] Implement directory, five park pages, source panels, checklist and disclosure routes.
- [x] Add noindex/ad-free gates and meaningful no-JavaScript links; disable controls that cannot function without scripts.
- [x] Pin dependencies and generate actual npm lockfiles on GitHub Actions without lifecycle scripts; remove the temporary write-enabled bootstrap after completion.
- [x] Repair explicit Node type configuration detected by full Astro checking and retain a toolchain regression test.
- [x] Verify full installation, Astro check/build, 35 Node tests, 20 Python tests, 18 static-output tests and 6 browser tests. All 79 passed in Actions run 36479129760 for implementation head 7c39fb34291a6d334355cd883f250604d7ee5154.
- [x] Open draft PR #1, leave main unmerged and production undeployed, and update PROJECT_STATUS.md with exact evidence and remaining gates.

## Scope rulings

The initial checker handles one-day first-entry private-vehicle travel; special circumstances need direct official review. Road/facility/fee/forecast collection, complete source coverage, raw evidence retention, semantic history, daily source-change review, hosting and publication remain later gates. No-JavaScript checklist controls are disabled to avoid a misleading static progress counter. These limitations do not reduce the full approved product target.
