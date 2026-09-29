# Pilot keyboard, text-resize and reflow review

Review: 2026-09-28 America/Toronto (verification completed 2026-09-29 UTC). This records a bounded engineering review of the current 14-page pilot. It is not a WCAG conformance certification, independent accessibility approval or live-source verification.

## Demonstrated defects and repairs

| Finding | Reproduction | Repair |
|---|---|---|
| Enlarged text overflow | At 360 CSS pixels with root text set to 200%, the home/directory cards, About heading and Yellowstone heading extended outside their viewport. A directory title also extended beyond its card. | Allow card/park-intro flexible children to shrink with `min-width: 0`; allow long H1/card-title text to wrap. No text was hidden or reduced to make the test pass. |
| Skip link did not place focus in main content | The first keyboard Tab reached the skip link, but Enter left `main` unfocused on all 14 pages with JavaScript disabled. | Give the existing main landmark `tabindex="-1"`. This creates a native fragment-focus destination, without inserting an extra sequential tab stop. |
| Incorrect current-page announcement | Explore parks claimed `aria-current="page"` on park-detail routes; current footer pages lacked that attribute. | Compare the actual route for the header link and each footer link. Fragment jumps in history remain section links, not current-page links. |
| Low-contrast secondary text | Computed fixed-theme scans reported small step numbers/code labels below 4.5:1 and large park indices below 3:1. | Reuse the existing darker `--muted` token for these three classes. The light theme and other status colors remain unchanged. |

Changes are isolated to the shared Layout and a 19-line `src/styles/accessibility.css`, imported after the existing global stylesheet. No provider data, rule logic, source timestamps or browser state semantics changed.

## Repeatable browser coverage

`tests/accessibility.browser.spec.ts` adds 38 cases to the existing suite:

- All 14 routes: reflow at widths 320 and 640 CSS pixels; root text set to 200% at widths 1280 and 360. Open evidence disclosures, preserve visible source links and headings, check both document overflow and painted text/selected content boundaries.
- All 14 routes with JavaScript disabled: first-Tab skip-link visibility, Enter moving focus into `main`, next Tab reaching the correct next control (or footer when main has none), native evidence disclosure toggling.
- All pages: language, title, one main/H1, unique IDs, associated native form labels, current-page navigation and absence of positive tabindex; sampled enabled text contrast for the current opaque-background theme.
- All five park forms: native select/checkbox/submit controls, a visible keyboard focus outline on submit, status-region presence, checklist reset and keyboard disclosure toggling.
- Both directories: keyboard search, announced empty state and native state filtering. Reduced motion: animated scrolling disabled.

The tests do not add a third-party accessibility scanner or alter product dependencies. They use the already installed Chromium through Playwright. Existing synthetic-history/private-preview browser checks still run separately and remain passing.

## Verification evidence

Base: `b0b919322dfd1dbeff5d8747d115a3ee3e6ca82b`.
Test-first commit: `53012b706512e778aa329ec4bfa33aff8020fbde`.
Verified repair head: `a0eda54799bd0d50b6c90f004b598f9bc1a83941`.

RED: Verify pilot #30, run 36514179672, job 109232690783. All 105 Node, 158 Python and 18 generated-output tests passed. Chromium reported 20 failed and 46 passed: four reflow cases, fourteen skip-focus cases, the navigation case and the contrast case failed. All 28 pre-existing browser cases passed.

GREEN: Verify pilot #31, run 36514758211, job 109234464538. Temporary PR merge `6702652af2db5296580ff23fe3e92e748058703a` tested the repair against unchanged main. **105 Node + 158 Python + 18 generated-output + 66 Chromium = 347 passing tests.** Astro checked 22 files with zero errors, warnings or hints; the production build still contains 14 HTML pages plus build.json.

Run: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36514758211
Artifact: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36514758211/artifacts/11010935329
Artifact ZIP SHA-256: `88df496b9f0ea3eb8d77d8b422103d1eee12a42d564947b6f1f126dec7841cb0`.

The downloaded artifact hash was verified. Captured desktop and enlarged-text screenshots were inspected for representative directory, About and Yellowstone layouts. CI retains three new full-page 360px/200%-root-text screenshots under the accessibility test directories, plus the existing desktop directory and mobile Yosemite images. This is author visual inspection of selected captures, not a full independent visual audit. Artifact retention is seven days; private archives and candidate preview directories are not included.

## Test-helper corrections

The first probe also revealed three assumptions in the new helpers. The internal-width measurement now checks hero content children instead of counting a deliberately clipped decorative pseudo-element; it additionally checks card-title width. Current-page assertions distinguish fragment jumps from site navigation. After main receives skip focus, the next Tab is allowed to reach the footer on prose-only pages with no main controls. The first RED run failed before reaching that last assertion. These corrections preserve the intended visible-content/focus behavior; no old tests or new test cases were removed.

## Limits and remaining manual checks

A 320 CSS-pixel layout is the reflow-equivalent viewport discussed by W3C for a 1280-pixel viewport at 400% zoom. This suite changes viewport and root font size; it does **not** operate the browser's actual zoom UI or prove every rendered glyph doubles. Screen-reader announcements, browser/OS zoom combinations, Firefox/WebKit, OS-native popup/date controls, forced colors, non-text control contrast, arbitrary opacity/media and a complete WCAG checklist still need separate testing. A status-region attribute is not proof of an assistive-technology announcement.

Reference guidance: W3C Understanding Reflow https://www.w3.org/WAI/WCAG21/Understanding/reflow ; Focus Visible https://www.w3.org/WAI/WCAG22/Understanding/focus-visible ; WCAG 2.2 Quick Reference https://www.w3.org/WAI/WCAG22/quickref/ .

Local diagnostics used a verified CI build in an isolated scratch directory, with styles embedded for offline rendering because local browser HTTP navigation is restricted. No restriction was disabled. Full navigation and build verification took place in GitHub CI. There was no local full-repository clone or independent reviewer. Existing Actions runtime/install-script warnings remain maintenance items.

The next implementation priority is substantive editorial source-change handling using the existing evidence conventions. The API-key, live-source, durable storage, hosting, publication/rollback and advertising gates are unchanged. This pass does not declare M1/M2 or the public pilot release complete.
