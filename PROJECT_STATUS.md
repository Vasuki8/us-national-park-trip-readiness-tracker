# Project status and handoff

Updated: 2026-09-28 America/Toronto (verification completed 2026-09-29 UTC). **Visitor-facing history is implemented and CI-verified; the public pilot release remains incomplete.**

Repository: `Vasuki8/us-national-park-trip-readiness-tracker`.
Branch: `feat/pilot-foundation`. Draft PR: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/1
Main remains `a9d9c19e8307828c5bdb6f331e24ca3fe7afffce`. No merge or deployment was performed.

## Standing direction and preserved capabilities

AdSense-first eventual public product, light theme, no paid data dependency. Validate five parks before expanding to 20. Trustworthy displayed data precedes indexing and advertising. No all-clear, safety score, reopening inference, guessed exemption or annual extrapolation.

The Astro site still has 14 HTML pages plus build.json, a searchable directory, five park pages, source evidence and a self-reported checklist. All five parks have entry-source evidence; only Yosemite and Rocky Mountain have dated rules. Yellowstone, Zion and Grand Canyon have separate undated observations. Human review, source, effective, collection, build and publication clocks remain distinct.

Existing collector, immutable private evidence archive, semantic differ, offline record/report commands and staging receipt/recovery path are preserved. Staging uses expected-parent archive checks and records successful, failed and quarantined attempts without public writes. Its trusted-local-filesystem and recovery limits remain as documented in `docs/EVIDENCE_HISTORY.md` and `docs/STAGING_COLLECTION.md`.

## New: visitor-facing notice history

- `tracker/history_projection.py`: read-only `project_history(store, code, limit=20)` returns the current snapshot and its history together from one verified committed-chain read. It excludes pending receipts and private archive internals. Before/after source text is reconstructable, not just a hash.
- Projection bounds: at most 20 observations and 100 displayed changes per observation; maximum 2 MiB history payload. Total and omitted check/change counts are explicit. Oversized history is refused, not silently truncated. The archive itself is not pruned.
- `scripts/validate-history.ts`: strict server/build validation checks exact fields, park-specific official URLs, evidence hashes, snapshot binding, chronology, baseline/failure semantics and omitted counts. Visible complete changes are checked against current notice hashes. Last-success times cannot be relabeled or invented within a failed window. Invalid data fails the Astro build.
- `src/components/HistoryTimeline.astro`: shared timeline on all five park pages and `/changes/`, with park jump links on the latter. First observations are baselines, not newly started closures. Added/edited/no-longer-present notices have expandable before/after evidence and official links. Notice removal is explicitly not a confirmed reopening.
- Failed checks retain earlier accepted evidence; empty timelines do not imply no changes. Freshness recalculates every minute and when returning to the page without changing evidence timestamps. Absolute times and the no-JavaScript warning remain in static HTML. Source markup is escaped, not executed.
- `data/history.json`: five empty histories bound to the unchanged `never_checked` public alert snapshots. Site snapshot hashing now includes history. No real NPS alert text, private archive or pending receipt was committed.
- Synthetic fixtures are reproducibly generated with the real archive/projector and checked by TypeScript. A separate Astro test site uses the production component, but its routes and assets never enter the production build. Browser verification checks that exclusion.

Contract, limits and publication boundaries: `docs/VISITOR_HISTORY.md`.
Plan: `docs/superpowers/plans/2026-09-28-visitor-history.md`.

## Verified implementation

Code/test head: **`70322a54c28d2942f89b442bf7fe888122d8438b`**. Application code is the same as `77533db`; the follow-up corrects the no-JavaScript test selector and requires explicit paragraph visibility.

**Verify pilot #17, run 36508305834, completed successfully.** Job **109214628545** tested temporary PR merge **`59d9ae671923bea27793db4c15ecb2701dba0327`** against unchanged main. A temporary test merge is not an actual merge into main.
Run: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36508305834

| Check | Verified result |
|---|---|
| Reproducible npm installation | Passed |
| Node core/data/history/coverage tests | 67 passed |
| Python collector/archive/staging/projection tests | 143 passed |
| Astro check | 21 files; 0 errors, 0 warnings, 0 hints |
| Production static build | 14 HTML pages plus build.json |
| Generated-output tests | 18 passed |
| Chromium browser tests | 18 passed |
| **Total** | **246 passed; 40 new tests in this increment** |

