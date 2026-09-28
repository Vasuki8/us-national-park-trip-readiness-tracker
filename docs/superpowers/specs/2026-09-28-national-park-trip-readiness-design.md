# U.S. National Park “Trip Readiness” Tracker
## Product and architecture specification — 28 September 2026

**Approval addendum:** The owner approved the kickoff design and authorized development in `Vasuki8/us-national-park-trip-readiness-tracker` on 28 September 2026. The original kickoff scope below remains the target, not a claim that every feature has been delivered. Current implementation, verification and remaining gates are in `PROJECT_STATUS.md`.

## 1. Product purpose

Help a traveler answer: **“For my park, dates, arrival time, and planned areas, what could prevent or materially change my visit—and what do I still need to check?”**

The owner's established objectives are a public product with Google AdSense as the primary revenue model, substantial monthly visitor traffic, and no paid data-commercialization licence in the core dependency chain. The website should use a light theme. The government-exam/scholarship dashboard is a separate project and is not included here.

Proposed audience: independent U.S. national-park visitors, including road-trip travelers, families, and international visitors. This audience selection is a product assumption, not measured demand. Traffic, search rankings, advertising approval, and revenue are not established.

Success for the first release means useful, source-traceable trip decisions—not the largest number of park pages. The product is a planning aid, not an emergency-warning system or a declaration that a trip is safe.

## 2. Approaches considered

**A. Static park directory with an alert feed.** Cheapest and fastest, but weak differentiation and too easy to become copied-source content. Useful as a foundation, not the whole product.

**B. Source-backed readiness pages, a date-aware checklist, and change history — recommended.** Combine structured official data with reviewed rules and original explanations. Keep the site static-first, with small browser-side interactions. This adds real utility without requiring paid map, booking, or AI services.

**C. Full booking, routing, and real-time availability platform.** Defer. It introduces additional rights reviews, provider dependencies, misleading-availability risk, support work, and ongoing costs before the core audience has been validated.

The proposed first implementation covers option B in a narrow pilot. It does not include an automated travel agent or account system.

## 3. Coverage and release boundary

The launch target remains **20 national parks**. Prove the data model on **five pilot parks** first: Yosemite, Rocky Mountain, Yellowstone, Zion, and Grand Canyon. These are proposed test cases, not a claimed visitation ranking. Their detailed source audits have not all been completed.

The remaining 15 should be selected using the official 2025 recreation-visit data, filtered to the national-park designation and checked for combined reporting units. The latest complete annual release was identified, but a verified top-20 export was not obtained in the kickoff [S09]. Do not label an arbitrary selection “the 20 most visited.”

Do not automatically include every NPS unit: parkways, monuments, recreation areas, and national parks are not interchangeable categories. Preserve official park identifiers and separately model visitor areas when one administrative unit represents multiple destinations.

### Pilot page contract

Each pilot gets one useful canonical readiness page containing:

- A park/date/arrival-time/area selector, with optional inputs clearly marked.
- Official alerts grouped by affected area and type, with unresolved classification preserved.
- Entry, vehicle-access, parking, and activity-permit requirements kept separate.
- Roads, visitor centers, campground operations, accessibility notes, hours, and fee information only where supported; otherwise a visible coverage gap and official link.
- A trip checklist, a source-observation change history, and links to authoritative park guidance.
- A weather section only after the location and freshness checks pass; until then it links to official weather guidance.

**Not in the pilot:** campsite or permit inventory, booking, accounts, payment collection, paid APIs, Google Maps, route optimization, real-time crowd estimates, user-generated condition reports, AI-generated safety judgments, email/push subscriptions, or active advertising scripts.

## 4. Information architecture and visual direction

Working project identifier: `national-park-trip-readiness`. No domain, brand availability or trademark clearance is implied. The authorized repository is `Vasuki8/us-national-park-trip-readiness-tracker`.

