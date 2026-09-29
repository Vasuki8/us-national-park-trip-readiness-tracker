# Project status and handoff

Updated: **September 29, 2026 (America/Toronto)**.
**Actual HTML from all five configured NPS entry pages now passes scoped extraction and temporary private-ledger replay. Reviewed context baselines, persistent live evidence, final approval reconciliation and public release remain unfinished.**

Repository: `Vasuki8/us-national-park-trip-readiness-tracker`.
Branch: `feat/pilot-foundation`.
Draft PR: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/1
Main remains `a9d9c19e8307828c5bdb6f331e24ca3fe7afffce`. No merge or production deployment was performed.

## Standing direction and preserved capabilities

Eventual AdSense-first, light-theme product, no paid data dependency. Validate five parks before expanding to 20. Trustworthy data precedes indexing/advertising. Never infer an all-clear, reopening, exemption or annual validity from absent information.

The production build remains 14 HTML pages plus build.json: park/state search, five park pages, dated/undated source evidence, self-reported checklists, notice history and 35 official planning links. Only Yosemite and Rocky Mountain have dated rules; the other three parks have undated observations. Planning links are not live condition checks. Original source, approval, effective, collection, import/build and publication clocks remain distinct.

Existing alert collector/archive/staging, visitor history, isolated candidate previews, accessibility repairs, source review gate, scoped extraction and private editorial ledger remain in place. Do not rebuild these systems. Contracts are in docs/EVIDENCE_HISTORY.md, STAGING_COLLECTION.md, VISITOR_HISTORY.md, PREVIEW_BUNDLES.md, ACCESSIBILITY_REVIEW.md, ENTRY_CHANGE_REVIEW.md, ENTRY_SOURCE_EXTRACTION.md and ENTRY_REVIEW_LEDGER.md.

Public alert snapshots remain `never_checked`. Public histories and the public entry-review register remain empty. No original guidance, approved date, planning resource or public dataset was changed in this increment. The site interface, dependency files, existing CI and alert preflight workflow are unchanged.

## New: real-page compatibility and envelope repair

The new `tracker/entry_compatibility.py` diagnostic makes one explicitly requested credential-free HTTPS GET for each of the five fixed source profiles. It rejects redirects, unsupported types/encodings, invalid UTF-8, oversized/incomplete responses and inconsistent capture receipts. No arbitrary URLs, retries or API-key lookup are supported.

It runs actual captures through `inspect_entry_sources` with no context baselines, records them through the existing SQLite ledger and TypeScript gate in a temporary private directory, and reads/replays the committed event. Safe metadata only is printed; no raw source bodies, context text, proposal replacements, private paths or credentials are uploaded. Temporary evidence is removed at the end. This validates integration but is not a durable live archive.

Initial live runs 36574128149 and 36574421469 received all five pages with HTTP 200 but exposed a shared parser incompatibility: redundant document-closing tags after an already complete body/html, preceded by scripts. `tracker/entry_html.py` now handles precisely one inert duplicate closing pair while retaining strict interior balancing. New regression tests also exposed and repaired silently discarded out-of-body prose/elements. Missing or misnested internal tags, duplicate opening bodies, appended visible content and incomplete/reordered closing pairs still refuse. Script/style behavior remains outside comparison scope, not implicitly approved.

The final diagnostic workflow is manual `workflow_dispatch` only, contents:read, with a five-minute job limit and no capture artifacts. Development-only marker-gated push execution has been removed. No recurring collection was enabled. The 15-second network timeout applies per socket operation, not as an absolute standalone command deadline.

## Actual live verification

**Entry HTML compatibility diagnostic #3, run 36575873171, job 109431220513, head a98487ec123b629ba433deee00fe3ab24b29fc4c.**
https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36575873171

On **2026-09-29 at 13:32:52.880Z–13:32:53.190Z** (9:32 a.m. Toronto), all five exact source URLs returned HTTP 200 and their actual HTML contexts were extracted. All six saved guidance excerpts were uniquely present in that scope. Actual captures, extracted evidence and resulting proposals successfully round-tripped through the existing temporary private ledger and review gate.

Report: `all_contexts_extracted:true`, `ledger_replay_verified:true`, `pending_proposals:6`, `approved_context_baselines:0`, `approval_performed:false`, `publication_performed:false`, `raw_captures_uploaded:false`. Every source reason was `context_not_reviewed`.

**The six temporary holds are missing-context-review holds, not confirmed rule changes.** Presence of saved excerpts does not approve surrounding exceptions, renew original guidance dates or establish current park conditions. The diagnostic intentionally created no context baseline or public proposal. Raw captures were not retained after its temporary ledger was removed. Exact source clocks, byte counts and raw/context hashes are recorded in **docs/LIVE_ENTRY_COMPATIBILITY.md**.

## Exact implementation verification

Code/test head: **a98487ec123b629ba433deee00fe3ab24b29fc4c**.
**Verify pilot #44, run 36575877382, completed successfully.** Job **109431236802** tested temporary PR merge **28b113ba5a98d721289208ec39a91191a7521abd** against unchanged main. This CI test merge is not a merge into main. Complete logs were read.
https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36575877382

