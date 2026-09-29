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
5. Candidate source text remains outside generated public HTML/JavaScript; public warning uses metadata only.

## Tasks

- [x] Write failing unit contracts for comparison, strict input, chronology, replay, idempotency, sticky holds and data immutability.
- [x] Implement intake/validation/gating as pure functions; run tests.
- [ ] Add an empty production register, wire it into server data and add a source-review notice with minimal safe metadata.
- [ ] Verify existing evaluator/coverage behavior with held rules and notes; add isolated browser fixtures for warnings and escaping/exclusion.
- [ ] Run full CI; self-review the diff; update PROJECT_STATUS.md and PR #1.

## Execution ledger

Base: 00bd01b8d320a9776ac4b4374ebe3c35802d3cb0; feature branch remains feat/pilot-foundation. Main unchanged. Direct container GitHub DNS failed; use isolated partial local files and full GitHub CI, not an invented full clone. No independent reviewer tool is available.
Ruling: implement selected-text intake and a build-consumed review register first. Source adapters and protected operator persistence require a later slice; no automatic webpage-change coverage is claimed. This keeps approval explicit and avoids inventing full-page baselines from existing short excerpts.

The 20 pure Node contracts were observed failing against explicit not-implemented exports, then all20passed locally on Node22.16.0. Added four integration contracts against actual stored record shapes and eight browser cases; a deliberately unimplemented test fixture page establishes browser RED before the warning component is written. The complete repository is verified in CI; no local full-build claim.