| Route | Purpose |
|---|---|
| `/` | Explain the tool, find a covered park, expose data freshness |
| `/parks/` | Search and filter the covered inventory |
| `/parks/{slug}/` | Canonical park readiness page |
| `/changes/` | Observed additions, edits, and removals across covered parks |
| `/how-it-works/` | Explain sources, freshness, coverage limits, and checklist logic |
| `/sources/` | Human-readable source and rights register |
| `/about/`, `/privacy/`, `/terms/`, `/corrections/` | Ownership, disclosures, and correction process |

Comparison and saved-park screens are a later increment, after the five-park pilot passes. Do not create every possible date or comparison as an indexable URL.

Use an off-white background, dark readable text, restrained forest-green accents, generous spacing, and mobile-first cards. The top of a park page should show the visitor's selections, important unresolved requirements, and freshness before decorative content. Status must be understandable without color. Use accessible native controls and visible keyboard focus.

No photography is necessary for the first release. Original CSS decoration avoids making image permissions a launch dependency. Do not imitate the NPS arrowhead or imply official affiliation.

## 5. Readiness semantics

Do not produce a 0–100 readiness score or a blanket green “safe/open” badge. Show separate dimensions:

| Dimension | Examples of valid states |
|---|---|
| Published restrictions | Restriction reported; no matching item in the checked feed; coverage incomplete |
| Required visitor action | Applies; does not apply under this rule; more information needed; not verified |
| Checklist completion | Not reviewed; reviewed by traveler; action marked complete by traveler |
| Evidence freshness | Within review window; stale; collection failed; never checked |

A traveler marking an item complete is not verification that a reservation exists. If all checks are marked complete, use “Your checklist is complete,” never “Your trip is guaranteed” or “The park is safe.”

An empty successful alerts response means only that the checked feed returned no alerts for the requested scope. A failed request is not an empty successful response. A removed alert means “no longer present in the checked feed,” not “road reopened.” A facility-level closure must not close the entire park in the UI.

### Date and rule evaluation

A requirement record must specify its applicable year or date interval, park-local timezone, daily time interval, affected area, activity or travel mode, exceptions, and evidence. An unknown year is not permission to reuse a prior-year rule.

Trip date selection filters explicit effective periods. Current notices without enough timing information remain visible as “current notice; applicability to your dates not confirmed.” Do not project current closures into a future trip or imply they will be resolved.

The reviewed sources demonstrate why specificity matters: Yosemite's entrance-reservation page says it is not using a timed-entry system in 2026 [S06]. Rocky Mountain publishes different 2026 dates and daily windows for general access and Bear Lake Road [S07]. Neither observation settles camping or activity-permit requirements.

Long or ambiguous rules need reviewed normalization. Automated extraction may propose a change, but must not silently publish a new “not required” determination. Unknown inputs produce an unresolved result rather than a guessed exemption.

## 6. Sources and content rights

**Core sources:** the NPS API for covered structured information, reviewed official park pages for rules and operational details, and NWS for supported weather products. NPS registration is free and requires a private API key [S02–S03]. NWS describes its API information as open data free to use for any purpose [S05].

NPS-created government material is generally reusable subject to its published ownership policy, applicable law, and content-specific rights. This is not a blanket licence for every item appearing on an NPS site. Third-party text, photographs, maps, donor materials, and official marks need separate review [S04].

Proposed initial policy: publish source-linked facts and original summaries of reviewed government-authored material; exclude unreviewed third-party media. Keep source acknowledgments and an appropriate notice such as “No claim to original U.S. Government works.” Use a clear independent/non-endorsed disclosure. This is a technical source review, not a legal clearance opinion.

Link users to official reservation pages. Recreation.gov/RIDB ingestion and availability are deferred until their specific terms, endpoints, and permitted uses are reviewed. A discoverable endpoint or freely visible webpage is not sufficient permission.

NPS fee rules require their own effective dates and units. Central guidance includes nonresident fees for specified parks [S08]; do not show one universal vehicle price as the total cost for every party. The pilot presents sourced components and limitations, not an unverified all-in calculator.

## 7. Technical architecture

**Frontend:** Astro static generation, TypeScript for limited browser interactions, and lightweight CSS. Produce meaningful HTML before JavaScript. The Astro documentation covers Cloudflare deployment [S16]. Pin exact supported versions during implementation, after checking the then-current documentation.

