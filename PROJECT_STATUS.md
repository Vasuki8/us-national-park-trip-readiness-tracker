# Project status and handoff

Updated: 2026-09-28 America/Toronto (verification completed 2026-09-29 UTC). **Seven official planning checks per park are implemented and CI-verified. A fresh NPS diagnostic still received no key; live integration and public release remain blocked.**

Repository: `Vasuki8/us-national-park-trip-readiness-tracker`.
Branch: `feat/pilot-foundation`. Draft PR: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/1
Main remains `a9d9c19e8307828c5bdb6f331e24ca3fe7afffce`. No merge or production deployment was performed.

## Standing direction and preserved capabilities

AdSense-first eventual public product, light theme, no paid data dependency. Validate five parks before expanding to 20. Trustworthy displayed data precedes indexing and advertising. Never infer an all-clear, reopening, permit exemption or annual validity from missing information.

The production build remains 14 HTML pages plus build.json, with park/state search, five park pages, source panels, a self-reported checklist, visitor history and now park-specific official planning resources. All five parks have entry-source evidence; only Yosemite and Rocky Mountain have dated rules. The other three have undated observations, not executable annual rules. Source, human review, effective, collection, build and publication clocks remain distinct.

Existing collection, immutable private archive, semantic comparison, staging receipt/recovery, history projection and isolated preview workflow are preserved. Their limits and recovery contracts remain in docs/EVIDENCE_HISTORY.md, docs/STAGING_COLLECTION.md, docs/VISITOR_HISTORY.md and docs/PREVIEW_BUNDLES.md. No replacement pipeline was built.

All five public alert snapshots remain `never_checked`; public histories remain empty. Existing entry rules, notes, operational timestamps and park inventory are unchanged. The new planning-link register intentionally changes page content and site snapshot identity, not operational coverage.

## New: seven official checks for each pilot

`data/planning-resources.json` contains **35 park/topic pairs**: roads, facilities, camping, accessibility, fees, permits and weather. Each retains a reviewed NPS URL, source-page title, original planning prompt and absolute `link_reviewed_at`. The source-navigation batch was reviewed at **2026-09-29T02:18:54Z**. Pages were opened and topics/titles checked through web retrieval; this is not an independent HTTP uptime test or current-conditions review.

`src/components/PlanningResources.astro` replaces the three generic coverage-gap cards on all five park pages. Each card says **Official link only**. The section explains that these topics are not monitored, that link review is not a conditions check/permit decision/price quote/forecast, and that opening a source does not complete the checklist. Native links work without JavaScript. The checklist has an explicit jump to `#official-checks`, without changing any checkmark.

`scripts/validate-planning-resources.ts` requires all seven topics exactly once per park, official park-specific HTTPS planning URLs, bounded text, exact permitted fields and valid nonfuture link-review times. Cross-park/lookalike/encoded/credential-bearing links, missing or duplicate categories, operational fields and impossible clocks fail the build. Diagnostics do not echo input. The data boundary validates this register and includes it in snapshot hashing; rule/feed coverage inputs and the date evaluator do not consume it.

Source-navigation findings and remaining acceptance gaps: **docs/PILOT_COVERAGE_AUDIT.md**.
Implementation plan: docs/superpowers/plans/2026-09-28-pilot-coverage.md.

## Verified implementation

Code/test head: **9588675aa616a3e24acafdf71760ef57ddec3f39**.
**Verify pilot #28, run 36512665650, completed successfully.** Job **109228036485** tested temporary PR merge **66dac3bd458a38a2dfb7e4486415848541ea7dd3** against unchanged main. This is a CI test merge, not an actual merge into main.
Run: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36512665650

| Check | Verified result |
|---|---|
| Reproducible npm installation | Passed |
| Node core/data/history/preview/planning tests | 105 passed, 0 failed |
| Python collector/archive/staging/projection/preview tests | 158 passed |
| Astro check | 22 files; 0 errors, 0 warnings, 0 hints |
| Production static build | 14 HTML pages plus build.json |
| Generated-output tests | 18 passed |
| Chromium browser tests | 28 passed |
| **Total automated tests** | **309 passed; 16 added in this increment** |

Twelve new unit tests cover complete inventory, safe official URLs, strict link-only scope, timestamps, malformed text and defensive copying. Four new browser cases cover all35 actual hrefs/prompts/review times, preserved never-checked alerts and empty histories, native checklist navigation, no-JavaScript use across all5 parks, normal360px page layouts and doubled root text size within the new component. The text-resize test is not a claim of full-site browser-zoom/accessibility acceptance. All24 existing browser cases remain passing, including private-preview isolation.

