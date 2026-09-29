# Project status and handoff

Updated: September 29, 2026 (America/Toronto).
**Private source-review persistence and non-approving reviewer decisions are implemented, reviewed and CI-verified. Live source monitoring, final approval/reconciliation and the public pilot release remain unfinished.**

Repository: `Vasuki8/us-national-park-trip-readiness-tracker`.
Branch: `feat/pilot-foundation`.
Draft PR: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/1
Main remains `a9d9c19e8307828c5bdb6f331e24ca3fe7afffce`. No merge or production deployment was performed.

## Standing direction and preserved capabilities

The eventual product is AdSense-first, light-theme and has no paid data dependency. Validate five parks before expanding to 20. Trustworthy displayed data precedes indexing and advertising. Do not infer an all-clear, reopening, permit exemption or annual validity from missing information.

The production build remains 14 HTML pages plus build.json: park/state search, five park pages, source evidence, self-reported checklists, notice history and seven official planning links per park. All five parks have entry evidence; only Yosemite and Rocky Mountain have dated rules. The three other parks have undated observations. The 35 planning destinations are links only, not current-conditions checks. Source, approval, effective, collection, import/build and publication clocks remain distinct.

Existing alert collection, private notice archive, staging/recovery, visitor history, isolated previews, accessibility repairs, selected-source review gate and scoped HTML extractor are preserved. Their contracts remain in docs/EVIDENCE_HISTORY.md, STAGING_COLLECTION.md, VISITOR_HISTORY.md, PREVIEW_BUNDLES.md, ACCESSIBILITY_REVIEW.md, ENTRY_CHANGE_REVIEW.md and ENTRY_SOURCE_EXTRACTION.md.

Public alerts remain `never_checked`; public histories and the public pending-review register remain empty. Original rules/notes, approval timestamps, planning resources and all public datasets are unchanged. No actual source captures, new context approvals or real reviewer decisions were added to public product data.

## Completed private editorial ledger

The branch already contained implementation `da698d4a12553bb2ecc9d1f65eba9ec3c6c8b9cb` when this continuation inspected it, ahead of the previous 416-test handoff. Its Verify pilot #38 run (36570324360, job 109412408594) had passed. That newer work was preserved, audited and finished rather than recreated.

`tracker.entry_review_store.EntryReviewStore` retains supplied captures, their extracted current/reference context, precise failure reasons, checks, accumulated proposals and reviewer decisions. The ledger is separate from the park-alert archive and is not imported by the public site. It uses one owner-only local SQLite database outside the repository; no new package, account or hosting service was added.

The Python event model invokes the existing extractor and the existing TypeScript assessment gate through a bounded Node bridge. The entire stored chain is re-evaluated on read; a rehashed but inconsistent proposal/context is refused. Matching checks are retained too, so they cannot be replayed backwards merely because they created no proposal. Original guidance and context-approval timestamps are not renewed.

Writes require the expected ledger revision both before preparation and within the transaction. Captures, context, proposals and the new head commit together. Exact retries acknowledge an existing commit without duplicate events or rolling back newer history. Failed transactions retain the previously committed state; explicit recovery verifies committed evidence after SQLite journal recovery. A killed initializer may leave an invalid empty file requiring operator inspection, not an automatically accepted empty ledger.

The offline CLI provides `status`, `record`, `disposition` and `recover`. Summaries expose revision/proposal references, counts, safe reasons and timestamps, not HTML, context, private paths, rationale or arbitrary exception text. Input and storage checks reject nonprivate permissions, protected repository destinations, symlinks, hard links, named pipes and unrelated databases. The Node child does not inherit API keys or NODE_OPTIONS.

Reviewer decisions currently support only `retain_hold` and `request_guidance_revision`. Both retain every pending hold and the original evidence. Reviewer identity is an operator-supplied label, not authenticated identity. There is no approve/resolve command, automatic guidance rewrite, baseline approval or production promotion.

Contract and commands: **docs/ENTRY_REVIEW_LEDGER.md**.
Plan and execution record: docs/superpowers/plans/2026-09-29-entry-review-store.md.

## Review repairs in this continuation

Four new tests were added in `61a1816ab53226af46b1df2f470d26b06cee8964`. Verify pilot #39 (36571477262, job 109416293174) ran 138 passing Node tests and 230 Python tests. It reproduced three failed assertions in two test methods: Boolean schema versions in a rehashed event/register passed replay, and a Boolean-to-integer change in otherwise matching guidance passed the exact-inventory check. The subsequent build/browser steps were skipped in that deliberately failing run.

Cause: Python nested equality treats true and 1 as equal. Fix `67a24917c44567ede4424f3d558453ad825df240` compares canonical JSON bytes for replayed events, original guidance and initial seed identity. This preserves JSON types without changing the ledger format, legitimate stored events or review policy. The production repair changes three comparisons plus two comments in two files.

The other two new tests verify lost acknowledgement of a committed reviewer decision and a competing reviewer write. They confirm retry without duplicate decisions, preservation of original timestamps and holds, and rejection of a stale losing write. All four tests and the previously failing subcases pass after the fix. No test was removed or weakened.

## Exact verified implementation

Code/test head: **67a24917c44567ede4424f3d558453ad825df240**.
**Verify pilot #40, run 36572571183, completed successfully.** Job **109419924407** tested temporary PR merge **1e7b2d5f204d1e673832d82dc168afb75afa1a2a** against unchanged main. A CI test merge is not an actual merge into main. Complete job logs were read.
Run: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36572571183

