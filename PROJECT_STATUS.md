# Project status and handoff

Verification completed: 2026-09-29 UTC.
**Explicit-scope entry-source HTML extraction is implemented and CI-verified. Real HTML compatibility, automatic monitoring and the public pilot release remain unverified or unfinished.**

Repository: `Vasuki8/us-national-park-trip-readiness-tracker`.
Branch: `feat/pilot-foundation`.
Draft PR: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/1
Main remains `a9d9c19e8307828c5bdb6f331e24ca3fe7afffce`. No merge or production deployment was performed.

## Standing direction and preserved capabilities

The eventual public product is AdSense-first, uses a light theme and has no paid data dependency. Validate five parks before expanding to 20. Trustworthy displayed data precedes indexing and advertising. Never infer an all-clear, reopening, permit exemption or annual validity from missing information.

The production build remains 14 HTML pages plus build.json: park/state search, five park pages, source evidence, self-reported checklists, notice history and seven official planning checks per park. All five parks have entry evidence; only Yosemite and Rocky Mountain have dated rules. The other three have undated observations, not executable annual rules. The 35 planning destinations are links only, not current-conditions checks. Source, approval, effective, collection, build and publication clocks remain distinct.

Existing collector, private immutable archive, staging/recovery, visitor history, isolated previews, planning links, accessibility repairs and selected-excerpt review gate are preserved. Contracts remain in `docs/EVIDENCE_HISTORY.md`, `docs/STAGING_COLLECTION.md`, `docs/VISITOR_HISTORY.md`, `docs/PREVIEW_BUNDLES.md`, `docs/ACCESSIBILITY_REVIEW.md` and `docs/ENTRY_CHANGE_REVIEW.md`. No replacement pipeline was built.

This increment changes no existing application, data, dependency or workflow file. It adds an extraction adapter, tests and documentation. Original guidance, approval timestamps, planning resources, public alert snapshots, histories and entry-review register are unchanged. All public alerts remain `never_checked`; histories and pending proposals remain empty. No real context baseline or source-change proposal was added.

## New: scoped source-page extraction

`tracker/entry_html.py` implements bounded, non-rendering HTML inspection. It retains normalized body text and block boundaries, body H1 text and anchor targets. Body navigation, footers and collapsed/hidden FAQ text are included deliberately. A changed surrounding exception or link target cannot pass merely because the approved sentence is still present. Script/style content and comments cannot establish evidence. Base elements and deletion/insertion/strike annotations require review.

`tracker/entry_sources.py` implements pure `inspect_entry_sources(records, captures, baselines, now)`. Five exact URL/heading profiles cover the six current guidance bindings. It consumes a complete batch of supplied HTML captures, verifies source identity, original observation clocks and full guidance revision hashes, and compares extracted context against separately reviewed context baselines. It does not fetch, persist, approve, resolve proposals or publish.

An approved short excerpt does not become a context baseline. A missing baseline, changed context, ambiguous/missing heading or excerpt, failed capture, or parser refusal cannot produce a matching observation. Changed guidance revisions, invalid clocks, source redirects and incomplete inventories refuse rather than borrowing an unrelated source or approval.

The result separates `observations`, which use the existing six-field TypeScript intake contract, from private `sources` evidence containing the precise reason, source/profile identity, current and baseline contexts, hashes and original check/review times. Context-verification failures map conservatively to the existing gate's failed-check status; operators must consult the private reason rather than interpret every failure as an HTTP error. Missing excerpts use the existing missing status. Matching context still cannot renew guidance approval or clear older pending holds.

Limits: 1 MiB supplied HTML per page, 65,536 body-text characters, 30,000 element starts, depth 128, 2,048 links, and 2 MiB returned JSON. No silent truncation. Diagnostics use fixed codes and do not echo source payloads. Returned context is untrusted/private comparison material, not a visitor-safe payload or redistribution clearance.

Contract and limitations: **`docs/ENTRY_SOURCE_EXTRACTION.md`**.
Plan: `docs/superpowers/plans/2026-09-28-entry-source-extraction.md`.

## Verified implementation

Code/test head: **`9a32976ef57189528ed7cd6b55b374376bab8194`**.
**Verify pilot #36, run 36519854445, completed successfully.** Job **109250112261** tested temporary PR merge **`55ac96d9019548e7cca1691f874030f250dfef73`** against unchanged main. This CI test merge is not a merge into main.
Run: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36519854445

| Check | Verified result |
|---|---|
| Reproducible npm installation | Passed |
| Node core/data/history/preview/planning/review/extraction tests | 136 passed |
| Python collection/archive/staging/projection/preview/extraction tests | 188 passed |
| Astro check | 24 files; zero errors, warnings or hints |
| Production build | 14 HTML pages plus build.json |
| Generated-output tests | 18 passed |
| Chromium browser tests | 74 passed |
| **Total automated tests** | **416 passed; 36 added** |

The 30 new Python tests cover extraction, source profiles, context approval boundaries, surrounding/hidden text and changed links, ambiguous selectors, malformed/truncated HTML, bounds, original clocks, hash/revision binding and defensive copying. Six new cross-language tests invoke the actual Python extractor with the repository's six stored guidance records, pass its output to the actual TypeScript gate, and confirm suspension in the existing entry evaluator. They verify that later matching context cannot clear pending holds and production data stays unchanged. All 74 existing browser tests remain passing; this increment adds no UI behavior.

