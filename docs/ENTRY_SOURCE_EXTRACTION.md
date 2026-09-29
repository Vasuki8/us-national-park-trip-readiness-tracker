# Entry-source context extraction

## Purpose and boundary

`tracker.entry_sources.inspect_entry_sources(records, captures, baselines, now)` turns supplied official-page HTML into observations accepted by the existing TypeScript `assessEntrySources` API. It does not fetch, persist, approve, publish, or change original guidance. It returns `observations` plus a separate private `sources` evidence list. These are retained together by the protected operator ledger described in `docs/ENTRY_REVIEW_LEDGER.md`; the extraction API itself does no file I/O.

The current six guidance bindings share five sources. Profiles bind each park to the exact URL and expected H1 in `PROFILES`. A successful context check requires a separately reviewed baseline for that page, tied to the full original guidance hashes. An approved short excerpt alone is never treated as an approved full-page context. No production context baselines have been approved.

## What is compared

Scope `html-body-text-links-v1` contains normalized body text, block boundaries, H1 text and anchor href strings. Body navigation, footer content and collapsed/hidden FAQ text are intentionally included so an exception outside the old excerpt cannot disappear from comparison. Relative anchor targets are retained as private strings, never followed or rendered as trusted links. A changed link target affects context even when its visible label stays the same.

This is not a browser renderer. Script/style content and comments cannot establish the approved excerpt. Media, CSS-driven presentation, dynamic requests, linked-page content and embedded documents are not inspected. New script behavior with unchanged source text is outside this scope. Matching context means only these selected representations match, not that all page behavior or actual park conditions are unchanged.

Whitespace and inline emphasis can normalize without a change; body block boundaries remain distinct. Base elements and deletion/insertion/strike annotations require review, rather than silently retargeting links or accepting struck-out guidance. Input must have an explicitly closed, unique body and exactly one expected H1; a missing/duplicate excerpt or expected heading is not resolved by taking the first match. Strict interior tag balancing intentionally rejects some browser-repairable/optional-end-tag HTML. The September29 compatibility repair permits one exact redundant body/html closing pair after a completed document, but refuses appended visible text/elements instead of silently discarding them. See `docs/LIVE_ENTRY_COMPATIBILITY.md` for the observed envelope and its limits.

## Interfaces

Each capture has exactly `source_url`, `final_url`, `checked_at`, `status`, `content_type`, and `html`. A successful capture requires exact source/final URL identity, a text/html content type, and a supplied HTML string. A failed capture has null HTML, type and final URL. Its original attempt timestamp remains distinct from the baseline review timestamp. Different or redirected sources require explicit review instead of silently reusing a profile.

Each reviewed baseline has exactly `schema_version:1`, `source_url`, `profile_id`, `guidance_hashes`, `checked_at`, `reviewed_at`, `context`, and `context_hash`. The check precedes or equals that context review; the new capture must be later. A different approved guidance version invalidates its baseline. Hashes bind consistent data, not authenticity or reviewer authorization. Baselines are trusted operator review inputs, not proof that a review occurred. No approve/resolve service is implemented here.

A complete batch has one capture for every distinct source in the supplied validated guidance inventory, up to the five supported profiles. Original records remain in input order in the observations; shared-source rules are evaluated together. Incomplete inventories, stale baseline bindings, invalid clocks and unknown fields raise a fixed `SourceExtractionError` code. Per-page extraction problems become held observations while preserving the rest of the complete batch.

| Private extraction reason | Existing gate status | Meaning |
|---|---|---|
| matching_reviewed_context | observed | Approved excerpt is uniquely present and supplied context matches its separate reviewed baseline. This is not a new guidance approval. |
| excerpt_missing | missing | At least one bound excerpt is absent; no replacement text is invented. All guidance sharing that page is held conservatively. |
| context_not_reviewed | failed | Selected text may exist, but no reviewed surrounding-context baseline exists. |
| context_changed | failed | Surrounding text, block structure, heading or link targets differ from the reviewed context. |
| excerpt_ambiguous / heading_ambiguous | failed | Multiple or missing selectors cannot be trusted. |
| capture_failed / bounded-parser error | failed | Source/context verification did not complete. This need not imply an HTTP failure. |

`result.observations` uses the unchanged six-field intake contract. Pass it to `assessEntrySources(originalRecords, result.observations, pendingRegister, now)`; the existing register/hold/evaluator then suspends affected guidance. `result.sources` preserves the precise reason, profile/source identity, observation time, full original-guidance hash map, current extracted context and reviewed baseline context with their hashes. It is not a visitor payload. The ordinary gate's generic check-failed reason must be interpreted alongside this private evidence by operators; it does not assert that a network request failed.

## Bounds and handling

Maximum supplied HTML: 1 MiB UTF-8 per page. Text: 65,536 characters. Maximum element starts: 30,000; nesting: 128; links: 2,048. Maximum returned JSON: 2 MiB. Invalid controls and lone surrogates are refused. No source text is interpolated into diagnostic messages. Bound violations do not silently truncate evidence or declare a match. Caller-supplied strings are already in memory; these are parser/output limits, not a transport download budget.

Returned context can contain arbitrary third-party text and anchor strings from the supplied document. Keep it private, do not execute it, and do not turn it into HTML or clickable links without separate validation. Source-content review is required before any real context is committed to a public repository or published. Noindex is not privacy or access control.

## Source-profile review

On September 28, 2026 America/Toronto, the following public pages were opened through web retrieval to confirm their titles and textual scope. That initial review was a heading/source-family review, NOT a raw DOM capture, availability measurement, context baseline approval or current travel advice:

- Yosemite, Entrance Reservations: https://www.nps.gov/yose/planyourvisit/reservations.htm
- Rocky Mountain, Timed Entry Permit System: https://www.nps.gov/romo/planyourvisit/timed-entry-permit-system.htm
- Yellowstone, Permits & Reservations: https://www.nps.gov/yell/planyourvisit/permitsandreservations.htm
- Zion, Permits & Reservations: https://www.nps.gov/zion/planyourvisit/permitsandreservations.htm
- Grand Canyon National Park Operations Update: https://www.nps.gov/grca/planyourvisit/grand-canyon-national-park-public-health-update.htm

These source families mix entrance statements with additional provisions, activity information or operating updates. Comparing body context is deliberately broader than locating a stored sentence. No current fee, reservation, exception or road-status values were added to product data.

Parser reference: https://docs.python.org/3/library/html.parser.html. Python's parser tokenizes input; our additional checks supply the explicit completeness and scope constraints. Tests, rather than assumptions about tolerant HTML parsing, define the accepted subset.

## Verification and next integration

Synthetic HTML is generated in `tests/test_entry_sources.py` and `tests/entry_source_fixtures.py`. It is not downloaded NPS HTML. The six cross-language tests run the actual Python extractor against the six repository guidance records and pass the resulting observations to the actual TypeScript gate/evaluator. Matching context cannot renew reviewed_at, and later matching text cannot clear pending proposals.

Protected persistence and non-approving reviewer dispositions now exist in `docs/ENTRY_REVIEW_LEDGER.md`. On September 29, 2026, actual captures of all five configured entry pages passed the scoped extractor and temporary-ledger replay after a narrow document-trailer repair; see `docs/LIVE_ENTRY_COMPATIBILITY.md` for exact timestamps, hashes, scope and limitations. That diagnostic created no approved context baseline, renewed guidance or durable live archive. Operator-reviewed reference contexts and explicit approval/reconciliation remain prerequisites to matching source coverage. Alert API-key validation is separate; no keyed NPS API call is claimed.