| Check | Verified result |
|---|---|
| Reproducible npm installation | Passed |
| Node core/data/review/cross-language tests | 138 passed |
| Python collector/archive/staging/extraction/ledger tests | 230 passed |
| Astro check | 24 files; zero errors, warnings or hints |
| Production build | 14 HTML pages plus build.json |
| Generated-output tests | 18 passed |
| Chromium browser tests | 74 passed |
| **Total automated tests** | **460 passed** |

Relative to the previous communicated 416-test extraction milestone, the ledger adds 44 tests: 40 already present in da698d4 and four added during this review. The ledger tests include real child-process termination before/after commit, transaction conflicts, lost acknowledgements, strict private I/O, type-exact replay, and integration with the six actual repository guidance records. Synthetic inputs do not establish live-source compatibility. All existing 74 browser cases remain passing; no UI change or new visual/accessibility audit is claimed.

Artifact `pilot-verification`, ID **11035336902**, contains production output, existing screenshots and lockfile; not private ledgers/captures or isolated candidate/test outputs. Seven-day retention. CI-reported ZIP SHA-256: `1418bce04d4b0866811f24deab5031e1bc603b211587c59882f17bcb5b886db3`. Not independently downloaded in this continuation.
Artifact: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36572571183/artifacts/11035336902

The final handoff and plan commit changes documentation only and receives its own CI check, recorded in PR #1. The result above identifies the exact implementation, not future changes.

## Review and operating limits

Review was author self-review, not independent approval. This continuation used live GitHub file/commit reads and GitHub CI; direct local GitHub DNS was unavailable, and no full local clone/test pass is claimed. The earlier implementation's local evidence is retained in its plan rather than attributed to this review. No API-key configuration check or NPS request was made in this continuation.

The ledger is bounded: 8 MiB input, 12 MiB event, 64 events and 128 MiB aggregate event payload. Capacity errors preserve existing evidence; no auto-pruning, rotation or approved-guidance migration is implemented. Reads replay the bounded chain and prioritize verification over throughput.

Supported tests concern trusted local POSIX filesystem/process-interruption behavior. Hosted storage, encryption, authenticated reviewers, multi-host operation, Windows/network filesystems, hardware power-loss and off-host backup/restore are not established. An actor able to rewrite all source inputs and database contents is outside the authenticity guarantees. Existing CI action-runtime and npm install-script warnings remain maintenance items; earlier manual accessibility limitations still apply.

## Remaining live-source and publication gates

Actual captured NPS HTML has not yet been validated against the extractor; its HTML fixtures are synthetic. Strict tag balancing may reject browser-repairable markup. Dynamic content, media, embedded documents and linked pages are outside its explicit body-text/link scope. Separately reviewed real context baselines are required; a short saved excerpt cannot be promoted automatically into one.

The last observed NPS API diagnostic remains run 36481482091, job 109224608968, at 2026-09-29T02:13:16Z: empty NPS_API_KEY, not_configured, gate_passed:false, no requests. It used original preflight code 0dce38beb7c1d9bc3d7feba0d8a69ca1f97ddca7 and does not establish current secret settings. Setup guidance is in docs/NPS_PREFLIGHT.md. Do not repeatedly rerun an unchanged empty-key diagnostic as feature progress.

Real captures and proposals are private untrusted material. Storing them or hashing them does not confer redistribution rights; noindex is not access control. Live API compatibility, reviewed fixtures, durable operator storage/backup, source-content review, final approval reconciliation, hosting and publication/rollback remain release requirements. No live public feed, collection schedule, deployment, indexing, ads, tracking, accounts, spending or provider agreement was activated. Neither M1 nor M2 is declared complete.

## Next coherent task

Read current PR/head/CI first. The ledger, CLI, source extractor, review gate, alert collector, archive, staging and preview systems exist; do not rebuild them.

**Prioritize real captured-page compatibility and reviewed context-baseline evidence next**, starting with the five existing entry-source profiles. Keep captures outside the public repository, record actual retrieval times, and test the existing parser against real markup before introducing further automation. Preserve explicit uncertainty when extraction fails and do not label missing baselines as matching. Do not silently renew original guidance or remove pending holds.

After the actual source inputs are understood, implement explicit approved-guidance reconciliation with retained reviewer disposition and old/new revision evidence. The current disposition commands record review work but intentionally cannot complete approval. Any new network capture must be bounded, opt-in and distinct from public promotion; reuse the ledger for evidence rather than another storage mechanism.

When an owner-controlled NPS key is available, validate alerts through the existing preflight/staging/preview path. Before scheduling or launch, resolve persistent storage, hosting, source-use and publication/rollback. Ephemeral Actions workspaces are not durable hosted archives. Do not expand to 20 parks or activate advertising before pilot acceptance.

## Verification lineage

Prior communicated totals: 79 foundation; 109 source coverage; 167 private history; 206 staging; 246 visitor history; 293 previews; 309 planning checks; 347 accessibility; 380 selected-source gate; 416 extraction (9a32976 / run 36519854445, handoff 9f7de20 / run 36520261071). New ledger implementation da698d4 passed #38; type-identity review/fix passed all 460 in #40. PR #1 remains draft and unmerged.