The eight new browser cases cover production empty-history states, populated synthetic baseline/change/evidence rendering, escaped markup, failed-check context, open-page freshness expiration, omitted history, no-JavaScript evidence and visible fallback copy, 360px layouts with expanded evidence, and exclusion of test/private content from production assets. Existing date, search, checklist, mobile and no-JavaScript cases remain passing.

Artifact `pilot-verification`, ID **11008196173**, contains the production build, existing browser screenshots and lockfile; not private archives or the synthetic test-site build. Seven-day retention. ZIP SHA-256: `8582e49185752f9949658c09c9f45947330fad2b86522b1ff2c444755a0a5b60`.
Artifact: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36508305834/artifacts/11008196173

This handoff/plan update changes documentation only. Its CI is verified separately; the result above proves the exact code/test head, not future changes.

## Execution and review record

Local verification used an isolated partial workspace with Git-blob-verified existing dependencies, not a full clone: direct container GitHub DNS was unavailable. The 15 projection/fixture tests and 17 new Node tests passed locally; GitHub CI ran the complete repository on Node 24/Python 3.12.

Tests preceded implementation. CI #14 exposed an isolated test-site configuration issue (URL objects instead of string paths); it did not establish browser RED. After correction, #15 ran the ten existing browser tests successfully and failed exactly seven missing timeline contracts before component implementation. Author review reproduced and repaired three timestamp-validation gaps. Run #16 passed all data/build tests and 17 browser cases; its sole failure used ancestor text matching for a noscript message. Playwright deliberately skips NOSCRIPT in aggregated text, so the corrected test directly checks the fallback paragraph for both visibility and text. #17 then passed all 246 tests. No test was removed or its intended behavior relaxed.

Review was author self-review, not independent approval. No independent visual/accessibility or field-conditions audit is claimed. The 20-file implementation comparison preserved public alert records, all source reviews, existing collector/archive/staging code, dependencies and workflows. Existing Actions Node-runtime and npm install-script warnings remain maintenance items.

## Live NPS and publication gates

No NPS API request or key-configuration recheck was performed in this increment. The last observed preflight remains run **36481482091**, at **2026-09-28T20:45:52Z**, which received an empty `NPS_API_KEY`, made no requests and reported `gate_passed: false`. That historical result does not establish the current secret configuration.

Once an owner-controlled private Actions secret is available, rerun the existing read-only preflight and inspect actual provider shapes privately. Never put keys in chat, URLs, source code or issues. Configuration remains in `docs/NPS_PREFLIGHT.md`.

Production alert snapshots remain `never_checked`; production history remains empty. There is no automatic export/promotion CLI, live public feed, scheduler, deployment, advertising, tracking, accounts, indexing, spending or provider-agreement acceptance. Private archival and a valid hash do not confer source-content redistribution approval.

## Next coherent task

Read the current PR/head/CI first and preserve newer changes. The visitor projector, validator, timeline, evidence panels and isolated browser fixture site now exist; do not rebuild them.

Next develop a staging-only preview bundle that keeps candidate current snapshots and histories together, validates the pair, and builds an isolated preview without overwriting committed production data. Test mismatched pairs, failed/quarantined attempts, interrupted preparation and exclusion of pending/private state. Keep candidate preparation separate from approval and deployment; no production promotion before live-source and content-use gates pass.

Before scheduling: provide operator-controlled persistent archive storage, validate private live-source compatibility and retain reviewed credential-free fixtures. Ephemeral Actions checkouts are not durable private archives. Automatic editorial source-change review, complete permit/road/facility coverage, source-content rights, hosting and publication/rollback validation remain release gates.

## Limits and verification lineage

Visitor digests are consistency checks, not signatures or an independently verifiable copy of the entire archive chain. Truncated views cannot prove omitted events; full verification remains in the trusted archive read. Archive/staging durability is limited to tested trusted local Linux cases: no hardware power-loss, Windows-directory, network-filesystem, hostile same-user writer or off-host backup/restore guarantees. A response lost before receipt persistence cannot be recovered. No automatic pruning, lock stealing or bulk-removal override exists.

Prior full passes: foundation 79 tests; source coverage 109; private history 167; staging 206 at `afdf98f` / run 36487323692 and handoff `9ab1047` / run 36487875643. Visitor-history verification is recorded above. PR #1 remains draft and unmerged; passing synthetic tests does not establish live-condition or public-release readiness.
