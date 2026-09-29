# Pilot accessibility and reflow implementation plan

> **For agentic workers:** Use superpowers:executing-plans and test-driven-development. Continue the approved pilot acceptance work, not a redesign or new subsystem.

**Goal:** Repair demonstrated keyboard, enlarged-text and readability defects across the 14 production pages, with persistent regression coverage.
**Architecture:** Exercise existing static pages and native controls. Keep changes small and shared; no UI library, tracking, server or alternate data pipeline.
**Stack:** Existing Astro, CSS and Playwright; no new dependencies.
**Authority:** Approved design sections 4/5/12, acceptance criteria 28–35, and the next-task handoff at `b0b9193`.

## Constraints and interpretation

Do not change data, evidence timestamps, collector/preview logic, source rules, credentials, dependencies or workflows. Preserve the light theme, noindex, ads-off and existing branch. No merge or deployment.

Test reflow at 320/640 CSS pixels and doubled root text at 1280/360 pixels. A 320-pixel viewport is the reflow equivalent of 1280 pixels at 400% zoom. These viewport/font changes are not actual browser UI zoom or accessibility certification. Screen-reader, browser and OS coverage remains a manual release check.

Reference guidance: W3C Understanding Reflow https://www.w3.org/WAI/WCAG21/Understanding/reflow ; Focus Visible https://www.w3.org/WAI/WCAG22/Understanding/focus-visible ; WCAG 2.2 Quick Reference https://www.w3.org/WAI/WCAG22/quickref/ . Contrast sampling covers computed opaque backgrounds in this fixed theme, not arbitrary media, opacity or native popups.

## Review focus

Do not hide or shrink information to pass overflow checks. Preserve source links, headings and native form/checklist behavior. Skip navigation must move focus without JavaScript. Current-page announcements must match routes. A styling fix cannot mark unverified data as verified. Private and synthetic previews stay separate.

## Task 1 — probes and failing tests

- [x] Read the current PR and handoff. Base: `b0b919322dfd1dbeff5d8747d115a3ee3e6ca82b`; main unchanged.
- [x] Download and verify run #29 artifact 11009937843, SHA-256 `fd38f237eafa20821062884d3145d53f5822a66e68f262fac9069af5b03b2bbc`.
- [x] Diagnose enlarged-text overflow on the directory, homepage, About and Yellowstone; identify low-contrast labels.
- [x] Commit 38 new browser cases at `53012b7`. Observe failures in run #30, 36514179672, before product repair.

## Task 2 — demonstrated repairs

- [x] Add a readable 19-line stylesheet for flexible children, heading/card-title wrapping and secondary-text contrast. Do not reformat global CSS or hide content.
- [x] Add native main-fragment focus with `tabindex=-1` and correct header/footer current-page announcements.
- [x] Correct helper assumptions for decoration, fragment navigation and the next focusable control on prose-only pages; retain every test case.
- [x] Verify `a0eda54799bd0d50b6c90f004b598f9bc1a83941` in run #31, 36514758211: 105 Node + 158 Python + 18 static + 66 Chromium = 347 passing tests. Astro checks are clean; the build has 14 HTML pages plus build.json.
- [x] Download/hash-verify artifact 11010935329 and inspect representative desktop/enlarged-text screenshots.

## Task 3 — review and handoff

- [x] Self-review the five changed implementation/test/plan files against the base; confirm no data, provider, dependency or workflow changes.
- [x] Record findings, verification and manual limits in `docs/ACCESSIBILITY_REVIEW.md`, `PROJECT_STATUS.md` and the coverage audit. Keep PR #1 draft and unmerged.
- [ ] Verify the documentation-only follow-up CI separately and record it in PR #1.

## Execution ledger

Local scratch used a verified build and offline rendering, not a full clone. Browser HTTP restrictions were not disabled. Full navigation and build verification ran in GitHub CI. No independent reviewer was available.

Run #30, job 109232690783: all Node/Python/static tests passed. Of 66 browser cases, 20 failed and 46 passed. The failing cases were four reflow, fourteen skip-focus, one navigation and one contrast test. All 28 existing browser cases passed; native form/checklist keyboard tests already passed.

**Ruling:** Measure hero content children instead of its decorative pseudo-element; exclude section fragments from page-current assertions; allow the next Tab after main focus to reach the footer when main has no controls. These correct helper assumptions. The first skip test failed before its next-control assertion. Add card-title containment to detect internal clipping independently of document overflow.

Run #31, job 109234464538, tested temporary PR merge `6702652af2db5296580ff23fe3e92e748058703a` and passed all 347 tests. Artifact SHA-256 `88df496b9f0ea3eb8d77d8b422103d1eee12a42d564947b6f1f126dec7841cb0` was verified; representative screenshots were inspected. No production merge, deployment or live-source operation occurred.

**Ruling:** Limit conclusions to tested Chromium states. Actual browser zoom, screen readers, other browsers/OS controls and complete WCAG review remain unverified. Next code work is substantive editorial source-change review, not another accessibility framework or duplicate collection pipeline.
