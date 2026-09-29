# Private preview-bundle implementation plan

> **For agentic workers:** Use superpowers:executing-plans and test-driven-development for this continuation.

**Goal:** Inspect candidate snapshots and their histories together without changing production data or treating a preview as a release.
**Architecture:** An offline Python command projects all five committed park histories into one immutable, content-addressed candidate JSON file. A TypeScript validator checks the envelope and existing snapshot/history contracts. An explicit local build command creates a unique ignored workspace and uses a separate Astro root with the production timeline component. Only a completed, verified build receives a ready marker.
**Tech stack:** Existing Python/uv, Node/TypeScript, Astro and Playwright; no dependencies or services added.
**Spec:** docs/superpowers/specs/2026-09-28-national-park-trip-readiness-design.md, sections 7-9 and 12; PROJECT_STATUS.md at 0a32079, next-task contract.

## Global constraints

No NPS request, credential lookup, source-review refresh, scheduler, production-data replacement, deployment, indexing, ads or spending. Archive and staging schemas remain unchanged. Candidate generation is not content approval. Preserve failed/quarantined states and last-good timestamps. Baselines are not new closures; removals are not reopenings. No publication timestamp is invented.

## Review focus

- Mixed snapshot/history heads, wrong parks and rewritten clocks must fail before building.
- Interrupted writes/builds must not produce a completed candidate or ready preview.
- Source/Git/production output paths, symlinks and overwritten files must be refused.
- Pending records, local archive paths, credentials and synthetic previews must not enter production assets.
- Empty, failed, stale and quarantined data must remain explicit in rendered previews.

## Task 1: offline immutable candidate bundle — complete

Files: tracker/preview.py; tests/test_preview_bundle.py.
Interface: make_bundle(HistoryStore, data_kind='unreviewed_source') -> dict, and prepare_bundle(archive_dir: Path, output_dir: Path, data_kind='unreviewed_source') -> Path. Fixed inventory yose/romo/yell/zion/grca; exact snapshot/history pairs from project_history. Canonical UTF-8 JSON, maximum 10 MiB; digest names final file. Output is separate from archive and protected repository directories, bounded to 128 entries/64 MiB including temporary reservation. No overwrite or auto-pruning. Synthetic construction is for tests, not approval.
- [x] Commit tests before implementation; observe missing exporter failure; implement and verify the 15 new Python cases.
- [x] Verify archive/input preservation, corrupt-source rejection, exact retries and failed-install recovery.

## Task 2: strict loading and isolated build preparation — complete

Files: scripts/preview-bundle.ts; scripts/preview-workspace.mjs; scripts/build-preview.ts; tests/preview-bundle.test.ts; tests/preview-workspace.test.ts; tests/build-preview.test.ts; tests/preview-io.test.ts.
Interfaces: validatePreviewBundle(value), readPreviewBundle(path), createWorkspace(projectRoot), workspacePaths(projectRoot,workspace), writeReady/readReady, buildPreview(input,runner). Fixed ignored parent .superpowers/preview-builds; fresh workspace per attempt; never production dist. Bounded strict envelope/pair validation; installed Astro and allowlisted child environment. Ready only after successful build/output checks.
- [x] Commit Node contracts before implementations and verify them in CI.
- [x] Test unsafe destinations, symlinks, partial readiness, output identity, frozen inputs, failure handling and environment isolation.
- [x] Reproduce actual named-pipe blocking before the regular-file precheck repair; verify the subprocess regression passes.

## Task 3: complete candidate-to-page preview and verification — complete

Files: preview/astro.config.mjs; preview/src/lib/bundle.ts; preview/src/pages/index.astro; preview/src/pages/preview.json.ts; tests/build_preview_fixture.py; tests/serve-preview.ts; tests/preview.browser.spec.ts; playwright.config.ts; docs/PREVIEW_BUNDLES.md; PROJECT_STATUS.md.
The separate preview root requires its generated workspace. It never silently uses committed production data. Persistent not-published labeling, identity, current records and matching timelines remain explicit. The synthetic generator uses the real archive/export/build path. Existing CI does not upload private candidate artifacts.
- [x] Commit end-to-end test contracts before the preview implementation; diagnose real build startup failures rather than bypassing the build.
- [x] Verify successful/failed/quarantined/empty states, source escaping, 360px/no-JavaScript use and byte-for-byte production isolation.
- [x] Run full CI, self-review and prepare the handoff/PR update. Leave PR draft and unmerged.

## Execution ledger and rulings

Base: 0a32079a96f8106e1427b19a4aa9699e7eaffc4e. Connected GitHub branch and CI were the full-repository execution environment; no local full-clone/test claim. No independent subagent reviewer was available.
Pre-flight: Task 1 produces the envelope validated by Task 2; Task 3 reads the frozen workspace copy. Per-park head consistency is required; a simultaneous five-park transaction is not claimed.

CI #19 (36509634326): prior 67 Node tests passed, new preview modules absent. CI #20 (36509825545): 87 Node tests passed, new Python exporter absent. CI #21 (36510035416): new build-driver tests exposed the missing module. These are recorded missing-module failures, not invented behavioral assertion results.

CI #22 (36510252837) and #23 (36510494661) passed 92 Node, 158 Python, 18 static tests and the production build; real candidate startup failed before browser assertions. The synthetic-only diagnostic identified source-relative import.meta.url relocating into Astro's prerender chunks. Ruling: use the repository cwd explicitly pinned by the build driver; retain all workspace path checks and no production fallback.

Author review added the named-pipe regression. CI #24 (36510678885) reproduced a blocked reader with a real child-process timeout; all 92 other Node tests passed. Ruling: check regular-file type before open, then verify descriptor identity. Trusted local filesystem is still the boundary; no hostile same-user race-proof claim.

**Full verification: CI #25, run 36510906825, head 7d7fdcbc28d13f70ad2452f973099825527fca61, job 109222573069.** Temporary PR merge 3f1311f7b0b369e9ad7fc98ade08364379804985 against unchanged main. **93 Node + 158 Python + 18 static + 24 Chromium = 293 passing tests.** Astro: 21 files, zero errors/warnings/hints. Production build: 14 pages plus build.json. The actual isolated preview built and served successfully, and the before/after production file comparison passed. Full logs read. Artifact 11008868862 contains production outputs, not private preview workspaces.

Final review: author self-review. No existing test was removed or weakened. Existing runtime/install-script maintenance warnings remain deferred. The final documentation-only update requires its own CI check.

Next: live NPS preflight and pilot acceptance/coverage checks using the existing staging/preview path; persistent storage, source-content review, hosting and rollback remain gates. Do not reimplement these completed layers or activate a scheduler merely because a preview succeeds.