Artifact `pilot-verification`, ID **11009312810**, contains production build, existing browser screenshots and lockfile; not private archive/candidate preview outputs. Seven-day retention. ZIP SHA-256: `a68a24b622f2ed2651cba2ec27f6f2e7652da42ad1d84cfc51616169601f8ae9`.
Artifact: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36512665650/artifacts/11009312810

The final handoff/audit/preflight/plan update is documentation-only and receives a separate CI check. This recorded result proves the exact implementation head, not future edits.

## Execution and review

Direct container GitHub DNS was unavailable. Local verification used an isolated partial scratch workspace, not a full clone. The12 new Node tests were observed RED with an explicit not-implemented stub, then passed locally on Node22.16.0. Complete verification ran in GitHub CI on Node24/Python3.12.

First pushed tests/register/plan at2bf691ac. CI#27,run36512367259, passed105Node,158Python,18static and all24existing browser cases; exactly4new browser cases failed on the missing cards/link. The UI implementation9588675 then passed all309tests in#28. No failing assertion was removed or weakened.

Author self-review covered the ten implementation/test/plan changed files: source register scope, complete park/category pairs, boundary validation, URL/text handling, unchanged rule/feed coverage, native checklist behavior and responsive markup. No independent reviewer, comprehensive accessibility/visual audit or field-condition verification is claimed. Existing Actions runtime deprecation and npm install-script warnings remain non-blocking maintenance items. No dependency or workflow change was made.

## Fresh NPS diagnostic — owner action still needed

The existing read-only preflight was rerun in this increment. **Run36481482091, job109224608968, at2026-09-29T02:13:16Z** returned:

```json
{"schema_version":1,"mode":"read_only","status":"not_configured","gate_passed":false,"publication_performed":false,"checks":[]}
```

The runner received an empty `NPS_API_KEY`; **no NPS request was made**. This is a fresh result, not an assumption based on the earlier run. It does not distinguish an absent key from a restricted/environment-only/misnamed secret. The job's successful execution is not successful live validation.

The rerun checked out original preflight code **0dce38beb7c1d9bc3d7feba0d8a69ca1f97ddca7**, not this application's newest commit. Review the intended executed revision before validating newer collector code.

Owner setup: repository Settings → Secrets and variables → Actions → Secrets → New repository secret, named **NPS_API_KEY**. Obtain/configure the key privately and rerun the read-only preflight. Do not put it in chat, source code, command arguments or issues. Full setup, original and latest diagnostic evidence: docs/NPS_PREFLIGHT.md.

No live public alert/history feed, scheduled collection, deployment, advertising, analytics, accounts, indexing, spending or provider-agreement acceptance was activated. Official-link coverage is not normalized road/facility/permit/fee/weather coverage.

## Next coherent task

Read the latest PR/head/CI before editing; preserve newer work. Do not rebuild collection, archive, staging, visitor history, private preview or these35 planning links.

Live-source compatibility is still gated by the owner-controlled key supplied to the preflight. Once configured, validate actual provider shapes, review credential-free fixtures and use the existing staging/preview path. Do not keep rerunning an unchanged empty-key job as a substitute for feature progress; the diagnostic above is the latest observed attempt, not a promise about later configuration.

The next self-contained code task available without credentials is the remaining **whole-site accessibility/reflow acceptance**: check keyboard focus,200%text/browser zoom, critical controls/notices/evidence and static fallback across the14pages, repair demonstrated failures, and retain browser evidence. Keep this separate from source-content and live-data approval. Follow with substantive editorial source-change review using the existing evidence conventions rather than silently refreshing review times.

Before scheduling or launch: resolve operator-controlled persistent archive storage and production hosting, source-content review, real live compatibility, publication/rollback tests and publisher/privacy requirements. Ephemeral Actions checkouts and preview folders are not durable hosted archives. The detailed acceptance audit does not mark M1/M2 fully complete. Do not expand to20parks or activate ads yet.

## Limits and verification lineage

Archive/preview workflows assume a trusted local filesystem and trusted dependencies. No hardware power-loss, Windows-directory, network-filesystem, hostile same-user mutation or off-host backup guarantee is made. Digests are consistency checks, not signatures or redistribution permission. The preview ready marker validates local identity/noindex completion, not a signed digest of every asset; noindex is not access control. Abandoned locks and disposable-workspace cleanup require operator review.

Prior verified totals: foundation79; source coverage109; private history167; staging206; visitor history246 at70322a54/run36508305834 and handoff0a32079/run36508571989; private preview293 at7d7fdcbc/run36510906825 and handoff1d96363/run36511195194. The309-test planning-check result is recorded above. PR#1 remains draft and unmerged.
