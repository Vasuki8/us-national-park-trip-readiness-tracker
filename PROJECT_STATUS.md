# Project status and handoff

Updated: 2026-09-28 America/Toronto (verification completed 2026-09-29 UTC). **Offline candidate bundles and isolated rendered previews are implemented and CI-verified. The public pilot release remains incomplete.**

Repository: `Vasuki8/us-national-park-trip-readiness-tracker`.
Branch: `feat/pilot-foundation`. Draft PR: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/1
Main remains `a9d9c19e8307828c5bdb6f331e24ca3fe7afffce`. No merge or production deployment was performed.

## Standing direction and preserved product

AdSense-first eventual public product, light theme, no paid data dependency. Validate five parks before expanding to 20. Trustworthy displayed data precedes indexing and advertising. Never infer an all-clear, reopening, permit exemption or annual validity from missing information.

The production build remains 14 HTML pages plus build.json, with park/state search, five park pages, source panels, self-reported checklists and visitor-facing history. All five parks have entry-source evidence; only Yosemite and Rocky Mountain have dated rules. The other three parks have undated observations, not executable annual rules. Source, human review, effective, collection, build and publication clocks remain distinct.

Existing collection, private evidence archive, semantic comparison, staging receipts/recovery, history projection and timeline components are unchanged. This increment adds a separate inspection path, not a replacement implementation. All committed public alert snapshots remain `never_checked`; all committed public histories remain empty. No editorial or public-data timestamp was advanced.

## New: offline candidate-to-preview path

- `tracker/preview.py` prepares a fixed five-park bundle using the existing verified archive reader and history projector. Each current snapshot and history comes from the same committed per-park observation. Different parks need not have been checked simultaneously; no global observation or publication timestamp is invented.
- Candidate files are canonical JSON with a content-derived identity. Preparation is offline, does not change the archive and excludes pending receipts/private archive internals. Equal retries reuse the same file; conflicting existing bytes are not overwritten. A candidate is marked `private_preview`, not approved or published.
- Output is separate from archive/source/site/Git paths, bounded to 10 MiB per bundle and 128 entries/64 MiB per candidate directory, including temporary reservations. Exclusive preparation locks and atomic file installation prevent partial temporary files from becoming completed candidates. Abandoned locks require operator review; nothing is automatically pruned.
- `scripts/preview-bundle.ts` checks the envelope, exact five-park inventory, content digest and existing strict snapshot/history contracts. Unknown fields, altered evidence, mismatched pairs, noncanonical JSON text, oversized input and symlinks are refused. Non-regular files are rejected before open, preventing a named-pipe input from blocking the reader.
- `scripts/build-preview.ts` validates input before creating a unique `.superpowers/preview-builds/run-.../` workspace. It freezes the bundle, invokes the installed Astro binary with a separate `preview/` root and an allowlisted child environment, and never targets production `dist/`. No NPS credentials or arbitrary Node options are inherited by the build child.
- A completed preview requires a successful actual build, matching output identity and noindex HTML before an atomic `ready.json` marker is installed. A failed attempt stays unready; it never returns an earlier output as its own success. Serving requires the ready marker and is documented for loopback-only use.
- The new candidate page displays an explicit persistent **Not published** warning, bundle identity, current candidate records, per-park collection states and the existing source-backed timeline. Failed/quarantined checks retain original successful-check times. Source markup remains escaped. The input bundle and private archive are not the web root.

Commands, limits and recovery: `docs/PREVIEW_BUNDLES.md`.
Plan: `docs/superpowers/plans/2026-09-28-preview-bundle.md`.

## Verified implementation

Code/test head: **`7d7fdcbc28d13f70ad2452f973099825527fca61`**.
**Verify pilot #25, run 36510906825, completed successfully.** Job **109222573069** tested temporary PR merge **`3f1311f7b0b369e9ad7fc98ade08364379804985`** against unchanged main. This is a CI test merge, not an actual merge into main.
Run: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36510906825

| Check | Verified result |
|---|---|
| Reproducible npm installation | Passed |
| Node core/data/history/preview tests | 93 passed, 0 failed |
| Python collector/archive/staging/projection/preview tests | 158 passed |
| Astro check | 21 files; 0 errors, 0 warnings, 0 hints |
| Production static build | 14 HTML pages plus build.json |
| Generated-output tests | 18 passed |
| Chromium browser tests | 24 passed |
| **Total automated tests** | **293 passed; 47 added in this increment** |

