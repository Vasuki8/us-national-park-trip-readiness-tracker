# Visitor-facing history implementation plan

> **For agentic workers:** Use superpowers:executing-plans task-by-task, with failing tests before implementation.

**Goal:** Render verified committed notice observations without confusing observation history with real-world conditions.
**Architecture:** A read-only Python projection returns the current snapshot and a bounded history together from one verified archive read. Strict TypeScript build validation binds that history to the snapshot. A shared static Astro timeline serves park pages and /changes/. Only empty production histories are committed; synthetic populated examples live in an isolated test site.
**Tech stack:** Existing Python/uv, TypeScript, Astro, Node tests and Playwright; no new dependencies.
**Spec:** docs/superpowers/specs/2026-09-28-national-park-trip-readiness-design.md (sections 5, 7–9 and 12); latest PROJECT_STATUS.md next-task contract.

## Global constraints

No network request, publication, scheduler, new storage service, advertising or indexing in this increment. Preserve collector/archive/staging schemas, all source-review clocks and current public alert snapshots. No inference that disappearance means reopening. Failures remain degraded even with recent last-good data. Baselines are not new closure events. Provider text is escaped, not interpreted as HTML.

## Review focus

- Current snapshot and history from different observations must fail validation.
- Failed/quarantined observations must not conceal earlier successful evidence or generate removals.
- Corrupt archives, unknown fields and altered evidence must fail closed.
- Truncated histories must disclose omitted observations/events; no silent loss or unbounded output.
- Synthetic fixtures, pending receipts, local paths and provider credentials must stay outside production data.

## Task 1 — bounded projection and cross-language fixtures

Files: tracker/history_projection.py; tests/test_history_projection.py; tests/fixtures/history-preview.json.
Interface: project_history(store: HistoryStore, code: str, *, limit: int = 20) -> dict with snapshot + history. The history includes head ID, canonical snapshot hash, total/omitted observation and change counts, and newest-first observations with source-linked before/after evidence. Maximum 20 observations, 100 changes per observation, 2 MiB history JSON. Empty archive projects an explicit never-checked snapshot. No writes, clocks or raw HTTP data.
- [x] Write and run tests for empty/baseline, changes, failures, read-only/corrupt archive, bounded windows and same-head binding.
- [x] Implement projection from one HistoryStore.read call and run Python tests.
- [x] Generate a clearly synthetic fixture through the real store/projector and test its reproducibility.

## Task 2 — validate and present history

Files: src/lib/history.ts; scripts/validate-history.ts; tests/history.test.ts; data/history.json.
Interface: validateHistory(value: unknown, snapshot: unknown) -> History; describeHistory(metadata, now) -> {title, detail}. Canonical digest is UTF-8 sorted-key JSON, identical to Python for this fixed string/integer schema.
- [x] Write failing validator/presentation tests for shape/hash/clock/status/event and truncation contracts.
- [x] Implement runtime/build validation, explicit empty/failed/stale labels and conservative copy.
- [x] Commit five empty history projections matching untouched public snapshots.

## Task 3 — shared timeline and browser proof

Files: src/components/HistoryTimeline.astro; src/scripts/history.ts; src/lib/data.ts; src/pages/[page].astro; src/pages/parks/[slug].astro; src/lib/content.ts; tests/history.browser.spec.ts; tests/history-site/; playwright.config.ts.
- [x] Add failing browser contracts for empty production pages and isolated synthetic populated histories.
- [x] Render original source text as escaped text, before/after details and absolute observation times; retain useful no-JavaScript fallback. Recompute freshness every minute and on return to the page.
- [x] Verify source links, failure/empty/truncation copy, mobile overflow and non-execution of markup; ensure fixtures are not part of production output.
- [x] Run the full existing CI, review diff, document limitations and prepare PROJECT_STATUS.md/PR handoff. No merge or deployment.

## Execution record

Resumed the owner-approved visitor-history task from 9ab1047 on the existing feature branch. Direct container GitHub DNS was unavailable; local work used an isolated partial workspace with hash-checked dependencies and full repository verification in CI. Review is author self-review, not independent approval. No additional owner setup was required for synthetic development.

The local Python projection suite has 15 tests, including fixture reproducibility. The original 14 TypeScript tests passed; review added three initially failing timestamp regressions (relabeling a retained success, inventing success within a failed window, and year-zero acceptance), fixed before the local 17-test pass.

CI #14 (36506775182) passed 64 Node, 143 Python and 18 generated-output tests but did not run browser assertions because the isolated Astro config supplied URL objects instead of string paths. Fixed using fileURLToPath. CI #15 (36507235090, f190c2f) then ran all 17 browser tests: the ten existing cases passed, and exactly seven timeline assertions failed on missing elements before implementation.

CI #16 (36507885402, 77533db) passed 67 Node,143 Python,18 generated-output checks and17 of18 browser cases. The remaining no-JavaScript assertion used ancestor text matching, which Playwright deliberately excludes NOSCRIPT content from. The corrected assertion targets the actual noscript paragraph and requires both visible rendering and expected text. Product markup was unchanged; no intended contract was relaxed.

**Full GREEN: CI #17, run36508305834, head70322a54c28d2942f89b442bf7fe888122d8438b, job109214628545.** Temporary PR merge59d9ae671923bea27793db4c15ecb2701dba0327. 67Node+143Python+18static+18Chromium=246passing tests. Astro21files clean, production14pages plusbuild.json. Artifact11008196173. Complete logs read. Documentation-only follow-up requires its own CI check.

Ruling: projection is read-only; no export/publication CLI before live-source/content review. Visitor hashes check consistency, not signatures or full archive proofs. Limits remain explicit in docs/VISITOR_HISTORY.md. Production histories remain empty. Existing source reviews, alert snapshots, collector/archive/staging code, dependencies and workflows were preserved.

Next work is staging-only preview-bundle preparation and validation, not another timeline implementation or a production promotion. See PROJECT_STATUS.md for current evidence and release gates.
