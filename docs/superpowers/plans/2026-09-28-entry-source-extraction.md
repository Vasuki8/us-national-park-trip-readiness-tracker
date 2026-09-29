# Entry-source context extraction implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline, with failing tests before implementation.

**Goal:** Turn bounded supplied official-page HTML into explicit-scope source observations for the existing entry-review gate, without approving guidance or claiming live monitoring.
**Architecture:** A Python standard-library parser extracts HTML body text (including collapsed/hidden text), the expected source-page heading, and link targets. A pure six-binding batch adapter compares this with a separately reviewed context baseline. It feeds the existing TypeScript proposal API through observed/missing/failed statuses; private evidence preserves context changes, absent baseline, ambiguous headings/excerpts and parser failures. No replacement collector or approval service.
**Tech stack:** Existing Python/uv and TypeScript/Node tests. No dependency additions.
**Spec:** docs/superpowers/specs/2026-09-28-national-park-trip-readiness-design.md sections 8–9; PROJECT_STATUS.md next-task contract; docs/ENTRY_CHANGE_REVIEW.md.

## Global constraints

Preserve all approved guidance, public data, proposal register, source clocks and browser interfaces. No network in the extraction API, persistence, scheduler, deployment, indexing or ads. No automatic context approval or fresh guidance approval from matching text. Short-excerpt approval and heading review are not context-baseline approval. Failures remain unresolved, never exemptions.

## Review focus

- Unchanged excerpt with a changed surrounding exception must not pass.
- Missing/duplicate body, heading or excerpt must fail closed, not take the first match.
- Changed guidance revision, old/future clock, redirected source or incomplete inventory must refuse.
- Script/comment copies cannot establish evidence; hidden FAQ text and link-target edits affect context.
- Oversized/truncated input cannot silently lose text; preserve inputs and exclude private evidence from visitor payloads.

## Tasks

- [x] Add Python tests for bounded HTML extraction, five profiles, reviewed context baselines and explicit failures; run initial missing-module check.
- [x] Implement the pure parser and complete-batch adapter; pass the initial 28 local tests.
- [x] Add regressions for base-URL retargeting and deletion markup. Observe both failing behavior assertions, repair them and pass all 30 Python tests.
- [x] Add six cross-language integration cases using all six real stored guidance bindings and the existing assessEntrySources/applyEntryReview/evaluateEntry functions.
- [x] Run complete CI, review the exact committed diff, document verified results and prepare the PROJECT_STATUS.md/PR handoff. Keep the existing draft PR unmerged.

## Decisions and execution

Resumed feature branch e1f89e0 on PR #1 for the previously presented source-extraction task. Local workspace is a fresh isolated partial copy because container GitHub/NPS DNS is unavailable. Connected GitHub supplies repository changes and full CI. Review is author self-review; no independent reviewer agent is available.

Public pages were read through web retrieval for exact titles and source-family scope, not raw HTML or complete DOM verification. Synthetic HTML is labeled accordingly. No real context baseline is fabricated from parsed web output.

Ruling: compare the supplied body text and link targets rather than a narrow heading interval. Global/footer noise may create extra review, but newly added exceptions outside the old sentence are retained. This is not full browser/dynamic/media coverage. Strict balancing and rejection of base/deletion/insertion/strike markup are conservative, documented limits.

Ruling: context failures feed the existing failed-check status, while precise reasons and before/after context remain in the private extraction result. This avoids fabricating a changed quote or creating another pending-state mechanism. Protected persistence must retain that evidence alongside the proposal register.

Local verification: 30 Python tests and compileall passed on Python 3.13. The first attempt failed because the module did not exist, not because every behavior assertion ran. Two later self-review regressions did fail observed-versus-failed assertions before repair. No tests were removed or weakened.

**Full CI passed:** Verify pilot #36, run `36519854445`, head `9a32976ef57189528ed7cd6b55b374376bab8194`, job `109250112261`, temporary PR merge `55ac96d9019548e7cca1691f874030f250dfef73`. Complete logs read: 136 Node + 188 Python + 18 generated-output + 74 Chromium = **416 passing tests**, 36 added. Astro checked 24 files with zero errors/warnings/hints; production remains 14 HTML pages plus build.json. All existing browser cases pass. Artifact 11012780424; CI-reported ZIP SHA-256 `c957a98974a38816ffa9bfbc3218c42d1d05844a8ea7a91a85d2e53a11b1a47e`, not independently downloaded in this increment.

The seven-file implementation diff adds only parser/adapter, tests and docs. Original data, source clocks, gate, UI, dependencies and workflows are unchanged. Final documentation-only handoff CI is checked separately in PR #1. No live extraction compatibility, approved context baseline, persistent operator state, scheduling or publication is claimed.

Next task: protected offline operator persistence and explicit review disposition, preserving the extraction result with proposals and rejecting stale writes. Real captured HTML/context-baseline review is still required before live monitoring.
