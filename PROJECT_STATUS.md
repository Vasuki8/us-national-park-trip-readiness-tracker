# Project status and handoff

Updated: 2026-09-28. **Development foundation, source coverage and private evidence/history capability implemented. Full public M1 release remains incomplete.**

Repository: `Vasuki8/us-national-park-trip-readiness-tracker`.
Branch: `feat/pilot-foundation`. Draft PR: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/1
Main remains at the initial README commit `a9d9c19e8307828c5bdb6f331e24ca3fe7afffce`. No merge or production deployment was performed.

## Standing product direction

AdSense-first eventual public product, light theme, no paid data dependency. Validate five pilot parks before expanding to 20. Trustworthy displayed data comes before traffic expansion, indexing or advertising. No safety scores, all-clear inference, guessed exemptions or year extrapolation.

## Existing product preserved

The Astro site has 14 HTML pages plus a build manifest, a searchable five-park directory, responsive light styling, source panels and a self-reported checklist. All five parks have stored entry-source evidence. Only Yosemite and Rocky Mountain have dated rules for the checker; Yellowstone, Zion and Grand Canyon have undated observations, never executable annual rules. Coverage labels derive from data and expire in the browser. Human review, collection, effective, build and publication clocks are distinct.

All five committed alert snapshots remain `never_checked`. Weather, booking inventory, complete permit/road/facility coverage and a real public change feed are not active. No source review or collection timestamp was advanced during this increment.

## New: private evidence and observation history

- `tracker/history_model.py`: strict validation of the existing normalized alert contract and pure semantic comparison. First successful collection is a baseline; later differences are added/edited/no-longer-present-in-feed, never reopening claims. Unchanged/reordered records produce no semantic events. Failed/quarantined attempts retain the accepted baseline and cannot rewrite records or their clocks.
- `tracker/history_store.py`: deduplicated content-addressed source text and immutable, hash-linked per-park observations. Verified reads reconstruct exact normalized records and recompute differences. An exclusive writer lock and atomic head replacement separate completed history from orphaned staging objects. Identical retries are idempotent; older/conflicting observations, damaged objects, unsafe paths and suspicious record drops fail closed.
- `tracker/history.py`: explicit offline `record` and `report` commands. They do not use keys, make network requests, modify source snapshots or publish website data. Reports have bounded output with explicit omitted counts and exclude provider notice text and raw exception messages. The CLI blocks archive destinations inside website/source/Git directories.
- `state/` is ignored by Git. No actual NPS alert history, credentials or private archive was committed. This adds capability, not populated live history or scheduled persistence.
- Resource bounds cover on-disk objects, observation count and reconstructed snapshot size. Nothing is automatically pruned or repaired.

Usage, storage layout, retention bounds and operator recovery are in `docs/EVIDENCE_HISTORY.md`. The scope/plan is `docs/superpowers/plans/2026-09-28-evidence-history.md`.

## Verification

Code/test head: `f43ee4ccd644d3f89868857658767f6b78654e85`.
Verification run: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36485050775
**Verify pilot #10 completed successfully.** Job `109139807159` tested temporary PR merge ref `b463e71be02168238add619ffdc823e4c3c909e2` against unchanged main.

| Check | Verified result |
|---|---|
| Reproducible npm installation | Passed |
| Node core/data/source-coverage tests | 50 passed |
| Python collector/preflight/history tests | 89 passed |
| Astro check | 18 files; 0 errors, 0 warnings, 0 hints |
| Static build | 14 HTML pages plus build.json |
| Generated-output tests | 18 passed |
| Chromium browser tests | 10 passed |
| **Total automated tests** | **167 passed; 58 added in this increment** |

Artifact `pilot-verification`, ID `10998886129`, contains the existing static build/browser screenshots and lockfile, not private archives. Seven-day retention. ZIP SHA-256: `365dde340056ea5bfc2e055fbe3e45d7ed870f6981be0dc1742ca84e27a40960`.
Artifact: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36485050775/artifacts/10998886129

