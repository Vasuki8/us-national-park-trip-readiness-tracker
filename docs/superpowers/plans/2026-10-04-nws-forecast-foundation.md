# NWS Forecast Foundation Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking. The owner delegates ordinary implementation decisions; execute inline with one independent whole-branch review.

**Goal:** Validate named-location NWS forecasts and preserve honest last-good evidence.

**Architecture:** A pure transport-injected Python adapter follows the existing
NPS profile pattern. Point mappings and forecasts are separately bound; public
data and private collection remain separate later layers.

**Tech Stack:** Python 3.12+, stdlib, existing canonical JSON/time helpers; Node 24/frozen repository checks.

**Spec:** [Design](../specs/2026-10-04-nws-forecast-foundation-design.md).

## Global constraints

- Exactly five pilot codes; no real coordinates or forecasts introduced.
- Six-hour forecast age, 168-hour mapping cache, eight-day validity bound.
- 1–32 periods, each positive and at most 24 hours; exclusive ends.
- No dependencies, HTTP implementation, persistence, publication or schedules.
- Preserve all existing public bytes and source clocks.

## Review focus

- Changed grid followed by failure must retain the old forecast's own mapping.
- A repeated check of old generated/update times must remain stale.
- Point rounding, Polygon edges and offset clocks must not misbind evidence.
- Malformed previous data must be refused before either injected request.
- Null or unfamiliar units must never become zero, calm or successful emptiness.

### Task 1: Pure source contract

**Files:** Create `tracker/park_forecasts.py`; test `tests/test_park_forecasts.py`.

**Interfaces:**
- `initial_forecast(location: dict) -> dict`
- `validate_forecast(snapshot: dict) -> dict`
- `collect_forecast(location: dict, previous: dict, now: str, fetch_json: Callable[[str], dict]) -> dict`
- `forecast_freshness(snapshot: dict, now: str) -> str`
- `ForecastError(ValueError)`, `ForecastCollectionError(RuntimeError)` fixed-code boundaries.

- [ ] Write synthetic tests for initial unknown state, identities, successful
  normalization, expected fixed request URLs, explicit metadata and nullable units.
- [ ] Run `uv run --frozen python -m unittest discover -s tests -p test_park_forecasts.py -v`;
  expect assertion failure that the adapter is missing.
- [ ] Implement strict location/mapping/forecast/snapshot validation, bounded
  interval/Polygon handling, canonical hashes and defensive collection state.
- [ ] Add retention, mapping-change, future/rewind, invalid previous, stale/expiry/
  coverage gap and microsecond-boundary tests before their behavior is implemented.
- [ ] Run the targeted suite to green, then the complete Python suite.
- [ ] Commit implementation and tests with the verified result.

### Task 2: Contract and continuity

**Files:** Create `docs/WEATHER_FOUNDATION.md`; update `docs/DEVELOPMENT.md`,
`docs/FOUNDATION_ASSESSMENT.md` and `PROJECT_STATUS.md`.

**Interfaces:** Documents describe Task 1's public functions and its exact limits.

- [ ] Document location-evidence versus approval, fixed URLs, clocks, policies,
  failure retention, unsupported response scope and next private collection layer.
- [ ] Run strict UTF-8, local Markdown links, private-marker and diff checks.
- [ ] Run full Python/Node, Astro, both builds and generated-site checks; required
  browser suites run on the unchanged supported CI runner if local installation
  remains unavailable.
- [ ] Review the immutable whole branch independently; fix important findings
  with regression tests and rerun affected/full checks as warranted.
- [ ] Commit and create the PR; required PR CI, exact-tree merge and main CI must
  pass. This pure adapter is not imported by the public build; do not republish
  unchanged runtime merely to claim weather is live.
- [ ] Record exact integration/live identity and next task in durable handoffs,
  preserve required ignored evidence and archive the managed worktree.
