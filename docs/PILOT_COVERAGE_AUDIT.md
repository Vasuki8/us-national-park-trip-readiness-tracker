# Five-park coverage and release acceptance audit

Audit: 2026-09-28 America/Toronto; 2026-09-29 UTC. This is an implementation/source-navigation audit, not a park-conditions report or release approval. Keyboard and reflow follow-through is recorded below and in `docs/ACCESSIBILITY_REVIEW.md`.

## Source-navigation coverage

`data/planning-resources.json` records seven official destinations for each pilot: roads, facilities, camping, accessibility, fees, permits and weather. The 35 park/topic pairs have source titles, original action prompts and absolute `link_reviewed_at` timestamps. The batch completed at `2026-09-29T02:18:54Z`; the interface repair did not advance that time.

These are **links only**, not reviewed operational values. The register contains no open/closed value, fee amount, forecast, exemption, effective period, live check or publication time. It never enters the rule evaluator or rule/feed freshness counts. A link review must not reset another evidence clock.

Source pages were opened and their relevance reviewed through web retrieval, not an independent HTTP uptime measurement. Reviewed redirect destinations were retained; unavailable guessed paths were not treated as evidence. Older seasons, dynamic sections and mixed scopes were not interpreted as current conditions.

| Park | Navigation improvement | Boundary |
|---|---|---|
| Yosemite | Conditions, hours, campgrounds, accessibility, fees, permits/reservations and weather; prompts distinguish intended entrance and road areas. | Entry guidance does not decide Half Dome, wilderness, campsite or route requirements. |
| Rocky Mountain | Dedicated road_status.htm, visitorcenters.htm, camping.htm and all-about-weather.htm, plus accessibility/fees/permits. | Seasonal road text is not a current road status; timed entry does not decide other activities. |
| Yellowstone | parkroads.htm and reviewed operating-dates.htm, plus campground/fee/permit/weather/accessibility pages. | Operating dates are not a verified facility-open flag or booking inventory. |
| Zion | Separate campground and weather-and-climate.htm guidance; prompts direct to activity-specific permits. | General entry is not permission for Angels Landing, The Narrows, The Subway or another activity. |
| Grand Canyon | Separate camping, permits/reservations, hours and weather-condition.htm destinations. | Check the intended rim/elevation; no whole-park road status or forecast is produced. |

Titles identify external resources; prompts are original planning questions, not copied operational notices. No media or NPS marks were added. Link coverage is not clearance to redistribute arbitrary source content or activate advertising.

## Latest observed connection evidence

Read-only NPS preflight run 36481482091, job 109224608968 at `2026-09-29T02:13:16Z` returned `not_configured`, `gate_passed:false`, `checks:[]`, `publication_performed:false`. The runner received an empty `NPS_API_KEY`; no NPS request occurred. A green diagnostic job means execution, not successful live integration. The interface repair did not rerun it.

That rerun used original preflight commit `0dce38beb7c1d9bc3d7feba0d8a69ca1f97ddca7`, not the current application head. It describes the key supplied to that execution, not every present secret setting. Owner setup remains in `docs/NPS_PREFLIGHT.md`.

## Release acceptance state

References are to `docs/ACCEPTANCE_CRITERIA.md`. Grouped evidence does not mean every scenario is complete.

| Area | Evidence available | Remaining requirement |
|---|---|---|
| Collection integrity, 1–6 | Synthetic transport, normalization, pagination, retention and quarantine tests. | Real keyed probe, reviewed credential-free fixtures and live compatibility. |
| Geography/time, 7–15 | Date/area/time tests; notices stay unclassified and future applicability unresolved. | Reviewed area classification and broader access/activity rules before additional determinations. |
| Freshness/history, 16–22 | Synthetic stale/failure behavior, immutable evidence, semantic comparison, recovery and private previews. | Editorial source-change handling, production publication/rollback and durable storage. |
| Weather/fees, 23–27 | Official links and explicit missing integration. | Named-point weather validity/geography and sourced fee components with date/unit/eligibility; no totals claimed. |
| Interface/content, 28–35 | Static, keyboard, mobile and no-JavaScript tests; 38 new cases across all 14 pages cover reflow, enlarged root text, skip focus, navigation and sampled contrast. | Independent screen-reader/cross-browser review, actual browser/OS zoom, native controls, forced colors and comprehensive visual/accessibility acceptance. |
| Publication/monetization, 36–40 | Development remains noindex/ad-free; current and preview data stay separate. | Hosting, persistent storage, actual URL verification, budgets, rollback and publisher/privacy/consent review. |

Neither M1 nor M2 is declared complete. Do not expand to 20 parks or enable ads based on test counts or successful previews alone.

## Verification and follow-through

Planning-source implementation `9588675` passed run #28, 36512665650: 309 tests. The 35 links, link-only scope, preserved alert/history states, checklist navigation and JavaScript-disabled use remain covered.

Interface repair `a0eda54799bd0d50b6c90f004b598f9bc1a83941` passed run #31, 36514758211: 105 Node + 158 Python + 18 static + 66 Chromium = 347 tests. New tests first exposed enlarged-text overflow, skip-focus failures, incorrect current-page annotations and low-contrast labels. The repair preserves content and data. Method, RED/GREEN evidence, helper corrections and screenshots are recorded in `docs/ACCESSIBILITY_REVIEW.md`. Root-font and viewport changes are not actual browser UI zoom or WCAG certification.

Next implement substantive editorial source-change review, retaining the existing evidence/approval boundaries. Once the owner-controlled key is available, use the preflight/staging/preview path to validate real sources. Do not replace completed infrastructure or silently update editorial review timestamps.
