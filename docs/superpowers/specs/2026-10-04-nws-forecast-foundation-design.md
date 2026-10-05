# Named-location NWS forecast foundation

The owner wants useful forecasts for named developed areas in the five pilot
parks, with trustworthy source identity, honest clocks and retained evidence
when a refresh fails. This architectural slice supplies the pure source
contract. Ordinary schema, cache and internal API choices are delegated by
the permanent owner policy; implementation proceeds within that authorization.

## Scope and architecture

Follow the existing narrow Python adapter approach. A transport-injected NWS
adapter is the recommended first step: it is inexpensive, independently
testable and leaves private durability and publication as separate boundaries.
Building private collection at the same time would couple unfinished source
validation to durable writes. Introducing a hosted weather service now would
add infrastructure before a validated source contract exists.

Create `tracker/park_forecasts.py`, synthetic tests and an operator-facing
foundation document. Reuse strict timestamp/canonical JSON helpers. Python
3.12+, Node 24 and the frozen dependency files remain unchanged. The adapter
has no HTTP implementation, credentials, CLI, disk writes, schedule, public
dataset or visitor consumer. Existing real data, clocks, rights, snapshot
identity, deployment and noindex/ad-free safeguards remain exact.

## Named locations and mapping

A location has exactly `id`, `park_code`, `name`, `latitude`, `longitude`,
`coordinate_source_url`, `coordinate_checked_at`. IDs are stable lowercase
slugs, names are nonempty, coordinates are finite numbers in geographic bounds,
and the coordinate source is a same-park NPS HTTPS page without credentials,
query, fragment or traversal. The evidence URL/check time establishes a
provenance container, not proof that the coordinates/name were reviewed. No
actual location is added in this increment; future collection must retain and
verify the geographic evidence, rather than substitute park centroids.

Use `/points/{latitude:.4f},{longitude:.4f}`; preserve original coordinates and
document the four-decimal lookup rounding. Require the returned GeoJSON Point
coordinates to match that rounded request. Accept only a three-letter uppercase
office, nonnegative integer grid coordinates and the exact HTTPS
`api.weather.gov/gridpoints/{office}/{x},{y}/forecast` URL. Never follow an
arbitrary provider URL. Mapping is rechecked at exactly 168 hours, an initial
local cache policy rather than an NWS promise. When discovery is due and fails,
retain evidence and do not silently request the outdated mapping.

## Forecast data and time

The injected request consumes the derived exact forecast URL and returns a
GeoJSON Feature. Require a bounded simple closed Polygon containing the rounded
point, including its boundary, so a response for another grid cannot be
mislabelled. Unsupported geometry is quarantined. Optional response `id`, when
present, must match the expected URL. This narrow adapter accepts the documented
12-hour `us` forecast format; hourly forecasts are separate future scope.

Retain `generatedAt` as generation time and `updateTime` as underlying source
update time, separately from attempt and successful collection clocks. Both
must be valid, ordered and no later than collection. Missing required clocks
quarantine the response rather than invent a source time. `published_at` stays
null. Parse `validTimes` as start/end or start plus a positive days/hours/minutes/
seconds duration, bounded to eight days. Retain its original text and derived
exclusive end. Months, years and weeks are not silently interpreted.

Accept 1–32 sequential nonoverlapping periods, each positive and no longer than
24 hours, entirely within that validity interval. Preserve offset-aware start/
end values and nullable names, summaries, temperature, wind and precipitation.
Legacy numeric F/C temperature and documented quantitative degF/degC values are
normalized with explicit units; null remains null. Wind text remains source
text, quantitative wind keeps its supported unit, and precipitation percentages
are bounded 0–100. Missing information is never zero, calm or clear. Icons,
elevation, raw headers, unknown fields and provider diagnostics are excluded.

Each accepted forecast contains its own mapping and deterministic canonical
hash. This binds retained forecasts to their original grid even if a later
point lookup changes the grid and the new forecast fails. Validate complete
previous state, hash, identities and clocks before invoking any transport.
Return defensive copies and refuse collection-clock rewinds.

## State, retention and freshness

Use never-checked, success, failed and quarantined collection states. Known
transport errors produce fixed generic codes; known malformed responses produce
quarantine. Unexpected programming exceptions propagate. No rejected response
body or exception text enters retained state. Successful mapping discovery can
be retained independently when the subsequent forecast fails; the previous
forecast and successful forecast clock stay exact.

Freshness returns not-collected, failed, quarantined, expired, not-covered,
mapping-stale, stale or fresh. Failure states take precedence. Expiry occurs at
the earliest of the source validity end and final period end. A gap or future
first period is not-covered. Mapping expires at 168 hours. Forecast freshness
expires at exactly six hours from the oldest of the last successful fetch,
generation and source-update clocks. These are conservative initial local
policies; rechecking old source data does not make it fresh. Comparisons retain
microsecond precision. No forecast implies park-wide coverage or trip safety.

## Verification and next boundary

Synthetic tests cover every pilot, exact URL derivation, coordinate/grid
misbinding, malformed/null/unit data, durations, gaps/overlaps, future and
rewound clocks, cache/freshness boundaries, hash tampering, partial failure,
changed-grid retention, defensive copies and safe diagnostics. Run the complete
repository verification and immutable independent review before authorized
integration. No weather publication or live-provider success is claimed from
synthetic tests. Next add authoritative named-location evidence and the separate
bounded private transport/checkpoint lifecycle; NWS alerts follow separately.

Consulted October 4, 2026: [NWS API documentation](https://www.weather.gov/documentation/services-web-api)
and [official OpenAPI schema](https://api.weather.gov/openapi.json). The schema
distinguishes forecast generation from underlying update time and documents
legacy and quantitative units. Documentation retrieval is not park collection.
