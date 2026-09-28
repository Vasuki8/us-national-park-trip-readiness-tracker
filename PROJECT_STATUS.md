# Project status and handoff

Updated: 2026-09-28. **Five-park development foundation, source coverage, private evidence history and recoverable staging collection are implemented. The public pilot release remains incomplete.**

Repository: `Vasuki8/us-national-park-trip-readiness-tracker`.
Branch: `feat/pilot-foundation`. Draft PR: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/1
Main remains at `a9d9c19e8307828c5bdb6f331e24ca3fe7afffce`. No merge or deployment was performed.

## Standing direction and existing product

AdSense-first eventual public product, light theme, no paid data dependency. Validate five pilot parks before expanding to 20. Trustworthy data precedes indexing and advertising. Never infer an all-clear, reopening, permit exemption or annual validity from missing information.

The Astro site has 14 HTML pages plus a build manifest, park/state search, five park pages, evidence panels and a self-reported checklist. All five parks have stored entry-source evidence; only Yosemite and Rocky Mountain have dated rules. Yellowstone, Zion and Grand Canyon have separate undated observations, never executable annual rules. Coverage labels derive from data and expire in the browser. Human review, collection, effective, build and publication clocks remain distinct.

The existing private archive retains reconstructable normalized notice text and immutable per-park observations. Its first successful check is a baseline; later events distinguish additions, edits and no-longer-present-in-feed notices. Failed/quarantined checks retain last-good evidence without generating removals. Offline record/report commands and archive bounds remain supported. See `docs/EVIDENCE_HISTORY.md`.

All five committed public alert snapshots still say `never_checked`. This increment does not modify the frontend, public data, existing collector, dated rules, undated notes, dependencies or workflows. No source-review or collection timestamp in website data was advanced.

## New: staging-only collector-to-archive integration

- `tracker/staging.py`: `StagingCollector.collect`, `recover` and `status` connect the existing collector to `archive/` inside an operator-controlled staging root. One park is processed per invocation. Validated pending receipts retain the candidate and the exact archive parent used for collection before archival starts.
- `tracker/history_store.py`: optional `expected_head` on `append`, checked inside the archive writer lock. Existing callers and on-disk schemas are unchanged. An intervening offline writer causes a conflict rather than applying a candidate against a different baseline. Exact committed retries are idempotent.
- Offline recovery reuses the saved candidate and original check timestamp, never another network request. It can acknowledge a committed ancestor without rolling back newer history. An uncommitted receipt whose parent has changed is retained for review. Receipt cleanup happens only after verified archival.
- Successful, failed and quarantined source attempts are archived distinctly. The stricter archive contract can quarantine collector-accepted but invalid records while retaining only prior accepted text. Private archival success does not imply provider success, complete coverage or permission to publish.
- `tracker/stage.py`: explicit `collect --live`, `recover` and `status` commands. Live collection requires a private `NPS_API_KEY`; missing consent or invalid credentials refuse before state writes or requests. Status/recovery are offline. Provider echoes of the configured key are rejected before retention. Diagnostics use fixed errors and scalar metadata, not raw notice text, responses or exceptions.
- Pending receipts are bounded by object size, total bytes and file count, including temporary/final-name reservation. Existing archive bounds also apply. Symlinks, traversal, protected source/site/Git directories and unsafe entries are rejected. Neither staging nor archive locks are automatically stolen or removed.

Commands, transaction boundaries, exit codes and operator recovery are documented in `docs/STAGING_COLLECTION.md`. The implementation plan is `docs/superpowers/plans/2026-09-28-staging-collection.md`.

## Verified implementation

Code/test head: **`afdf98f89f4481fe59cd666c59032be415f11348`**.
Run **36487323692**, **Verify pilot #12**, completed successfully on 2026-09-28.
Run: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36487323692
Job **109147282228** tested temporary PR merge **`83a051e91c57d2ce36d976a2d8e96d75e70f2b22`** against unchanged main. This is a test merge, not a merge into main.

| Check | Verified result |
|---|---|
| Reproducible npm installation | Passed |
| Node core/data/source-coverage tests | 50 passed |
| Python collector/preflight/history/staging tests | 128 passed |
| Astro check | 18 files; 0 errors, 0 warnings, 0 hints |
| Static build | 14 HTML pages plus build.json |
| Generated-output checks | 18 passed |
| Chromium browser tests | 10 passed |
| **Total automated tests** | **206 passed; 39 added in this increment** |