The earlier implementation `03d70ccb7f895d580e83b729a3425d17a16ef9ef` passed full workflow 36484859597. The follow-up changes only add an abrupt-process-exit regression test; application implementation is identical. Handoff-only commits after the recorded test head must be verified through their own CI. A successful temporary PR merge test is not an actual merge into main.

Local verification covered 55 tests on Python 3.13/Linux in an isolated partial workspace, including actual subprocess termination. Full GitHub CI supplies the unchanged collector for three additional integration tests and runs the complete existing Node/Astro/static/browser suites on Python 3.12. Do not present the local partial workspace as a complete repository clone: direct container GitHub DNS was unavailable. All new Python code/test blob hashes were checked against the uploaded Git objects.

Review was an author self-review, not independent approval. The review added and tested two missing safeguards: reconstructed-memory growth despite evidence deduplication, and forbidden website/source output destinations. No existing tests were removed or weakened. Initial model/store/CLI tests failed on absent modules before implementation; review regressions reproduced the missing behaviors before fixes. The abrupt-exit test passed against the implemented store without further production changes.

The new tests cover baseline semantics, additions/edits/removals, failure/recovery, timestamps, replay conflicts, Unicode/hash integrity, exact schema/source validation, lost/corrupt evidence, forged semantic changes, isolated park chains, resource limits, CLI sanitization/truncation and actual collector compatibility using synthetic responses. The process-exit test confirms the previous head remains readable and that an abandoned lock requires explicit recovery after confirming its process is stopped. It is not a test of hardware power loss or network filesystems.

## Live NPS gate: unchanged, not rechecked in this increment

The last observed read-only NPS preflight was run 36481482091, job 109127917904, at 2026-09-28T20:45:52Z. It received an empty `NPS_API_KEY` and reported `not_configured`, `gate_passed: false`, `publication_performed: false`, `checks: []`. No API request occurred. This result does not distinguish absent, misnamed, inaccessible or environment-only secrets, and it does not establish the current secret configuration.

Once an owner-controlled repository Actions secret named `NPS_API_KEY` is configured, rerun the existing read-only preflight and inspect actual source shapes before accepting live records. Never paste keys into chat, URLs, source code or issues. Configuration and interpretation remain in `docs/NPS_PREFLIGHT.md`.

## Next coherent task

Read the latest PR/head/CI first and preserve newer work. The private archive, semantic differ and offline CLI now exist; do not rebuild them or the earlier data-driven coverage layer.

The next key-independent task is to connect candidate collection to archival in a staging-only orchestration path: record successful, failed and quarantined attempts coherently; recover from interruptions without advancing public data; expose safe operator status. Then define a validated public-history projection and its publication checks. No scheduler should run until archive persistence on operator-controlled storage is resolved: GitHub Actions checkouts are not durable private archives.

When the NPS key is available, validate live transport and schema privately and retain reviewed credential-free fixtures. Private archival does not confer content-use approval for public redistribution. Public-history rendering, source-change review, rights checks, production hosting and rollback remain gates before indexing or ads.

## Known limits and deferred work

Local trusted filesystem only. Linux command/interruption cases are tested; Windows directory durability, sudden power loss, network filesystems, hostile same-user writers, off-host backup/restore and storage migration are not verified. Hashes detect damaged objects but are not signatures against a party controlling the whole archive. Raw HTTP response capture, automatic editorial source-change review and reviewed bulk-removal approval are not implemented. Existing Actions runtime and npm install-script warnings remain maintenance items; no dependency/workflow changes were made here.

No deployment, scheduled collection, accounts, tracking, advertising or spending was activated. No independent visual/accessibility or field-conditions audit is claimed. PR #1 remains draft and unmerged; live-condition and public-release readiness must not be inferred from passing synthetic tests.

## Verification lineage

- Foundation: 79 tests at `7c39fb3` / run 36479129760 and handoff `83352bd` / run 36479734880.
- Source coverage: 109 tests at `94bb7af` / run 36482305462 and handoff `f232154` / run 36482644929.
- Private history: code `03d70cc` / run 36484859597; follow-up process-exit test and final recorded verification above.
