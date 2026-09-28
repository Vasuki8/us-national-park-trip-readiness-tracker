# Source-readiness continuation plan

**Goal:** Complete the missing general-entry source reviews without inventing dated rules, make coverage labels derive from data, and attempt a read-only NPS integration preflight.
**Authority:** Continuation of the owner-approved pilot spec and PROJECT_STATUS.md. Execute inline in the existing draft PR; no merge, production deployment, indexing, schedule or ads.
**Base:** 83352bd88987eaebfa2252a5c9c3240fec096699, tree eece10648b427de7462343d67d7f83615e976d52.

## Tasks and acceptance

1. Add separate undated entry notes for Yellowstone, Zion and Grand Canyon. Store the reviewed source URL, exact text excerpt, SHA-256, actual review time, scope and rights basis. Dates stay null. Validate source host/park, hash integrity, review status, date semantics and duplicate identity. Do not change the dated-rule evaluator or extrapolate undated evidence.
2. Derive homepage/directory source-coverage counts and labels from inventory, rules, notes and collector states. Expired, failed, conflicting or missing evidence must not count as recently checked. Recalculate age in the browser. Add usable park-page evidence for undated notes and correct the methodology/disclosure text.
3. Add a read-only preflight that checks an owner-controlled NPS key only inside GitHub Actions. Use fixed pilot codes, bounded requests and safe scalar diagnostics. A missing key is a blocked integration gate, not an empty successful feed. Never print credentials or provider response bodies; never write production snapshots. Trigger an initial branch-only preflight, no recurring schedule.
4. Run local deterministic new tests, then full remote CI. Review the diff, retain any failures honestly, and update the handoff and PR with exact results and remaining gates.

## Review focus

Undated notes never authorize another year; excerpt tampering and lookalike URLs fail builds; duplicate or stale state cannot inflate coverage; missing keys never make requests; provider errors or echoed keys never appear in reports. Status remains noindex/ad-free and draft/unmerged.

## Execution constraints

The container cannot resolve github.com, so this is an isolated local test workspace assembled only from confirmed file contents. No remote main or repository settings are changed. Full existing-suite verification is performed by the repository's read-only CI. No independent reviewer is available; perform a separate author self-review.
