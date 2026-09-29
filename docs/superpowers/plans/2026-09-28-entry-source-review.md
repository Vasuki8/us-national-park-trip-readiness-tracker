# Entry-source review gate implementation plan

> **For agentic workers:** Use superpowers:executing-plans, with tests before implementation.

**Goal:** Turn changed, missing or failed selected entry-source observations into reviewable holds without replacing approved evidence or renewing its approval.
**Architecture:** A pure, bounded TypeScript intake compares operator-supplied plain-text observations to the exact approved guidance revision. Pending proposals are separate from rules/notes. The server data boundary validates the register and overlays only review_status; existing date, coverage and evidence paths consume that gated data.
**Tech stack:** Existing TypeScript/Node, Astro and Playwright. No new dependency.
**Spec:** docs/superpowers/specs/2026-09-28-national-park-trip-readiness-design.md, sections 8–9; PROJECT_STATUS.md next-task contract at 00bd01b.

## Scope and constraints

This is the next bounded slice of the approved source-review behavior, not an alternate collector. Intake operates on already-supplied, complete six-record observation batches, not HTML/network requests. Only whitespace differences are non-substantive. Equality is confined to supplied selected text and cannot prove a complete page unchanged. Missing/failed checks conservatively suspend conclusions. Later matching text cannot resolve earlier pending proposals. No automatic approval, silent timestamp refresh, source scraping, publication or scheduler. Keep all approved source data, alert history and entry semantics intact. The production register starts empty and must not imply monitoring is active.

## Review focus

1. Full approved-record fingerprint prevents replay against a changed summary, date or approval.
2. Missing, failed, changed and conflicting states cannot grant exemptions or improve coverage.
3. Later matching observations and exact retries do not clear unresolved proposals.
4. Invalid clocks, unsafe/cross-source URLs, duplicates and unknown fields fail closed without echoing payloads.
5. Candidate source text stays out of visitor warning payloads; public warning uses metadata only. A public repository is not private storage.

## Tasks

- [x] Write failing unit contracts for comparison, strict input, chronology, replay, idempotency, sticky holds and data immutability.
- [x] Implement intake/validation/gating as pure functions; run tests.
- [x] Add an empty production register, wire it into server data and add a source-review notice with minimal safe metadata.
- [x] Verify existing evaluator/coverage behavior with held rules and notes; add isolated browser fixtures for warnings and candidate-text exclusion.
- [x] Run full CI; self-review the diff; prepare PROJECT_STATUS.md and PR #1 handoff. Documentation-only final commit receives a separate CI check.

## Execution ledger

Base: 00bd01b8d320a9776ac4b4374ebe3c35802d3cb0; feature branch remains feat/pilot-foundation. Main unchanged. Direct container GitHub DNS failed; used isolated partial local files and full GitHub CI, not a full clone. No independent reviewer tool was available; review is author self-review.

Ruling: implement selected-text intake and a build-consumed review register first. Source adapters and protected operator persistence require later slices; no automatic webpage-change coverage is claimed. This keeps approval explicit and avoids inventing full-page baselines from existing short excerpts.

The 20 pure Node contracts were observed failing against explicit not-implemented exports, then all 20 passed locally on Node 22.16.0. Added four integration contracts against actual stored record shapes and eight browser cases. The deliberately unimplemented isolated fixture established browser RED before the warning component was written.

**RED CI #33, run 36516442674, head e44a0504834f4f9d4f0bf4087148bdc4c5efeda9.** Job 109239670786, temporary merge 8399078b132b758a5578cfd6ac2c365d33234162. 129 Node, 158 Python, 18 static tests passed. All 66 existing browser tests and the new empty-production-register case passed. Exactly seven new fixture/warning cases failed on absent elements. No assertion was removed or weakened.

Author review identified sparse JavaScript arrays bypassing the complete-batch promise because Array.map skips holes. The new regression reproduced Missing expected exception, then passed after requiring processed binding count to equal inventory size. All 21 pure tests passed locally. This is a programmatic input boundary repair, not a change to approval semantics.

**GREEN CI #34, run 36517106972, head 7d56fc022929c054820456a80bd5f461c15373e5.** Job 109241749706, temporary merge 726b989178a37da6496524a942c013a60d1260e2. **130 Node + 158 Python + 18 static + 74 Chromium = 380 passing tests, 33 added.** Astro: 24 files, zero errors/warnings/hints. Production: 14 HTML pages plus build.json. Complete logs read. Artifact 11011247228, CI-reported ZIP SHA-256 02965591be41efd5b5df668a1f94f337928548cf442586bd505988d5a1b6496d. No new independent visual audit or live-source compatibility is claimed.

The 13-file implementation comparison preserves existing rules/notes, planning register, alerts/history, provider/archive/staging/preview code, dependencies and workflow files. Public proposals remain empty. No live request, key check, source approval, scheduler, publication or merge was performed.

Next task is explicit-scope source observation extraction, not rebuilding the review gate. Later protected operator persistence/resolution must retain evidence and reviewer disposition. See docs/ENTRY_CHANGE_REVIEW.md and PROJECT_STATUS.md for exact boundaries and release requirements.