The six new browser tests use a real synthetic archive, Python candidate export, TypeScript validation, actual isolated Astro build and the production history component. They verify five-park rendering, failed/quarantined/empty states, metadata identity, source-text non-execution, no-JavaScript evidence, 360px expanded layouts, and no candidate routes/notices on the production server. The harness compares every production `data/` and `dist/` file before and after preview generation; they remain byte-for-byte unchanged.

Artifact `pilot-verification`, ID **11008868862**, contains the production build, existing browser screenshots and lockfile, not private candidate bundles or preview workspace outputs. Seven-day retention. ZIP SHA-256: `577cfeb6c304f8251e22a40186fdb2e8f062d255891ac05dec22108a34a8da83`.
Artifact: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36510906825/artifacts/11008868862

The final handoff/plan update changes documentation only and is checked through its own CI. This recorded result proves the exact implementation above, not future edits.

## Execution and review record

This continuation used the connected GitHub feature branch and full GitHub CI as its execution environment; direct container GitHub DNS was unavailable. No local full clone or local full-suite verification is claimed. Seven implementation/test commits from `0a32079` changed 19 files; production data, existing `src/`, collector/archive/staging implementations, dependencies and workflow files were preserved. Only Playwright configuration was extended to start the separate candidate test server.

New tests were committed before their implementations. Run #19 failed on missing preview modules; #20 passed the new Node contracts and exposed the missing Python exporter; #21 exposed the missing build driver. Runs #22 and #23 passed Node/Python/static checks but failed during real preview startup before browser assertions. Synthetic-only diagnostics traced the failure to source-relative `import.meta.url` being relocated into Astro prerender chunks. The loader now uses the repository working directory explicitly pinned by the build driver.

Author self-review identified a possible hang when opening a named pipe before checking its type. Run #24 reproduced that behavior with an actual subprocess and timeout. The reader now checks regular-file type before open and verifies descriptor identity afterward; #25 passed that regression and all 293 tests. No existing assertion was removed or weakened. Earlier startup failures must not be described as observed failures of individual browser assertions.

Review was author self-review, not independent approval. No comprehensive accessibility/visual, field-conditions or adversarial filesystem audit is claimed. Existing Actions runtime deprecation and npm install-script warnings remain non-blocking maintenance items; no dependency upgrades were made.

## Live NPS and public-release requirements

No live NPS request, credential lookup or key-configuration recheck was performed in this increment. The last observed preflight remains run **36481482091**, at **2026-09-28T20:45:52Z**, which received an empty `NPS_API_KEY`, made no requests and reported `gate_passed: false`. That historical result does not establish current secret settings.

Before actual live ingestion, rerun the existing read-only preflight with an owner-controlled private Actions secret and inspect provider shapes privately. Never put keys in chat, URLs, source code or issues. Setup and interpretation remain in `docs/NPS_PREFLIGHT.md`.

No production promotion command, live public alert/history feed, collection schedule, deployment, advertising, analytics, accounts, indexing, spending or provider-agreement acceptance was activated. Successful preview preparation is not source-content approval, live-source compatibility or public-release readiness.

## Next coherent task

Read the latest PR/head/CI first and preserve newer work. Collection, archival, staging recovery, visitor history and candidate preview now exist; do not rebuild these layers.

Move to the live-source and pilot-release acceptance checks. First rerun the existing read-only NPS preflight rather than continuing to assume the old missing-key result is current. If a key is available, validate actual provider shapes privately, retain reviewed credential-free fixtures, and use the existing staging/preview path for inspection. If the preflight is still blocked, record that exact diagnostic and advance the official-source coverage/acceptance audit for the five pilot pages without inventing data or adding another duplicate pipeline.

Resolve operator-controlled persistent archive storage and production hosting before scheduling. Preview build directories and ephemeral Actions checkouts are not durable hosted archives. Source-content review, automatic editorial source-change review, complete permit/road/facility coverage, publication/rollback tests and owner-controlled hosting setup remain release requirements. Do not expand to 20 parks or activate advertising before the pilot meets its acceptance criteria.

## Limits and lineage

Trusted local filesystem and trusted application dependencies are assumed. No hardware power-loss, Windows-directory, network-filesystem, hostile same-user mutation or off-host backup guarantee is made. Digests are consistency checks, not signatures or permission to redistribute. The ready marker validates this local build's identity/noindex completion, not a signed digest of every output asset. `noindex` is not access control; keep the candidate server private. Abandoned locks and disposable-workspace cleanup require explicit operator review.

Prior verified totals: foundation 79; source coverage 109; private history 167; staging 206; visitor history 246 at `70322a54` / run 36508305834 and handoff `0a32079` / run 36508571989. The 293-test preview result is recorded above. PR #1 remains draft and unmerged.
