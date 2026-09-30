# GitHub project Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Verify and release a pilot build compatible with the free GitHub project Pages path.

**Architecture:** Astro's base setting prefixes bundled assets; a shared URL helper prefixes internal navigation. CI retains root and project outputs. Manual release selects a matching verified manifest without rebuilding.

**Tech Stack:** Astro 7, TypeScript, Node 24, Python unittest, Playwright, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-30-pages-base-path.md`

## Global Constraints

- Support `/` and `/us-national-park-trip-readiness-tracker/`.
- Retain manual release/rollback, exact successful main verification and noindex controls.
- Do not publish private data or enable deployment, indexing or advertising.

## Review Focus

- Root and project navigation must both work, including current-page markers.
- Bundled CSS/JS and all generated internal destinations must resolve.
- External URLs and fragment links retain their destinations.
- Release refuses a missing/mismatched project artifact before upload.
- Older root artifacts remain root-only rollback candidates.

### Task 1: Base-aware builds and verified-artifact release

**Files:** Astro config, `src/lib/urls.ts`, layouts/pages/Directory, build manifest, package/CI/Playwright configuration, site/URL/browser/release tests, release/readiness/README/status docs.

**Interfaces:** `siteUrl(path: string, base: string): string` prefixes a root-relative internal URL. Build manifests produce `base_path: string`; release consumes it against the normalized configured Pages path. Output directories remain fixed `dist` and `dist-pages`.

- [x] **Step 1: Write failing URL tests** for root/project paths, external and fragment preservation; run the focused Node test and observe failure.
- [x] **Step 2: Implement base config/helper and navigation**; run focused tests and Astro check with zero diagnostics. The documented CLI `--base`/`--outDir` overrides provide the project configuration without changing root defaults.
- [x] **Step 3: Add failing generated-output checks** for manifest path, all page/asset links, current navigation and both builds; implement dual builds and run 14-page verification for each output.
- [x] **Step 4: Add project-path browser tests** for search/card navigation, entry/checklist interaction, footer and fragment navigation; all four passed in Verify pilot #136 (local browser download unavailable).
- [x] **Step 5: Replace release refusal with artifact matching**, test root/project/missing/mismatched/legacy manifests by executing the workflow script in a synthetic harness; preserve manual/exact-run boundaries.
- [x] **Step 6: Update CI and operator docs**, run full local verification, request independent whole-change review, resolve substantive findings, commit and publish to authorized main, and verify exact-head CI. Code commit `5751fc4` passed Verify pilot #136 with 607 tests. A follow-up preserves root screenshot evidence in the dual browser run; its exact-head CI remains the final artifact-retention check.
