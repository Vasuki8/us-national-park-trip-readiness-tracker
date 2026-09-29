# Five-park coverage and release acceptance audit

Audit date: 2026-09-28 America/Toronto (2026-09-29 UTC). This is an implementation/source-navigation audit, not a park-conditions report or release approval.

## What changed

`data/planning-resources.json` records seven official planning destinations for each pilot: roads, facilities, camping, accessibility, fees, permits and weather. The 35 park/topic pairs have source titles, original action prompts and an absolute `link_reviewed_at` timestamp. The review batch completed at 2026-09-29T02:18:54Z.

These are **links only**. A relevant destination is not a reviewed operational value. The register contains no open/closed value, fee amount, forecast, permit exemption, effective period, live check or publication timestamp. It never enters the entry-rule evaluator or the rule/feed freshness counts. A new link review must not reset any other evidence clock.

The source pages were opened and their relevance reviewed through web retrieval. This is not an independent direct-HTTP uptime measurement. Where retrieval showed a redirect, the reviewed destination was retained; an unavailable guessed path was not retained as evidence. Some pages contain older seasons, dynamic sections or mixed scopes. No current road/facility status was inferred from them.

## Source-navigation inventory

The complete URLs and page titles live in the machine-validated register; this table highlights why a generic park-planning link was insufficient.

| Park | Navigation improvement | Boundary |
|---|---|---|
| Yosemite | Conditions, hours, campgrounds, accessibility, fees, permits/reservations and weather pages; road prompt names intended entrance and road areas. | Entry guidance does not decide Half Dome, wilderness, campsite or route requirements. |
| Rocky Mountain | Dedicated `road_status.htm`, `visitorcenters.htm`, `camping.htm` and `all-about-weather.htm`, alongside accessibility/fees/permits. | Do not turn mixed seasonal road text into a current road status or extrapolate a timed-entry result to other activities. |
| Yellowstone | `parkroads.htm` and the reviewed `operating-dates.htm` destination, with separate campground/fee/permit/weather/accessibility pages. | Operating dates are not a verified facility-open flag or booking inventory. |
| Zion | Separate campground and `weather-and-climate.htm` guidance; prompts direct visitors to activity-specific permit instructions. | A general-entry result is not permission for Angels Landing, The Narrows, The Subway or another activity. |
| Grand Canyon | Separate camping, permits/reservations, operating hours and `weather-condition.htm` destinations. | Check the intended rim/elevation; no whole-park road status or forecast is produced. |

The source titles identify external resources. The action prompts are original planning questions, not copied operational notices. No media or NPS marks were added. This narrow link register is not clearance to redistribute arbitrary source content or to activate advertising.

## Latest live-connection evidence

Reran the existing read-only NPS preflight, run `36481482091`, latest job `109224608968`. At `2026-09-29T02:13:16Z`, it returned `status: not_configured`, `gate_passed: false`, `checks: []`, `publication_performed: false`. The runner received an empty `NPS_API_KEY`; no NPS request was made. The diagnostic job's green status means it executed, not that live integration passed.

The rerun checked out original preflight commit `0dce38beb7c1d9bc3d7feba0d8a69ca1f97ddca7`. It did not run the current application head. This is a new diagnostic of the key supplied to that workflow, not an inspection of all repository/environment secret settings. See `docs/NPS_PREFLIGHT.md` for the owner-controlled setup path.

## Release acceptance state

References are to `docs/ACCEPTANCE_CRITERIA.md`; grouped evidence is not a claim that every scenario in a group is complete.

| Acceptance area | Evidence available | Remaining requirement |
|---|---|---|
| Collection integrity, 1-6 | Existing synthetic transport, normalization, pagination, retention and quarantine tests. | A real keyed source probe, reviewed credential-free response fixtures and live-shape compatibility. |
| Geography/time, 7-15 | Existing date/area/time tests; notices stay unclassified and future applicability unresolved. | Reviewed area classification and broader activity/access rules before making additional determinations. |
| Freshness/history, 16-22 | Synthetic stale/failure behavior, immutable evidence, semantic comparison, staged recovery and private preview tests. | Automatic editorial source-change handling, production publication/rollback drills and durable operator storage. |
| Weather/fees, 23-27 | Relevant official links and explicit missing integration. | Named-point weather validity/geography and sourced fee components with date/unit/eligibility. No total-price calculator is claimed. |
| Interface/content, 28-35 | Meaningful static pages and keyboard/mobile/no-JavaScript tests; new cards have dedicated browser assertions. | Independent accessibility/visual review and comprehensive browser-zoom/reflow acceptance. Doubling root text size within one component is not a full zoom audit. |
| Publication/monetization, 36-40 | Development remains noindex/ad-free; current and preview data stay separate. | Owner-controlled hosting and persistent storage, actual URL verification, publication budgets, rollback, publisher/privacy/consent review. |

The register improves the visible coverage-gap path, not collected operational coverage. Neither M1 nor M2 is marked complete by this increment. Do not expand to 20 parks or enable advertising on the strength of test counts or a successful preview alone.

## Verification and follow-through

Implementation `9588675aa616a3e24acafdf71760ef57ddec3f39` passed Verify pilot #28, run `36512665650`: 105 Node + 158 Python + 18 static + 28 Chromium = 309 tests. The four new browser cases were observed failing on missing UI in run #27 before implementation, then passed without assertion changes. All 24 existing browser cases remain passing. The 35 source links, link-only scope, unchanged alert/history states, native checklist jump, JavaScript-disabled use, normal 360px page layouts and doubled text within the new component are covered.

Configure the private Actions key through the owner's normal settings process, then rerun the existing probe. Use the already-built collector/archive/staging/preview path once real-source prerequisites are met; do not add another pipeline. In the meantime, finish outstanding accessibility/reflow acceptance and substantive source-change detection separately. Keep public operational claims bounded by their actual evidence and release requirements.
