# Individual activity foundation

Implemented October 3, 2026. This pure adapter has synthetic tests. It establishes
no real activity inventory, source rights, private backup, public promotion or
deployment evidence.

## Source and interpretation

NPS `/thingstodo` supplies individual listings. The `/parks` categories already
displayed on park pages remain categories; they are not substituted for listings.
The [official schema](https://www.nps.gov/subjects/developer/customcf/swagger.json)
and [API documentation](https://www.nps.gov/subjects/developer/api-documentation.htm)
were consulted October 3, 2026 without an authenticated activity request.

`relatedParks` establishes source attribution. At least one validated relationship
must match the queried pilot; additional parks are retained. Relationships
preserve supplied names, designation, states and optional official URLs. They do
not prove an activity lies inside any park boundary or establish its responsible
agency. Global NPS activity URLs do not encode the queried park. Park-scoped
activity URLs must relate to a validated relationship.

`geographic_relationship` stays `unconfirmed`; `responsible_agency`, `difficulty`
and `permit_required` stay null. Descriptive wording does not infer these fields.
Fee and reservation flags remain distinct; neither establishes entry permits,
exemptions, annual validity or availability. An empty retrieved inventory does
not establish that a park has no activities.

## API and stored contract

`tracker/park_activities.py` exposes:

- `initial_activities(park_code)` for an unknown, uncollected inventory.
- `validate_activities(snapshot)` for strict validation and a defensive copy.
- `preflight_activity_attempt(park_code, previous, now)` for a pure isolated
  baseline check before a batch acquires credentials or invokes any factory.
- `collect_activities(park_code, previous, now, fetch_page)` for an injected,
  park-scoped `fetch_page(start)` transport.
- `activity_freshness(snapshot, now)` for clock-injected freshness.

Only Yosemite, Rocky Mountain, Yellowstone, Zion and Grand Canyon may be queried.
The source URL is fixed to the endpoint and pilot code. There is no default HTTP
transport, credential handling, CLI, persistence, exporter or UI consumer. The
adapter reuses only public canonical encoding, digest and instant helpers from
the history model; activities do not enter the alert archive or inherit existing
alert/profile approval.

Listings retain IDs, titles, official URLs, short/long descriptions, location and
its description, duration and its description, seasons and their description,
accessibility information, category IDs/names and activity description, fee/reservation/
pet flags and descriptions, age context, time-of-day context and credit. Missing
or null optional text stays null; supplied empty text stays empty, and empty
lists stay distinct from unknown lists. Deterministic sorting preserves supplied
strings. Duplicate identities and duplicate season/time values are refused.

Flags accept explicit booleans and literal `"true"`/`"false"` strings. Missing,
null or empty-string flags stay unknown. Integers, arbitrary truthy values and
differently spelled strings are refused. Official schema/examples use both
`arePetsPermittedWithRestrictions` and `arePetsPermittedwithRestrictions`; both
aliases are accepted, and conflicting normalized values quarantine the candidate.

Source HTML remains untrusted text. A future renderer must escape or separately
review it rather than insert it as HTML. Credit is metadata, not reuse rights.
Images, coordinates, undocumented organization objects, amenities and other
out-of-scope provider fields are excluded. Unknown normalized fields are refused.
Public text and media need separate reviewed rights and promotion contracts.

There is no exposed trustworthy publisher issue/update clock. Snapshot issue,
update and publication times and record source update times stay null.
Observation clocks describe collection. Semantic hashes include all retained
source fields and explicit unknown interpretation fields; observation clocks
do not affect the hash. Unchanged records preserve first and changed observation
clocks. Changed records advance only the changed clock; newly observed IDs start
both clocks at the current attempt.

## Pagination, bounds and recovery

Validate the complete previous snapshot, source identity and clocks before
transport. Attempts must strictly advance the previous attempt clock, including
when timezone offsets express the same instant. The accepted defensive copy
remains the baseline throughout callbacks. Before requests, both possible
degraded envelopes must fit with all retained records and the new attempt clock.
Insufficient capacity raises a fixed `ActivityError` without transport or caller
mutation; evidence is never trimmed to make room for failure metadata.

Accept only complete pagination with stable totals, exact requested offsets,
unique IDs and forward progress. Counts are nonnegative integers or one-to-eight
digit ASCII decimal strings, excluding booleans, signs, fractions, whitespace and Unicode digit
lookalikes. If supplied, a page limit must be positive, bounded and cover its
page. Bounds are 100 pages, 5,000 records, 1,000 entries per nested list, 65,536
characters per source text field, 256 characters per identifier, 256 KiB per
canonical normalized record and 8 MiB per canonical snapshot. Aggregate size is
checked while accumulating records and validating retained inventories.

A first complete zero-total inventory is a successful feed check with limited
coverage. A populated inventory falling below half its previous count, including
becoming empty, needs review. Exactly half is accepted; an odd baseline requires
the first integer count at or above half. This conservative local policy does
not prove any source listing was removed.

A malformed/refused page discards the entire candidate and returns
`quarantined`/`incomplete` with `response_requires_review`. Classified
`ActivityCollectionError`, `TimeoutError` and `OSError` failures return
`failed`/`incomplete` with `provider_request_failed`. An injected `ActivityError`
is an explicit response refusal. Unexpected transport programming errors
propagate. Degradation advances only the attempt clock and preserves accepted
records and original successful/observation clocks. Rejected bodies and exception
messages are never retained. Caller baselines and provider payloads are not
modified; accepted nested data is detached before the next page request.

## Freshness and next layer

The initial independent policy expires successful inventories at exactly 168
hours with microsecond precision. This local policy is not an NPS validity
guarantee. `not_collected`, `failed` and `quarantined` remain distinct; the latest
degraded attempt takes precedence over age. Freshness refuses future evidence
and never renews clocks. Alerts and seasonal profiles retain independent policies.

The [private collection workflow](ACTIVITY_COLLECTION.md) now implements the
separate bounded header-authenticated transport and immutable five-park
checkpoint/recovery lifecycle using existing POSIX guards. It preflights every
baseline before keys or factories. Synthetic checks establish tooling only.
Next implement separate reviewed text-rights/public projection; real collection,
verified remote backup, approval, promotion and Things to Do rendering remain
subsequent steps.
