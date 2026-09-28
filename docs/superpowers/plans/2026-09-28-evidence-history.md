# Evidence History Implementation Plan

> Execution: continue the authorized next task inline with test-driven development. This is a private operator capability, not activation of live collection or public history.

**Goal:** Retain reconstructable accepted alert observations and distinguish additions, edits and disappearances without inventing park conditions.
**Architecture:** Validated normalized snapshots feed a pure semantic differ. Small content-addressed evidence objects and immutable observation objects form a per-park hash-linked chain; a locked, atomic head replacement commits each append. An explicit offline CLI imports snapshots and reports verified history. No production database, new dependencies or automatic publication.
**Tech stack:** Python 3.12+ standard library, existing uv/Node/Astro CI.
**Spec:** `docs/superpowers/specs/2026-09-28-national-park-trip-readiness-design.md`, sections 7–9; `PROJECT_STATUS.md` at f232154.

## Global constraints

- Do not modify current site snapshots, dated entry rules or review timestamps.
- Preserve missing, failed, quarantined, checked-feed-only and never-checked meanings.
- Initial successful observation is a baseline, not an invented set of new closures.
- Notice removal means only no longer present in a complete checked feed, never reopening.
- Retain normalized source text, not raw HTTP bodies/headers or merely hashes.
- Do not enable scheduling, deployment, indexing, ads or any paid service.

## Review focus

Interrupted writes must leave a readable old or complete new head; same-instant conflicting replays must be rejected; corrupt/missing evidence must fail closed; failed checks cannot rewrite last-good records; large apparent losses cannot bypass the collector's quarantine policy. Tests belong to the model/store tasks below.

## Task 1 — Snapshot contract and pure history semantics

Files: `tracker/history_model.py`, `tests/history_fixtures.py`, `tests/test_history_model.py`.
Interfaces: `validate_snapshot(value) -> dict` returns a sorted defensive copy; `compare(previous, current) -> dict` returns comparison and changes.
- [x] Test baseline, empty baseline, unchanged/reordered records, add/edit/remove, failed/quarantined retention, recovered baseline, clock conflicts, altered observation times, suspicious drops, hashes, exact schema and credential-shaped URL rejection.
- [x] Run `python -m unittest discover -s tests -p 'test_history_model.py' -v`; observe missing implementation fail.
- [x] Implement the validation and comparison contract; rerun all available tests.

## Task 2 — Immutable store and verified readback

Files: `tracker/history_store.py`, `tests/test_history_store.py`.
Interfaces: `HistoryStore(root).append(snapshot) -> observation_id`; `.read(park_code) -> list[dict]` in chronological order.
- [x] Test evidence deduplication/reconstruction, multi-park isolation, idempotent imports, writer locks, interrupted commit recovery, missing/corrupt objects, forged events, unsafe paths and quota handling.
- [x] Run store tests RED before implementation, then GREEN with the whole Python suite.
- [x] Limit snapshots/objects to 10 MiB, history to 4096 observations per park and archive files to 256 MiB / 65536 entries, and reconstructed snapshot JSON to 64 MiB. Do not prune automatically. Stop rather than overwrite history.

## Task 3 — Offline operator CLI, collector integration and handoff

Files: `tracker/history.py`, `tests/test_history_cli.py`, `tests/test_history_collector.py`, `.gitignore`, `docs/EVIDENCE_HISTORY.md`, `PROJECT_STATUS.md`.
Interfaces: `python -m tracker.history record --snapshot PATH --archive-dir PATH`; `... report --park CODE --archive-dir PATH --limit 20`.
- [x] Test no network/write-on-report, input validation, duplicate JSON keys, safe errors, bounded output, and actual collector-to-history compatibility.
- [x] Import only already-collected snapshots; no API key is required and no producer/scheduler is activated.
- [x] Run full existing GitHub CI, inspect results, self-review the changed files and document exact SHAs/results/limitations.

## Rulings

The container cannot resolve github.com, so GitHub connector reads/writes and full GitHub CI are used; the local workspace contains only the files needed for this increment and must not be represented as a complete clone. The unchanged existing collector is exercised through an integration test in CI. The private archive is ignored by Git and never passed to the website builder. Machine-assisted editorial source review and public-history export remain separate subsequent tasks.

## Local verification and review

54 new tests ran locally and passed. Three additional synthetic real-collector integration tests are included for full CI, because the isolated local workspace is not a full clone. Module-availability failures preceded initial model/store/CLI implementations. Self-review regressions then reproduced a missing destination guard and reconstruction-budget interface; both were implemented and the local suite returned green. Final verification is recorded in PROJECT_STATUS.md after GitHub CI. No fresh-context reviewer is available.

## Additional process-level check

`tests/test_history_crash.py` abruptly terminates a subprocess before head replacement, verifies the old chain is readable, verifies a new writer cannot steal the abandoned lock, and retries only after simulated explicit recovery with the child confirmed stopped. It passed locally. This adds no production behavior and is not a machine power-loss test.

## Completed verification

Code/test head `f43ee4ccd644d3f89868857658767f6b78654e85` passed full GitHub Actions run `36485050775` (Verify pilot #10): Node 50, Python 89, static-output 18, Chromium 10; **167 tests total**. Astro check/build passed with zero diagnostics. This includes 58 new history tests. The prior code commit `03d70cc` also passed full run `36484859597`. Final review was author self-review, not independent approval. The feature stays in draft PR #1, unmerged and undeployed. Detailed limitations, operational commands and the next staging-only orchestration task are recorded in `PROJECT_STATUS.md`.
