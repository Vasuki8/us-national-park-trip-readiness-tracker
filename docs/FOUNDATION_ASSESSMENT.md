# Explorer foundations assessment

Assessed October 2, 2026 against the permanent owner instructions and the
implemented five-park pilot. This records engineering decisions; it does not
establish source approval, image rights or deployment readiness.

## Existing capabilities and gaps

| Foundation | Implemented evidence | Gap and next use |
| --- | --- | --- |
| Central collection | `tracker/alerts.py` bounds requests, pagination, retries and normalized notice hashes. `tracker/stage.py` explicitly collects into private staging. | These contracts describe NPS alerts. Park descriptions, activity content and NWS forecasts need separate adapters and validation. |
| Provenance and recovery | Private archives, editorial ledger, backup verification and paired alert/history promotion retain source evidence and clocks. | Generalize through source-specific contracts; do not store unrelated datasets in the alert archive or treat source capture as publication approval. |
| Cached publication | Astro reads committed validated JSON. Browsers make no source API calls. A verified artifact is published deliberately. | Keep this inexpensive delivery model while adding sources. Later evaluate scheduled collection and Cloudflare against measured requirements. |
| Freshness and failure | Alert attempts and successful checks are distinct. Failed/quarantined refreshes retain records; alert age is four hours. Entry review age is 168 hours. | Add independent profile and named-location forecast policies. Build/publish time must not reset source freshness. |
| Publication boundary | Reviewed promotion binds all five alert files and paired history. | Pre-change audit found `python -m tracker` directly writing alert JSON, bypassing staging/history. This increment retires that entry point with a refusal-only migration message. |
| Park experience | Five static park routes, accessible native navigation, stored guidance, notices/history, official planning links and page-only checklist/printing. | No overview, seasonal, activity, forecast, photo or persistent-trip datasets. Build real source-backed sections before adding navigation to them. |
| Source rights | Existing rights manifests cover the six reviewed guidance records; media is refused by the readiness gate. | Review new text scope and each photo's reuse rights separately before public promotion. An API image credit is not a licence. |

## Architecture decision

Retain Astro, GitHub Pages and the current private review/promotion tools for
this increment. Migrating hosting does not solve the missing source contracts.
Fetching source APIs in visitor browsers conflicts with centralized collection
and would expose inconsistent clocks and credentials. Introduce narrow Python
adapters first, with injectable transports and synthetic tests; add private
durability, reviewed public exporters and UI consumers only when their contracts
are complete. No new dependencies or paid services are needed.

The first new adapter is a **park profile**, separate from alerts and entry
rules. It normalizes the NPS `/parks` response's introduction, identity, activity
categories and general seasonal weather text. Categories are not individual
hikes or activity listings. `weatherInfo` is seasonal/general context, never a
forecast. Park-level coordinates are not selected forecast locations. Images,
fees and other unrelated fields are excluded from this narrow schema.

## First increment contract

- Retire the legacy direct writer with a safe nonzero migration message and no
  requests, key reads or filesystem writes. Operators use the existing explicit
  `tracker.stage` command and reviewed promotion workflow.
- Add `tracker/park_profiles.py`: `initial_profile(park_code)`,
  `validate_profile(snapshot)`, `collect_profile(park_code, previous, now,
  fetch_page)` and `profile_freshness(snapshot, now)`.
- Restrict to the five pilot codes. A successful scoped `/parks` response has
  exactly one matching park, total one and start zero. Empty, wrong-park,
  duplicate, malformed and partial results retain the last-good profile and
  successful check clock with a quarantined state.
- Store only allowlisted normalized fields and a deterministic record hash.
  Missing optional description, seasonal context or categories remain null;
  a supplied empty category list remains distinct. Identity and official
  same-park HTTPS URL are required. Source issue/update/publication clocks stay
  null without trustworthy evidence. Observation clocks describe collection.
- Validate the complete previous snapshot before collection, including hash,
  source identity, state and timestamp coherence. Refuse rewind/future clocks
  before invoking transport. Preserve caller inputs through deep copies.
- A transport failure retains last-good evidence with a generic failure code;
  do not retain exception text or rejected provider bodies. An unexpected
  programming exception propagates rather than inventing a successful check.
- Use a seven-day profile freshness window as an initial conservative local
  policy for slow-changing context, independent of four-hour alerts. Failed or
  quarantined current attempts never count as a current successful refresh.
- This adapter has no default transport, CLI, persistence or public consumer.
  Tests use synthetic payloads. It neither acquires credentials nor authorizes
  collection/publication.

## Implementation sequence after this increment

The following private collection increment now implements the fixed-endpoint
transport and immutable five-park checkpoint lifecycle, including offline
verification, restore and private review-candidate export. It reuses existing
POSIX guards rather than adding a mutable archive. See
[PROFILE_COLLECTION.md](PROFILE_COLLECTION.md). Synthetic verification does
not establish real profiles, text-use review, remote backup or public promotion.

1. The [reviewed public-profile contract](PROFILE_PROMOTION.md) now implements
   separate text-use scope, complete approval/hash bindings, paired patch
   preparation/recheck and profile rights/backup coverage in build/readiness
   validation. This synthetic engineering work does not approve actual text.
2. The first real profiles, private remote recovery and reviewed public pair
   were completed in PR #11. PR #12 renders source-backed Overview and When to
   Visit, preserving fragments, original clocks and uncertainty. The current
   handoff records verification; these changes have not been deployed live.
3. The separate [NPS `/thingstodo` foundation](ACTIVITY_FOUNDATION.md) now adds
   bounded individual listings, park attribution, unknown geography/agency/
   difficulty/permits and independent freshness. Synthetic tests cover complete
   pagination and last-good retention; there is no real activity inventory.
   The separate [private activity collection lifecycle](ACTIVITY_COLLECTION.md)
   now adds fixed-endpoint transport, all-five preflight, immutable checkpoints,
   offline verification, restore and private unapproved review export. Synthetic
   tests establish tools only. Next implement separate activity text-rights/
   public projection before real collection, verified remote backup, reviewed
   promotion and visitor rendering.
4. Select named weather locations from authoritative geographic evidence.
   NWS `/points/{lat},{lon}` discovers the grid forecast; periodically recheck
   that mapping. Validate issue/valid-period/check clocks and retain last-good
   forecasts with their own freshness/expiry policy. Add NWS alerts separately.
5. Expand planning datasets, six-section park navigation and device-local trip
   tools in the owner's phase order. Photo publication requires per-asset rights
   review. Indexing, ads and recurring operations retain their deliberate gates.

The unresolved manual screen-reader announcement review remains a quality task;
automated keyboard checks cannot establish actual announcements.

## Official source references

Consulted October 2, 2026:

- [NPS API documentation](https://www.nps.gov/subjects/developer/api-documentation.htm)
  and [published schema](https://www.nps.gov/subjects/developer/customcf/swagger.json)
  distinguish park profiles, activity categories and individual things to do.
- [NPS API guide](https://www.nps.gov/subjects/developer/guides.htm) documents
  private header authentication and source usage guidance.
- [NWS API documentation](https://www.weather.gov/documentation/services-web-api)
  documents named-coordinate grid discovery, cache-friendly delivery, application
  identification and periodically rechecking point/grid mappings.

These documents guide adapter design; no live provider response was collected
or retained for this assessment.