| Check | Verified result |
|---|---|
| Reproducible npm installation | Passed |
| Node core/data/review/cross-language tests | 138 passed |
| Python collection/storage/extraction/compatibility tests | 258 passed |
| Astro check | 24 files; 0 errors, 0 warnings, 0 hints |
| Production build | 14 HTML pages plus build.json |
| Generated-output tests | 18 passed |
| Chromium browser tests | 74 passed |
| **Total automated tests** | **488 passed; 28 added** |

The 28 new methods cover the observed document trailer and hidden-loss regressions, opt-in/fixed-source transport, response/receipt validation, failure redaction and actual extractor/ledger/gate integration with all six stored guidance bindings. Unit fixtures remain synthetic; the separate live run above supplies actual captured-HTML evidence. No existing test was removed or weakened. All earlier browser cases remain passing; no UI change or new visual/accessibility audit is claimed.

Artifact `pilot-verification`, ID **11037711139**, includes production output, existing screenshots and lockfile, not captures or private ledgers. Seven-day retention. CI-reported ZIP SHA-256: `331de6b67608ae051bec8598f33d344b73ea11916515bd7f71e6e010d68cb05d`; this verification artifact was not independently downloaded in this increment.
https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36575877382/artifacts/11037711139

The final handoff adds documentation and disables the temporary push trigger; it does not change the verified application/test code. Its own CI result must be checked and recorded in PR #1, not inferred from #44.

## Execution and review limits

Local GitHub/NPS DNS was unavailable. A temporary development workflow packaged only committed public source code as a git archive. Its downloaded ZIP digest was verified (`c942fb0cc8959b7da4944bee245fe2a8ba726e378cdfc36816398138fa7e536a`). Local work used that complete isolated source snapshot, not a clone with upstream history; the source-artifact step was removed afterward. No live page body was in that artifact.

Tests preceded the repair: the 14 envelope methods initially produced nine failed assertions and four errors, including genuine silent-discard cases. They passed after the narrow fix, together with the 30 original extraction tests. The 14 diagnostic methods first ran against explicit unimplemented interfaces, then passed against the implementation. The local entry family passed 100 Python tests and eight cross-language Node cases, plus compileall.

A complete local baseline Python run on 3.13 exposed one existing stderr assertion contaminated by SQLite ResourceWarnings; a complete local Node run lacked installed Astro dependencies (136 passed, two failed). No full local pass is claimed, and unrelated tests were not weakened. Full #44 CI installed the lockfile and used the supported Node 24/Python 3.12 configuration; all 488 passed.

Review was author self-review, not independent approval. Existing action-runtime/install-script warnings remain. Previous manual screen-reader, actual OS/browser zoom, cross-browser and forced-color limitations remain. Hardware power-loss, Windows/network filesystems, hostile same-user mutation, encryption/authenticated reviewers and off-host backup are not newly established.

## Remaining gates and next coherent task

Read current PR/head/CI first. Real HTML body-text/link compatibility is now demonstrated for the five captured pages, so do not repeat that milestone or rebuild the collector, parser, ledger or preview systems.

**Next establish explicitly reviewed reference contexts and an approved-guidance reconciliation workflow**, using owner-controlled persistent captures and the existing ledger. Keep original capture times, current/previous guidance revisions, reviewer decisions and all unresolved holds linked. Never derive approval from a hash, matching sentence or successful HTTP request. The diagnostic CLI intentionally discards its temporary store, so it cannot substitute for persistent baseline evidence. Changing parser acceptance can make older ledger events fail replay; such cases require explicit operator handling, not automatic history rewrites.

Only the bounded body text/block/H1/link representation was tested. Linked/dynamic content, scripts/styles, media and embedded documents remain outside scope. No source-content rights or factual guarantees follow from extraction or hashing. Actual approved context baselines are still zero. Final approval/hold-resolution and publication remain separate from source capture.

The keyed NPS alert API and private-key configuration were not checked. The last historical key diagnostic remains run36481482091/job109224608968 at2026-09-29T02:13:16Z: empty key/no requests, original preflight code0dce38beb7c1d9bc3d7feba0d8a69ca1f97ddca7. It does not establish current secret settings. Use docs/NPS_PREFLIGHT.md when the owner-controlled key is ready; do not repeatedly rerun an unchanged empty-key check as progress.

Persistent storage/backup, reviewed source content, alert API compatibility, final editorial approval, hosting and publication/rollback remain release requirements. No deployment, indexing, advertising, tracking, accounts, spending or provider agreement was activated. Neither M1 nor M2 is declared complete; no expansion beyond five parks.

## Verification lineage

Prior totals: 79 foundation;109 source coverage;167 private history;206 staging;246 visitor history;293 preview;309 planning;347 accessibility;380 selected-source review;416 extraction;460 ledger/identity repair (67a2491 / run36572571183, handoffdc3c794 / run36573251437). Current implementation is 488 tests plus the separate five-page live capture/replay diagnostic above. PR #1 remains draft and unmerged.
