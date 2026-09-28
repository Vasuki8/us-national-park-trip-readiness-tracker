# Staging Collection Implementation Plan

> Execute inline using executing-plans and test-driven-development. This is the staging-only continuation requested by the owner, not permission to merge, publish, schedule or change provider accounts.

**Goal:** Connect the existing NPS collector to the private history archive without modifying website data, while preserving recoverable completed candidates.
**Architecture:** An operator-controlled staging directory owns the existing archive plus bounded pending receipts. Persist a validated candidate with its expected archive parent before appending. A compare-and-append guard detects intervening archive writes; recovery reuses the receipt without another request or a new timestamp.
**Tech stack:** Existing Python standard library and uv; existing Node/Astro CI unchanged. No new dependency or service.
**Spec:** `docs/superpowers/specs/2026-09-28-national-park-trip-readiness-design.md`, sections 7–9 and 12–13. Prior handoff at `d4eb109` names this exact next task.

## Global constraints

Private staging only. All five public snapshots remain `never_checked`; no source review, publication or effective timestamp changes. Preserve baseline/add/edit/disappearance semantics and last-good retention. No automatic lock removal, pruning or conflict overwrite. Live CLI collection requires `--live` and a privately supplied `NPS_API_KEY`; offline tests/recovery never require a key. No hosted workflow, storage service, public projection or schedule in this increment.

## Review focus

- Intervening offline archive import during network collection: stale-parent candidates must not be appended.
- Interrupted write before or after archive commit: only committed history is authoritative; receipts enable exact recovery.
- Collector-valid but archive-invalid source shapes: preserve the attempt as quarantined without retaining unsafe candidate text.
- Unsupported parks, invalid clocks, damaged receipts, symlinks and unsafe destinations: refuse before network or public writes.
- Reports and provider credential echoes: no raw notice text, keys or exception messages in operator output; no credential echoes retained.

## Task 1 — Expected-parent archive append

**Files:** `tracker/history_store.py`, `tests/test_staging_cas.py`.
**Interface:** `HistoryStore.append(snapshot, *, expected_head=UNSET) -> str`; omitted argument preserves current callers. A supplied parent is checked under the existing writer lock; an exact already-committed retry with that parent is idempotent.
- [x] Write/run tests showing correct parent, empty parent, stale parent, retry and malformed parent behavior.
- [x] Implement optional expected-head contract without changing stored schemas or existing callers.
- [x] Run targeted tests and compare baseline behavior before proceeding.

## Task 2 — Recoverable staging orchestration

**Files:** `tracker/staging.py`, `tests/test_staging.py`, `tests/test_staging_crash.py`.
**Interfaces:** `StagingCollector(root).collect(code, checked_at, fetch_page) -> dict`; `.recover(code) -> dict`; `.status(code) -> dict`. Archive remains `root/archive`; receipt is `root/pending/{code}.json`.
- [x] Write failing end-to-end tests against the actual existing collector/store using synthetic transport responses.
- [x] Implement strict bounded receipts, exclusive staging writer, validation-before-journaling, expected-parent append, offline recovery and scalar-only status.
- [x] Test success/failure/quarantine, five-park isolation, pre/post-commit interruption, no-network recovery, moved-head conflict, stale clocks, corrupted objects and protected destinations.
- [x] Test actual abrupt subprocess termination and explicit lock recovery; do not claim power-loss or network-filesystem durability.

## Task 3 — Operator CLI, full verification and handoff

**Files:** `tracker/stage.py`, `tests/test_stage_cli.py`, `docs/STAGING_COLLECTION.md`, `PROJECT_STATUS.md`.
**Interface:** `python -m tracker.stage collect --live|recover|status --park CODE --staging-dir PATH`. Status/recovery are offline. Missing key/consent refuses before any state write or request. Reports separate private archival success from provider success.
- [x] Write/run failing CLI tests for private-key/consent gates, safe diagnostics, output limits and no website writes.
- [x] Implement CLI with unchanged private-header transport and rejection of credential echoes before retention.
- [x] Run all new tests locally; run the complete existing Python/Node/Astro/static/browser suite in GitHub CI.
- [x] Self-review the diff, preserve later remote changes, update PR and handoff with exact verification and limitations. Keep PR draft/unmerged.

## Execution notes

Local workspace contains hash-verified copies of the three existing Python dependencies, not a full clone (container GitHub DNS failed). GitHub CI is required for the complete regression suite. No independent reviewer is available; author self-review is recorded separately.

## Completion record

Implementation `afdf98f89f4481fe59cd666c59032be415f11348` passed full GitHub Actions run **36487323692**, Verify pilot #12, job **109147282228**. The temporary PR merge was `83a051e91c57d2ce36d976a2d8e96d75e70f2b22` against unchanged main; no actual merge occurred. Results: 50 Node, 128 Python, 18 static-output and 10 browser tests, **206 total**. Astro check returned zero errors/warnings/hints and the full static build passed.

The **39 added tests** passed locally and in CI. Expected-parent tests first failed on the absent argument; staging/CLI tests failed on absent modules. Author self-review found a missing pending-file reservation; a failing regression preceded the correction. Three subprocess-termination tests cover before/during/after archive commit. Uploaded code/test blob hashes match the locally tested files. No existing test was removed or weakened.

Ruling: Receipt persistence begins after a complete validated collector result; an in-flight response lost before persistence is not recoverable. Recovery never invents a new source check or publication time. A stricter archive-validation rejection produces a quarantined attempt with only the previous accepted records. Existing collector, on-disk schema, site data, frontend and workflows are unchanged.

Final review: **author self-review, no independent reviewer**. Existing runtime/install-script warnings and local-filesystem durability limits remain documented. No live provider requests, secret recheck, public data export, schedule, deployment or merge occurred. Follow the handoff for the next public-history projection task; the staging path is complete within this private, unscheduled boundary.
