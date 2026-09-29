# Project status and handoff

Updated: 2026-09-28 America/Toronto; verification completed 2026-09-29 UTC.
**The selected entry-source review gate and visitor warnings are implemented and CI-verified. Automatic source monitoring and the public pilot release remain incomplete.**

Repository: `Vasuki8/us-national-park-trip-readiness-tracker`.
Branch: `feat/pilot-foundation`.
Draft PR: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/1
Main remains `a9d9c19e8307828c5bdb6f331e24ca3fe7afffce`. No merge or production deployment was performed.

## Standing direction and preserved capabilities

The eventual public product is AdSense-first, uses a light theme and has no paid data dependency. Validate five parks before expanding to 20. Trustworthy displayed data precedes indexing and advertising. Never infer an all-clear, reopening, permit exemption or annual validity from missing information.

The production build remains 14 HTML pages plus build.json: park/state search, five park pages, source evidence, self-reported checklists, notice history and seven official planning checks per park. All five parks have entry evidence; only Yosemite and Rocky Mountain have dated rules. The other three have undated observations, not executable annual rules. The 35 planning destinations are links only, not current-conditions checks. Source, approval, effective, collection, build and publication clocks stay distinct.

Existing collector, private immutable archive, staging/recovery, visitor history, isolated previews, planning links and accessibility repairs are preserved. Contracts and limitations remain in `docs/EVIDENCE_HISTORY.md`, `docs/STAGING_COLLECTION.md`, `docs/VISITOR_HISTORY.md`, `docs/PREVIEW_BUNDLES.md` and `docs/ACCESSIBILITY_REVIEW.md`. No replacement alert pipeline was built.

Original `data/rules.json`, `data/entry-notes.json`, planning resources, alert snapshots and history data are unchanged. All alerts remain `never_checked`; public histories remain empty. The new proposal register is empty and introduces no claimed real source observations. Source review dates were not refreshed.

## New: selected entry-source review gate

`scripts/entry-review.ts` provides pure `assessEntrySources`, `validateEntryReview`, `applyEntryReview` and `guidanceDigest` functions. They accept complete operator-supplied plain-text observation batches against the original approved records. The current inventory is six bindings: three dated rules and three undated notes. This is not a scraper, HTML selector, full-page semantic comparison, persistent collector or automatic approval service.

Changed selected text, a missing selected excerpt and a failed check create pending proposals. Exact before/after evidence and source-check timestamps are retained in the register. Only whitespace-equivalent supplied text is treated as matching; dates, times, punctuation, case, negation and added text are not ignored. A matching check never renews an approval or clears an earlier hold. Original conflicts remain conflicts. Undated records do not acquire effective dates or executable requirements.

A proposal binds the entire original guidance record, not merely its excerpt. Editing approved dates, summary, evidence or approval invalidates an unreconciled proposal. Duplicate pending observations are idempotent; conflicting same-instant or older-than-latest-pending observations fail. Exact field, source URL, timestamp, text and capacity validation rejects invalid input without echoing payloads. Sparse JavaScript arrays cannot masquerade as complete batches.

The server data boundary loads `data/entry-review.json`, validates it, and overlays only `review_status` on defensive copies. Existing entry checking, source coverage and evidence views consume those copies. Pending dated rules return review-required rather than an automatic entry conclusion. The site snapshot identity includes the register, but candidate replacement text is not passed to browser consumers.

`EntryReviewNotice.astro` appears before the park's entry checker when a hold exists. It explains the unresolved reason, links to the official source and distinguishes pending-check timestamps from approval/effective dates. The warning receives only public hold metadata; original approved evidence stays available for historical reference, marked for re-review. An empty register renders no warning and does not mean the source was checked.

Contract and approval boundaries: **`docs/ENTRY_CHANGE_REVIEW.md`**.
Plan: `docs/superpowers/plans/2026-09-28-entry-source-review.md`.

## Verified implementation

Code/test head: **`7d56fc022929c054820456a80bd5f461c15373e5`**.
**Verify pilot #34, run 36517106972, completed successfully.** Job **109241749706** tested temporary PR merge **`726b989178a37da6496524a942c013a60d1260e2`** against unchanged main. A CI test merge is not an actual merge into main.
Run: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36517106972

| Check | Verified result |
|---|---|
| Reproducible npm installation | Passed |
| Node core/data/history/preview/planning/review tests | 130 passed |
| Python collection/archive/staging/projection/preview tests | 158 passed |
| Astro check | 24 files; zero errors, warnings or hints |
| Production build | 14 HTML pages plus build.json |
| Generated-output tests | 18 passed |
| Chromium browser tests | 74 passed |
| **Total automated tests** | **380 passed; 33 added** |

The 25 new Node tests cover exact source/revision binding, changed/missing/failed observations, sticky holds, clocks, idempotency/conflicts, bounds, immutability, sparse batches and evaluator/coverage integration for all six current bindings. The eight browser cases cover changed/missing/failed/sticky warning states, unchanged approval timestamps, pending decision behavior, matching text, no-JavaScript links, 360px/doubled text and unchanged production state. All 66 pre-existing browser cases remain passing.