**Collector and validation:** Python managed with `uv`. Separate provider adapters, normalization, rule evaluation, semantic diffing, evidence storage, and publication validation. The collector must run independently of the frontend build and accept a deterministic clock in tests.

**Automation target:** GitHub Actions collects and validates official data, then builds and deploys an immutable snapshot. Keys stay in Actions secrets, never in browser JavaScript, public files, source URLs, or logs. Use an application-identifying User-Agent where required, rate-aware retries, bounded timeouts, and caching. This is a target, not an enabled schedule.

**Production-host candidate:** Cloudflare Pages. Keep GitHub for source control and automation; do not assume GitHub Pages is suitable for running an advertising business given its published restrictions [S13]. Review and accept the selected host's terms through the owner's normal account process before publishing [S15].

**Initial refresh design:** run a shared collection/build cycle every two hours, offset from the top of the hour. Twelve runs a day produce at most 372 scheduled builds in a 31-day month, leaving 128 of the currently documented 500-build allowance for code changes, retries, and previews [S14]. This is a proposed budget, not a configured schedule or an SLA. Do not enable both automatic Git builds and redundant direct-upload deployments for the same change.

Use controlled concurrency and month-to-date budget checks. Metadata can refresh daily within the shared cycle. Rebuild freshness status even when underlying facts do not change. GitHub documents possible schedule delays [S17], so display actual successful collection and publication times.

The first release is a periodically refreshed planning product. It must not claim live warnings. Faster refreshes can later use a separate data-delivery path or Workers Static Assets after limits and costs are evaluated [S18]; that is not necessary for the pilot.

No production database is required initially. Keep current normalized snapshots, a compact append-only semantic change log, and small content-addressed evidence excerpts. Do not commit full HTML responses every two hours. Define retention and storage limits before expanding coverage; hashes alone are not sufficient evidence to reconstruct a claim.

## 8. Evidence and provenance contract

| Field | Meaning |
|---|---|
| `provider`, `source_url`, `source_record_id` | Origin and stable source identity; record ID may be null |
| `park_id`, `area_id`, `subject_type` | Geographic and topical scope |
| `source_published_at`, `source_updated_at` | Source-provided times only; null if absent |
| `effective_from`, `effective_to`, `timezone` | When the claim applies, distinct from collection |
| `last_checked_at`, `last_successful_fetch_at` | Actual collection attempt and success |
| `reviewed_at`, `review_status` | Human/curation state for normalized rules |
| `observed_first_at`, `observed_changed_at` | This tracker's own history, not the event's true start |
| `snapshot_id`, `published_at` | The website release that displayed the claim |
| `content_hash`, `evidence_excerpt` | Deduplication/integrity and the supporting text |
| `value`, `unit`, `qualifiers` | Facts without losing per-vehicle/per-person or other distinctions |
| `rights_basis`, `rights_reviewed_at` | Scope and date of the content-use review |
| `collection_status`, `coverage_status` | Success is not the same as completeness |

Do not store a collection timestamp in a field labeled “NPS updated.” Do not use a page footer's general revision date as the effective date for every claim. Preserve conflicts instead of silently preferring whichever source fetched most recently.

## 9. Freshness, outages, and publication

Proposed operator thresholds are product decisions, not promises by NPS or NWS:

- Alerts and operational notices: target a successful check every two hours; mark stale after four hours.
- Park metadata, hours, and fee components: target daily collection; mark stale after 48 hours.
- Curated entry rules: check source changes daily; substantive changes suspend the old automatic conclusion pending review. Re-review unchanged rules at least weekly and at season boundaries.
- Weather: only render periods that actually exist in a supported forecast. Use the product's validity/expiry and a maximum four-hour snapshot age; label its location and issuance time.

The browser recalculates staleness against absolute timestamps, including when publication stops. The HTML always includes absolute times and an instruction to verify official sources. Unsupported or future forecast periods remain unavailable, not interpolated or fabricated.

On a provider error, retain the last valid snapshot with a degraded status and original timestamp. Publish that degraded status when possible, rather than quietly preserving a seemingly fresh page. Distinguish provider failure from website deployment failure in the operator report.

