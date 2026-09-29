# Entry-source context extraction implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline, with failing tests before implementation.

**Goal:** Turn bounded supplied official-page HTML into explicit-scope source observations for the existing entry-review gate, without approving guidance or claiming live monitoring.
**Architecture:** A Python standard-library parser extracts HTML body text (including collapsed/hidden body text), the expected source-page heading, and link targets. A pure six-binding batch adapter compares that context with a separately reviewed complete context baseline. It feeds the existing TypeScript proposal API using its existing observed/missing/failed statuses; private extraction evidence distinguishes context changes, missing baseline, ambiguous heading/excerpt and parser failure. There is no replacement collector or approval service.
**Tech stack:** Existing Python/uv, TypeScript/Node tests. No dependency additions.
**Spec:** docs/superpowers/specs/2026-09-28-national-park-trip-readiness-design.md sections 8–9; PROJECT_STATUS.md next-task contract; docs/ENTRY_CHANGE_REVIEW.md.

## Global constraints

Preserve every approved guidance record, public snapshot/history, proposal register, source timestamp and browser interface. No network in the extraction API, no persistence or scheduler, no deployment, no indexing/advertising. No automatic baseline creation or fresh approval from matching text. Only an explicitly reviewed context baseline can establish a context comparison; source heading review is not baseline approval. Failures remain unresolved, never exemptions.

## Review focus

- Unchanged excerpt with changed/new surrounding exception must not pass.
- Missing/duplicate body, expected heading or excerpt must fail closed, not use the first match.
- Changed guidance revision, old/future input clock, redirected source or incomplete inventory must refuse.
- Script/comment copies of a quote cannot establish evidence; collapsed FAQ text and link-target edits must affect context.
- Oversize/truncated/malformed input cannot silently lose text; input mutation and output/private-state leakage must be tested.

## Tasks

- [x] Add Python tests for bounded HTML extraction, five source profiles, reviewed context baselines, explicit failures and source identity; run initial missing-module check.
- [x] Implement a pure parser and complete-batch adapter, then pass 28 local tests.
- [x] During self-review, add two regressions for base-URL retargeting and deletion markup. Observe both failing assertions (observed instead of failed), then repair and pass all 30 Python tests.
- [x] Add six cross-language integration tests using all six real stored guidance bindings and the existing assessEntrySources/applyEntryReview/evaluateEntry functions.
- [ ] Run complete GitHub CI, review exact committed diff, document verification and update PROJECT_STATUS.md/PR #1. No merge.

## Decisions and execution

Resuming feature branch e1f89e0 on PR #1. User's continue authorizes the scoped source-extraction next step already presented. Local workspace is a fresh isolated partial copy because container GitHub/NPS DNS is unavailable; connected GitHub is used for repository changes and full CI. No independent reviewer agent is available; review is author self-review.

Public NPS pages were read through web retrieval for exact page titles and source-family structure, not for raw HTML or complete DOM verification. Synthetic HTML fixtures are labeled as synthetic. No live compatibility claim or real context baseline is fabricated from parsed web output.

Ruling: capture the entire supplied body text and link targets, rather than a narrow phrase/heading interval. This intentionally includes global/footer noise and can create conservative extra review; it avoids silently dropping newly added exceptions outside the old excerpt. Script/style text is excluded and never executed. This is not browser-rendered, full-page/dynamic/media coverage. Strict balancing and rejection of base/deletion/insertion/strike markup are explicit conservative limits.

Ruling: context verification failures map to the existing gate's failed-check status, with exact private reason/context retained in extraction evidence. This avoids manufacturing a changed quote or adding an alternate pending-state mechanism. Persisting extraction evidence alongside proposals belongs to the subsequent protected operator I/O task.

Local verification: 30 Python tests passed on Python 3.13.5; compileall passed. The initial test attempt failed because the extractor module did not yet exist; it was not a full set of behavior assertions. The two subsequent self-review regressions did fail behavior assertions before their repairs. Full cross-language/build/browser validation remains pending in CI for this commit.