Populated warning states are synthetic and confined to the existing isolated test site. They use the production gate, evaluator and warning component; they do not establish live extraction compatibility or a complete operator-to-production promotion test. No new screenshot/independent visual or accessibility audit is claimed in this increment.

Artifact `pilot-verification`, ID **11011247228**, contains production output, existing screenshots and lockfile; not private archives or isolated candidate/test-site outputs. Retention: seven days. CI-reported ZIP SHA-256: `02965591be41efd5b5df668a1f94f337928548cf442586bd505988d5a1b6496d`.
Artifact: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36517106972/artifacts/11011247228

The final handoff/plan update is documentation-only and receives a separate CI check recorded in PR #1. These results prove the exact implementation head, not future changes.

## Execution and review record

Direct container GitHub DNS was unavailable. Local verification used an isolated partial workspace, not a full repository clone. The initial 20 pure tests were observed failing against explicit not-implemented exports, then passed locally on Node 22.16.0. Full builds and browser navigation ran in GitHub CI on Node 24/Python 3.12.

Tests and core intake were pushed at `e44a050`. Run #33, **36516442674**, passed 129 Node, 158 Python and 18 static tests plus all 66 existing browser cases and the new production-empty-register check. Exactly seven new browser cases failed on intentionally missing warning/fixture elements before UI implementation. No assertion was removed or weakened.

Author self-review found that array length alone admitted sparse programmatic batches because Array.map skips holes. A new regression failed with Missing expected exception; the explicit processed-inventory count then passed all 21 local pure tests. UI/gate wiring and this fix at `7d56fc0` passed all 380 tests in #34. The 13-file increment comparison preserves approved data, existing provider/history/staging/preview implementations, dependencies and workflow files; Playwright's test inventory was extended.

Review was author self-review, not independent approval. Existing Actions runtime and npm install-script warnings remain maintenance items. Prior manual accessibility limitations—screen readers, actual browser/OS zoom, other browsers, native popup controls and forced colors—still apply.

## Source-review limits and live-release gates

A matching excerpt cannot detect new contradictory or qualifying content elsewhere on its page. Existing approved excerpts are not full-page baselines. Source adapters must explicitly establish selected scope and surrounding context before automated page-change coverage can be claimed.

This slice has no network fetch, protected file reader/writer, approve/resolve command or automatic register persistence. The register contains unresolved proposals, not a durable all-check history; matching checks are returned as metadata only. Trusted repository changes must record reviewer disposition and preserve earlier proposal evidence, not simply delete holds. Hashes check consistency, not authority, factual correctness or redistribution permission. Real proposal text committed to a public repository is public even when not displayed on the site.

No NPS request or API-key configuration recheck occurred. The latest observed preflight remains run 36481482091, job 109224608968, at `2026-09-29T02:13:16Z`: empty `NPS_API_KEY`, `not_configured`, `gate_passed:false`, no requests. That used original preflight code `0dce38beb7c1d9bc3d7feba0d8a69ca1f97ddca7`, not the newest collector. It does not establish current secret settings. Owner setup remains in `docs/NPS_PREFLIGHT.md`.

Live compatibility, reviewed response fixtures, durable operator storage, source-content rights, production hosting and publication/rollback remain release requirements. No live public feed, recurring collection, deployment, advertising, tracking, accounts, indexing, spending or provider agreement was activated. Neither M1 nor M2 is declared complete.

## Next coherent task

Read current PR/head/CI before editing; preserve newer work. The review gate and warning now exist—do not rebuild them, the alert collector, archive, staging, history, preview system or planning links.

Next implement **source-specific observation extraction with explicit scope**, starting from reviewed fixtures for the existing official entry pages. Distinguish matching selected text from complete-page coverage; additions to surrounding exceptions, missing/duplicate selectors or ambiguous extraction must require review. Retain source identity and original observation clocks and feed the existing proposal API without renewing approvals. Do not manufacture a full-page baseline from a short stored excerpt. Keep any network collection opt-in and separate from approval/publication.

A subsequent protected operator I/O/resolution slice must persist/reconcile pending evidence, prevent stale writes and retain reviewer disposition. Do not claim such persistence from the current pure API. Once an owner-controlled NPS key is available, use the existing read-only preflight/staging/preview path for actual alert compatibility rather than another pipeline. Do not repeatedly rerun an unchanged empty-key diagnostic as feature progress.

Before scheduling or launch, resolve persistent archive storage, hosting, source-use and publication/rollback requirements. Ephemeral Actions workspaces and preview folders are not durable hosted archives. Do not expand to 20 parks or activate ads before pilot acceptance.

## Verification lineage

Prior passing totals: foundation 79; source coverage 109; private history 167; staging 206; visitor history 246; private preview 293; planning checks 309; accessibility 347 at `a0eda54` / run 36514758211 and handoff `00bd01b` / run 36515271031. Current 380-test evidence is above. PR #1 remains draft and unmerged.
