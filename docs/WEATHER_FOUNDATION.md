# Named-location weather foundation

`tracker/park_forecasts.py` is a pure NWS source adapter. It normalizes synthetic
or caller-provided responses and retains accepted evidence during failure. It
does not implement HTTP, collection commands, private checkpoints, publication,
schedules or visitor weather rendering. No real forecast location or forecast
has been added. Seasonal NPS guidance remains a separate dataset.

## API and source identity

- `initial_forecast(location)` returns a never-checked state.
- `validate_forecast(snapshot)` strictly validates complete state and hashes,
  returning a defensive copy.
- `collect_forecast(location, previous, now, fetch_json)` validates inputs before
  invoking an injected callback with exact official request URLs.
- `forecast_freshness(snapshot, now)` returns the current source-specific state.
- `ForecastCollectionError`, `TimeoutError` and `OSError` classify failed
  requests; `ForecastError` classifies invalid responses. Unexpected programming
  errors propagate. Exception messages and rejected bodies are never retained.

A location contains exactly `id`, `park_code`, `name`, `latitude`, `longitude`,
`coordinate_source_url` and `coordinate_checked_at`. Only the five pilot codes
are accepted. The NPS source page must match that park, use HTTPS, and contain
no credentials, query, fragment or traversal. A syntactically valid evidence
container does not prove that a real place/name/coordinate relationship was
reviewed or authorize its publication. The next layer must retain authoritative
geographic evidence; park profile centroids must not become named forecasts.

Point lookup rounds original coordinates to four decimal places and retains
the original location. Returned Point geometry must match that rounded request.
Office/grid fields derive one exact URL:
`https://api.weather.gov/gridpoints/{office}/{x},{y}/forecast`. Arbitrary linked
URLs are refused. The future transport must bound bytes, timeout and redirects,
identify the application using NWS's required User-Agent, and validate the
actual response origin. This pure callback interface is not that transport.

## Normalized evidence

Accepted 12-hour `us` GeoJSON forecasts need a simple closed Polygon containing
the rounded point, including its boundary. Wrong-grid, self-crossing, degenerate,
unclosed, multiple-ring or unsupported geometry is quarantined. Optional
response IDs, when present, must match the expected forecast endpoint. Requests
and geometry together bind the source; missing GeoJSON IDs are not fabricated.

Forecasts retain their own mapping, generation time, underlying source update
time, original `validTimes`, derived validity interval and 1–32 ordered periods.
Generation and update clocks must be present, coherent and no later than the
successful check. On the same grid, an older generation or update clock cannot
replace newer accepted evidence. A new grid is a separate stream. Publication
time remains unknown/null.

Intervals support explicit start/end or a positive days/hours/minutes/seconds
duration of at most eight days. Months, years and weeks are unsupported. Periods
must fit the source interval, be positive, at most 24 hours and nonoverlapping;
gaps stay gaps. Offset timestamps and microseconds are preserved.

Period metadata includes nullable name, summaries, temperature, wind direction,
wind speed and precipitation probability. Legacy integer F/C temperatures and
quantitative degF/degC temperatures carry explicit units. Quantitative wind
accepts km/h, m/s and mph; legacy wind strings stay source text. Missing values
remain null, including quantitative null values. Zero precipitation remains
zero; null never becomes zero or clear weather. Icons, elevation, unused fields
and diagnostics are excluded. Canonical normalized hashes and strict exact-key
schemas detect altered prior evidence. Received JSON and normalized state are
bounded to 1 MiB; extreme integers that cannot be finite numeric values are
safe refusals rather than uncaught conversion errors.

## Independent mapping, attempts and freshness

Point mappings are cached for **168 hours** and rechecked at the exact boundary.
When a required lookup fails, the collector retains evidence and does not query
the old grid. Successful discovery can survive a later forecast failure. That
failure retains the old forecast's own mapping and successful forecast clock,
even when the current discovered mapping changed.

Collection states are never-checked, success, failed and quarantined. Successful
coverage means only the checked named grid, never a whole park or all weather
hazards. Failed/quarantined attempts preserve dated last-good evidence and use
fixed generic error codes plus point-lookup/forecast stage metadata. Previous
identity, hash and clock errors are refused before requests.

Freshness checks use these ordered states:

1. `not_collected`, `failed` or `quarantined` for the current collection state.
2. `expired` at the source validity end or last period end, whichever is earlier.
3. `not_covered` when no period covers the requested instant, including gaps.
4. `mapping_stale` at the 168-hour mapping boundary.
5. `stale` at **six hours** from the oldest successful-check, generation or
   underlying-update clock; otherwise `fresh`.

These are conservative initial local policies, not NWS update guarantees.
Repeated checks of old source data do not renew its age. A failed attempt does
not establish clear weather. Future evidence and collection-clock rewinds are
refused; comparisons retain microsecond precision.

## Verification and next work

Tests use synthetic locations and provider fixtures. They cover normalization,
provenance, geometry, units/nulls, intervals, expiry/gaps, cache boundaries,
source replays, retention after changed mappings, hashes, safe diagnostics and
caller mutation. No real weather request, source approval, rights approval,
backup or live forecast is established by these tests.

Next verify actual named locations against authoritative NPS geographic
evidence, then add the separate bounded private NWS transport and immutable
checkpoint/recovery lifecycle. Reviewed public export and weather rendering
follow those foundations. NWS alerts remain a separate adapter.

References checked October 4, 2026: [NWS API documentation](https://www.weather.gov/documentation/services-web-api)
and [official OpenAPI specification](https://api.weather.gov/openapi.json).