Artifact `pilot-verification`, ID **11012780424**, contains production output, existing screenshots and lockfile, not private contexts or isolated candidate/test-site outputs. Retention: seven days. CI-reported ZIP SHA-256: `c957a98974a38816ffa9bfbc3218c42d1d05844a8ea7a91a85d2e53a11b1a47e`. This artifact was not downloaded for an independent digest or visual check in this increment.
Artifact: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36519854445/artifacts/11012780424

The final handoff/plan update is documentation-only and receives a separate CI check recorded in PR #1. The results above prove the exact implementation head, not future changes.

## Execution and review record

Direct container GitHub and NPS DNS was unavailable. Local development used an isolated partial workspace, not a full clone. Thirty Python tests and compileall passed locally on Python 3.13; the complete repository ran in GitHub CI on Python 3.12 and Node 24.

Tests were written first. The initial run stopped on the missing extractor module, not 28 independently observed behavior failures. After implementation, 28 tests passed. Author review then added two genuine failing regressions: an HTML base element could silently retarget unchanged links, and struck-out source text could be counted as an unchanged claim. Both returned observed rather than failed. Conservative parser guards repaired both; all 30 then passed. No test was removed or weakened.

The seven-file implementation comparison consists only of new parser/adapter, test and documentation files. Original gate, application, approved data, provider pipelines, dependency and workflow files are preserved. Review was author self-review, not independent approval. Existing Actions runtime and npm install-script warnings remain maintenance items. No new visual/accessibility audit is claimed; previous screen-reader, actual browser/OS zoom, cross-browser, native-popup and forced-color limitations remain.

## Source and live-release boundaries

The five public NPS pages were opened through web retrieval to check headings and textual scope. This is not raw-HTML capture, DOM compatibility verification, an uptime measurement or a context-baseline approval. All extraction fixtures are synthetic HTML; no real full-page source text was committed. Original guidance review timestamps were not refreshed by this source-family review.

The parser is not a browser. Strict balancing intentionally rejects some optional-end-tag/browser-repairable HTML. Scripts, styles, media, embedded documents, linked pages and dynamic presentation are not compared. Matching body text/link targets does not establish that all page behavior or park conditions are unchanged. Including global/footer content can conservatively generate extra review. These tradeoffs require real captured-page validation before automation.

The result is currently in-memory only. Private contexts and proposals must be retained together by protected operator orchestration before durable source-change handling is claimed. Context baselines are trusted reviewer inputs, not authenticated approvals. Digests establish consistency, not source authenticity, factual truth or rights. Real contexts or proposals committed to a public repository are public even when absent from visitor HTML; noindex is not access control.

No keyed NPS API request or key-configuration recheck occurred. The latest observed diagnostic remains run 36481482091, job 109224608968, at `2026-09-29T02:13:16Z`: empty NPS_API_KEY, not_configured, gate_passed:false, no requests. That used original preflight code `0dce38beb7c1d9bc3d7feba0d8a69ca1f97ddca7`, not the newest collector. It does not establish current secret settings. Owner setup remains in `docs/NPS_PREFLIGHT.md`.

Live API compatibility, reviewed credential-free fixtures, durable operator storage, source-content review, hosting and publication/rollback remain release requirements. No live public feed, recurring collection, deployment, ads, tracking, accounts, indexing, spending or provider agreement was activated. Neither M1 nor M2 is declared complete.

## Next coherent task

Read current PR/head/CI and preserve newer work. Do not rebuild the existing collector/archive/staging/history/preview pipelines, selected-text gate or extraction API.

Next implement **protected operator persistence for source observations and review evidence**, keeping the extraction result and its proposal register together with expected-revision checks, safe private destinations, failure recovery and explicit reviewer disposition. Start with a small offline slice; never silently delete a hold, renew reviewed_at, or approve a context as a side effect of capture. Keep this private operation separate from production promotion. Actual captures and human-reviewed context baselines remain prerequisites to claiming live source monitoring.

Validate real raw HTML against the explicit parser scope and retain appropriately reviewed fixtures before enabling source collection. The current headings/profiles are not DOM acceptance evidence. Once the owner-controlled API key is available, use the existing read-only preflight/staging/preview path for alert integration, rather than a new pipeline or repeated empty-key diagnostics.

Before scheduling/launch, resolve persistent storage, hosting, source-use, publication/rollback and publisher/privacy requirements. Ephemeral Actions workspaces are not durable hosted archives. Do not expand to 20 parks or activate advertising before pilot acceptance.

## Limits and lineage

Existing archive/preview guarantees assume trusted local filesystems and dependencies; hardware power-loss, network/Windows filesystems, hostile same-user mutation and off-host backup remain unverified. Abandoned locks and cleanup require operator review. Preview readiness is not publication approval or a signature of every asset.

Previous totals: foundation 79; source coverage 109; private history 167; staging 206; visitor history 246; private preview 293; planning checks 309; accessibility 347; selected-source gate 380 at `7d56fc0` / run 36517106972 and handoff `e1f89e0` / run 36517384443. Current 416-test extraction evidence is above. PR #1 remains draft and unmerged.
