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

## Task 1: offline immutable candidate bundle

Files: tracker/preview.py; tests/test_preview_bundle.py.
Interface: make_bundle(HistoryStore, data_kind='unreviewed_source') -> dict, and prepare_bundle(archive_dir: Path, output_dir: Path, data_kind='unreviewed_source') -> Path. Fixed inventory yose/romo/yell/zion/grca; exact snapshot/history pairs from project_history. Canonical UTF-8 JSON, maximum 10 MiB; digest names final file. Output is separate from archive and protected repository directories, bounded to 128 entries/64 MiB including temporary reservation. No overwrite or auto-pruning. Explicit synthetic flag exists only for test construction, never approval.
- [ ] Write tests, observe RED, implement, verify GREEN and commit.
- [ ] Verify original archive/input files unchanged, corrupt source rejection, exact retries and interruption recovery.

## Task 2: strict loading and isolated build preparation

Files: scripts/preview-bundle.ts; scripts/preview-workspace.mjs; scripts/build-preview.ts; tests/preview-bundle.test.ts; tests/preview-workspace.test.ts.
Interface: validatePreviewBundle(value) and readPreviewBundle(path); createWorkspace(projectRoot), workspacePaths(projectRoot,workspace), writeReady(projectRoot,workspace,manifest). Fixed ignored parent .superpowers/preview-builds; fresh workspace per attempt; never production dist. Read canonical bytes with bounds, reject unknown/duplicate fields and mismatched content hash, validateHistory for each park. Local Astro only; build subprocess gets an allowlisted environment without API credentials or arbitrary Node options. A ready marker is atomic and written only after successful build/output checks. Failed workspaces remain unready for inspection.
- [ ] Write tests, observe RED, implement and verify GREEN.
- [ ] Test symlinks, unsafe destinations, output validation, partial readiness and prior-build preservation.

## Task 3: complete candidate-to-page preview and verification

Files: preview/astro.config.mjs; preview/src/lib/bundle.ts; preview/src/pages/index.astro; preview/src/pages/preview.json.ts; tests/build_preview_fixture.py; tests/preview.browser.spec.ts; playwright.config.ts; docs/PREVIEW_BUNDLES.md; PROJECT_STATUS.md.
Separate preview root requires its generated workspace. It cannot silently use committed production data. Display a persistent candidate/not-published notice, identity, per-park check times/current records and shared timelines. Do not claim a simultaneous five-park observation. The fixture generator uses real archive/projection code; browser tests build and serve the actual preview, not a hand-built HTML mock. No private candidate artifacts are uploaded by existing CI.
- [ ] Add failing end-to-end tests and implement the preview root.
- [ ] Verify successful/failed/quarantined/empty states, source markup escaping, 360px/no-JavaScript use and production isolation.
- [ ] Run full CI, self-review changes, update handoff/PR; leave PR draft and unmerged.

## Execution ledger

Base: 0a32079a96f8106e1427b19a4aa9699e7eaffc4e. Current PR and handoff read; scope continues the approved preview task. Direct container GitHub DNS is unavailable. Remote feature-branch commits and GitHub CI provide the full-repository test environment; do not claim a local full clone or local full-suite verification. No independent subagent reviewer is available.
Pre-flight: Task 1 produces canonical envelope consumed by Task 2; Task 3 reads only the frozen workspace copy through the same validator. Per-park head consistency is required; a simultaneous cross-park transaction is not claimed. Any broken build remains private and unready, not a production fallback.
