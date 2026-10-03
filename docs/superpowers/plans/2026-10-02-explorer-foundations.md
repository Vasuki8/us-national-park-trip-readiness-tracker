# Explorer foundations implementation plan

> **For agentic workers:** Use the subagent-driven-development workflow for the independent adapter task and review the complete branch before integration. Steps use checkbox syntax for tracking.

**Goal:** Close the legacy collection bypass and add a tested source-specific park-profile foundation.

**Architecture:** Preserve the existing alert pipeline. New profile normalization and collection are pure/injectable, independent of alert schemas and publication.

**Tech stack:** Python 3.12 standard library; existing unittest and WSL development environment.

**Spec:** `docs/FOUNDATION_ASSESSMENT.md`, especially First increment contract.

## Global constraints

- Preserve all committed public data, frontend output, private-evidence boundaries and release controls.
- No live source requests, credentials, filesystem profile persistence, default transport, new service or deployment.
- All five pilot parks only; nullable unknown fields and source clocks remain honest.
- Use synthetic fixtures and `umask 022`; required application verification runs through existing CI.

## Review focus

- A configured key and legacy path arguments must not trigger requests or writes.
- Invalid previous snapshots fail before transport; malformed clock/state/hash combinations cannot be retained as valid evidence.
- Empty/wrong/duplicate/partial profile responses preserve last-good data.
- Seasonal weather and activity categories must not become forecasts or individual listings.
- Equal content preserves observation clocks; failed attempts cannot renew successful-fetch freshness.

## Task 1: Retire direct-write CLI

Files: `tracker/__main__.py`, `tests/test_legacy_collector_cli.py`.

- [x] Reproduce legacy writes with synthetic transport and temporary files; record expected refusal assertions failing before the fix.
- [x] Replace the entry point with `main(argv: list[str] | None = None) -> int`, returning 2 and a static migration message to stderr. No environment/network/filesystem work.
- [x] Verify default and explicit destinations, configured/missing key, arbitrary arguments and subprocess module behavior. The recommended private staging command remains unchanged.
- [x] Run focused tests and self-review the diff.

## Task 2: Source-specific profile adapter

Files: `tracker/park_profiles.py`, `tests/test_park_profiles.py`.

- [x] Write and observe failing tests for the interfaces and spec contract before implementation.
- [x] Implement `initial_profile(park_code: str) -> dict`, `validate_profile(snapshot: dict) -> dict`, `collect_profile(park_code: str, previous: dict, now: str, fetch_page: Callable[[int], dict]) -> dict` and `profile_freshness(snapshot: dict, now: str) -> str`.
- [x] Verify valid profiles for all five parks, absent versus empty optional fields, seasonal labels, exact field allowlisting, official URL scope, stable hashes/clocks, failure retention, malformed feeds, prior-snapshot refusal, clock boundaries and mutation isolation.
- [x] Run focused tests and review source-specific invariants without adding public consumers.

## Task 3: Verify and integrate

Files: `docs/DEVELOPMENT.md`, `PROJECT_STATUS.md`, this plan.

- [ ] Run the complete Python and Node tests, Astro check, both builds and generated-site checks; use supported CI for both browser suites.
- [ ] Obtain independent branch review, fix actionable findings and verify the exact PR head before the preauthorized merge.
- [ ] Update the handoff and document remaining transport/durability/source-rights work. Record accurately that the live artifact and source data were unchanged.

Local checkpoint: 290 Node, 477 Python and 62 generated-site tests passed;
Astro reported zero diagnostics and both 14-page builds passed. Independent
review and the mutation-fallback re-review passed. PR browser CI and integration
remain pending; current handoff records the detailed evidence and next milestone.