Validate record counts, pagination, schema shape, parse success, identifiers, source allowlists, and unexpected dropouts before interpreting a disappearance as a change. A substantial feed loss requires review; it must not erase the public history or generate mass “reopened” events.

## 10. Weather geography

A forecast point represents a location, not an entire large park. Name the selected visitor center, valley, entrance, or trailhead, and retain its coordinates in source metadata. In later coverage, multiple representative points may be necessary.

Do not convert a state-wide weather alert into a park-specific alert without checking geographic applicability. Do not derive a park-wide all-clear from the absence of alerts at one point. NWS forecast products documented here generally cover the coming seven days; conditions for later travel dates are not known from that feed [S05].

Weather remains a separately gated increment. The first park page can be useful with official weather links while geography and expiry handling are tested.

## 11. AdSense and search strategy

The reason to return should be the tool's original utility: date-aware requirements, a personalized checklist, transparent coverage gaps, and changes since an earlier check. Add concise, reviewed explanations of the implications of official notices. Do not claim personal park visits or field testing that did not occur.

Google's publisher policy disallows copied/embedded content without added value [S10]. Google Search also addresses mass-produced low-value pages [S11]. Permission to use a government source does not establish advertising eligibility or guarantee rankings.

Start with one strong page per covered park. Add dedicated road, seasonal, or permit guides only when they contain distinct reviewed information. No automatically generated park × date × year × keyword pages. Keep private trip parameters out of analytics, indexed URLs, and ad targeting.

Ads are off during development. A later activation gate includes actual publisher details, domain/site review, privacy and consent configuration, approved ads.txt content where applicable, mobile checks, and placement review. Keep ads out of the critical notice panel and never style them as official reservation links. Check the regional requirements for personalized ads, including Google's certified CMP requirements [S12]. Do not invent an AdSense account or submit an application without the owner.

No paid analytics, subscriptions, affiliate network, or advertising-tracking integration is part of this initial build. Search Console and limited measurement can be considered after publication and the appropriate account/configuration review.

## 12. Release sequence and acceptance

| Milestone | Deliverable | Exit condition |
|---|---|---|
| M0 | Design, source review, acceptance scenarios, handoff | Owner review; assumptions and gates explicit |
| M1 | Searchable shell and a complete pilot park page, then all five pilots | Traceable sources; known/unknown/stale distinctions; deterministic rule tests; usable mobile layout |
| M2 | Scheduled collection, semantic history, and staged deployment | Live key integration tested; outage and rollback drills pass; actual publication verified |
| M3 | Expansion to the 20-park target | Coverage inventory audited; each published park meets the same evidence and content standards |
| M4 | Weather, comparisons, and local saved parks | Geography, expiry, storage, and privacy cases pass without making the core fragile |
| M5 | Advertising-readiness review and activation | Publisher requirements met; quality and consent checks completed; owner-controlled deployment |

Development proceeds sequentially and updates `PROJECT_STATUS.md` after each meaningful task. Do not call M1 complete because five empty templates render, or M2 complete because a workflow file exists.

Detailed acceptance scenarios are in `docs/ACCEPTANCE_CRITERIA.md`. Those define release requirements, not a statement that every test has run.

## 13. Setup and review gates

Development authorization is distinct from permission to purchase services or accept provider agreements. The initial source-code work belongs on a reviewable feature branch; deployment and monetization remain separate gates.

Before live deployment: supply an owner-controlled NPS API key through secrets, configure the chosen hosting account, review the proposed source-content handling, and set the production URL. Do not put credentials in chat or commit them to source control. No domain purchase or billable upgrade is authorized by this document.

Before claiming a top-20 ranking: obtain and audit the official 2025 national-park recreation-visit export. Before claiming full rights coverage: finish item-level reviews for anything beyond the narrowly reviewed government-created text and facts. Before making fee totals: audit eligibility, units, exceptions, and pass coverage.

Source references S01–S18 resolve in `docs/SOURCE_REVIEW.md`. Reviewed 28 September 2026. This document specifies product behavior, not current travel advice.
