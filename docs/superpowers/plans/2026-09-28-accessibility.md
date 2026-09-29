# Pilot accessibility and reflow implementation plan

> **For agentic workers:** Use superpowers:executing-plans and test-driven-development. Continue the approved pilot interface acceptance work, not a redesign or new subsystem.

**Goal:** Repair demonstrated keyboard, enlarged-text and readability defects across the 14 production pages, with persistent regression coverage.
**Architecture:** Exercise the existing static pages and native controls. Keep layout changes small and shared; do not add a UI library, tracking, server or alternate data pipeline.
**Tech stack:** Existing Astro, CSS and Playwright; no new dependencies.
**Spec:** docs/superpowers/specs/2026-09-28-national-park-trip-readiness-design.md sections 4/5/12; docs/ACCEPTANCE_CRITERIA.md 28-35; PROJECT_STATUS.md at b0b9193, next task.

## Constraints and test interpretation

No data or evidence timestamps, collector/preview behavior, source rules, credentials, dependencies or workflows may change. Keep the light theme, noindex and ads-off state. Stay on the existing feature branch; no merge or deployment.

Test 320 CSS-pixel reflow and a 640 CSS-pixel viewport, plus doubled root text size at 1280 and 360 pixels. A 320-pixel viewport is the reflow equivalent of a 1280-pixel viewport at 400% zoom; changing viewport/root font size is not an actual browser UI zoom or an independent accessibility certification. Full screen-reader/browser/OS coverage remains a manual release check.

References reviewed: W3C Understanding Reflow (https://www.w3.org/WAI/WCAG21/Understanding/reflow), Focus Visible (https://www.w3.org/WAI/WCAG22/Understanding/focus-visible), and WCAG 2.2 Quick Reference (https://www.w3.org/WAI/WCAG22/quickref/). Contrast tests apply computed opaque backgrounds to this fixed theme, not arbitrary media, opacity or OS-native widgets.

## Review focus

Do not fix overflow by hiding or shrinking information. Preserve visible source links, all headings and native form/checklist behavior. Skip navigation must move keyboard focus, including without JS. Current-page announcements must identify the actual route. Layout/contrast changes must not mark unverified data as verified. Keep synthetic/private preview artifacts outside the production upload.

## Task 1 — full-page acceptance probes and RED

- [x] Read current PR and status. Base b0b919322dfd1dbeff5d8747d115a3ee3e6ca82b; main a9d9c19 is unchanged.
- [x] Obtain and SHA-256-verify the exact CI #29 build artifact (11009937843; fd38f237eafa20821062884d3145d53f5822a66e68f262fac9069af5b03b2bbc).
- [x] Diagnose offline: doubled text at 360px overflows homepage/directory cards, About heading and Yellowstone heading. Fixed-theme text scan also identifies insufficient contrast for step numbers, park indices and NPS code labels.
- [ ] Add tests/accessibility.browser.spec.ts and extend the existing Playwright test list; run the actual site through CI before implementing fixes.

## Task 2 — demonstrated repairs only

- [ ] Fix flexible children and heading wrapping without overflow clipping or text reduction, in a small readable stylesheet loaded by Layout.
- [ ] Repair native skip-focus and current-page navigation only where regressions demonstrate the issue. Keep keyboard controls native.
- [ ] Adjust failing fixed-theme text tokens while preserving the light palette.
- [ ] Re-run all new and prior tests, preserve screenshots for representative enlarged-text pages and inspect the final rendered artifact.

## Task 3 — handoff and limits

- [ ] Self-review the complete increment against the base; verify no data/workflow changes.
- [ ] Update PROJECT_STATUS.md, the acceptance audit and this plan with exact CI evidence and remaining manual/live gates. Leave PR draft/unmerged.

## Execution ledger

Full repository execution uses GitHub CI. Local scratch is isolated under /mnt/data/park-a11y-work and contains the verified build artifact, not a full Git clone. Container DNS cannot resolve GitHub and browser HTTP navigation is restricted, so local diagnostics use offline static HTML with its stylesheet embedded and scripts removed. Those diagnoses do not establish actual navigation behavior. Native keyboard and no-JavaScript behavior must pass in the full CI browser.

Ruling: retain a separate compact accessibility/reflow stylesheet rather than reformatting the existing minified global CSS. This limits the reviewed diff and changes only demonstrated properties. No independent reviewer is available; disclose author self-review.