New coverage includes five expected-parent tests, 22 staging tests, nine CLI tests and three actual abrupt-subprocess-termination tests at pre-commit, mid-commit and post-commit boundaries. Existing archive, collector, date, mobile and no-JavaScript tests remain passing. Full CI logs were read; no inference of success was made from a workflow file alone.

Artifact `pilot-verification`, ID **10999353202**, contains the static build, screenshots and lockfile, not private archives. Retention: seven days. ZIP SHA-256: `f3301f859b2812f2a31367aeb39c9942b4935291193bd57beb60731caa0515ac`.
Artifact: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36487323692/artifacts/10999353202

Handoff-only commits after this implementation are checked through their own CI. This record proves the exact implementation above, not later changes.

## Execution and review record

The local isolated workspace contained hash-verified copies of existing Python dependencies, not a full repository clone: direct container GitHub DNS failed. All 39 new tests ran locally; complete regression verification ran in GitHub CI on Python 3.12. The uploaded code and test blobs were compared with the locally tested byte hashes.

Expected-parent tests first failed on the missing argument; staging/CLI tests first failed on absent modules. Author self-review found a pending-file limit that did not reserve temporary/final names: its regression failed before the correction and passed afterward. No existing test was removed or weakened. Actual process-termination tests verify readable prior history and explicit lock recovery after confirming the writer stopped. They do not prove hardware power-loss or network-filesystem durability.

Review was author self-review, not independent approval. No visual/accessibility or field-conditions audit is claimed. Existing Actions-runtime and npm install-script warnings remain maintenance items; no dependency or workflow changes were made.

## Live NPS gate: not rechecked in this increment

The last observed read-only preflight was run **36481482091**, job **109127917904**, at **2026-09-28T20:45:52Z**. It received an empty `NPS_API_KEY`, reported `not_configured`, `gate_passed: false`, `publication_performed: false`, and `checks: []`, and made no API request. This does not establish current secret settings or distinguish absent, misnamed, inaccessible or environment-only configuration.

Once an owner-controlled repository Actions secret named `NPS_API_KEY` is available, rerun the existing read-only preflight and inspect actual provider shapes privately. Never put keys in chat, URLs, source code or issues. See `docs/NPS_PREFLIGHT.md`. No live NPS request or real-response fixture was produced while developing this staging increment.

## Next coherent task

Read the latest PR/head/CI first and preserve newer changes. The collector, archive, semantic differ, data-driven coverage and staging receipt/recovery path now exist; do not rebuild them.

Next implement a validated visitor-facing change-history projection and rendering, initially tested with explicitly synthetic fixtures. Project only verified committed observations; do not expose pending/private state, invent publication times, turn baseline observations into new closures, or interpret removals as reopenings. Keep failed/stale/unknown coverage visible and tie any future exported current snapshot and history to the same accepted observation. Leave production history empty and honestly labeled until actual live collection and source-content review pass.

Persistent operator-controlled storage, private live-source compatibility and reviewed credential-free fixtures are still prerequisites to scheduling. A local staging directory in an ephemeral Actions checkout is not durable hosted persistence. Public-history content review, automatic editorial source-change review, hosting and publication/rollback validation remain separate release gates.

## Limits and inactive capabilities

Trusted local filesystem only. No Windows directory-durability, hardware power-loss, network-filesystem, hostile same-user writer, off-host backup/restore or storage-migration guarantees. Hashes are not signatures. A crash before receipt persistence cannot recover an in-flight response; the old archive remains authoritative and a later collection is a new attempt. Status is a read-only observation, not a cross-process publication transaction. Abandoned locks need explicit operator review; no automatic pruning, lock repair or bulk-removal override exists.

No real public alert/change feed, weather integration, complete permit/road/facility coverage, scheduled collection, deployment, accounts, tracking, advertising, indexing, spending or provider-agreement acceptance was activated. PR #1 remains draft and unmerged. Passing synthetic tests does not establish public-release or live-condition readiness.

## Verification lineage

- Foundation: 79 tests at `7c39fb3` / run 36479129760; handoff `83352bd` / run 36479734880.
- Source coverage: 109 tests at `94bb7af` / run 36482305462; handoff `f232154` / run 36482644929.
- Private history: 167 tests at `f43ee4c` / run 36485050775; handoff `d4eb109` / run 36485585784.
- Staging collection: 206 tests at `afdf98f` / run 36487323692.
