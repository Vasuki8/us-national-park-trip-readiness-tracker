# Source-readiness continuation plan

**Goal:** Complete the missing general-entry source reviews without inventing dated rules, make coverage labels derive from data, and attempt a read-only NPS integration preflight.
**Authority:** Continuation of the owner-approved pilot spec and PROJECT_STATUS.md. Execute inline in the existing draft PR; no merge, production deployment, indexing, schedule or ads.
**Base:** 83352bd88987eaebfa2252a5c9c3240fec096699, tree eece10648b427de7462343d67d7f83615e976d52.

## Tasks and acceptance

- [x] Add separate undated entry notes for Yellowstone, Zion and Grand Canyon. Store source URL, exact excerpt, SHA-256, actual review time, scope and rights basis. Dates stay null. Validate host/park, hash integrity, review status, calendar semantics and duplicate identity. Do not change the dated-rule evaluator or extrapolate undated evidence.
- [x] Derive homepage/directory source-coverage counts and labels from inventory, rules, notes and collector states. Expired, failed, conflicting or missing evidence cannot count as a recent successful check. Recalculate age in the browser. Add park-page evidence for undated notes and correct methodology/disclosure text.
- [x] Add and execute a read-only preflight using an owner-controlled NPS key only inside GitHub Actions. Fixed pilot codes, bounded requests, safe scalar diagnostics and no production writes. A missing key blocks the integration gate. The first run returned not_configured; real API validation remains blocked.
- [x] Run local deterministic tests, then full remote CI. Self-review the diff and update the handoff with exact results and remaining gates. Final README/plan/handoff documentation commit has no application changes.

## Review focus

Undated notes never authorize another year; excerpt tampering and lookalike URLs fail validation; duplicate or stale state cannot inflate coverage; missing keys never make requests; provider errors or echoed keys never appear in reports. Status remains noindex/ad-free and draft/unmerged.

## Execution and evidence

The container could not resolve github.com, so local deterministic tests ran in an isolated partial workspace assembled from confirmed source contents. Full existing-suite and browser verification ran through the repository's read-only CI. No remote main or repository settings changed. No independent reviewer was available; author self-review is recorded in PROJECT_STATUS.md.

15 new Node tests and 11 new Python tests were observed RED then GREEN locally. Commit 0dce38b included the four new browser contracts before their UI existed. Run 36481488060 had exactly those four expected browser failures; its six existing browser cases passed. After UI implementation, run **36482305462** at head **94bb7afdd1f2297f12a9a2f922ee57d5d71b1914** passed **50 Node + 31 Python + 18 static + 10 browser = 109 tests**, plus Astro check/build.

The read-only NPS preflight run **36481482091** received no configured key: status not_configured, gate_passed false, publication_performed false, checks empty. Diagnostic completion is not live integration approval. Configure the private Actions secret, then rerun without enabling publication.

Ruling: general-entry statements without effective dates stay in a separate observation schema, not invented annual rules. Cost: date-specific determinations for those three parks remain unavailable until sufficiently scoped evidence is reviewed. This preserves the spec's evidence/date requirements.

Ruling: durable response retention and automatic source-change monitoring remain separate next work. The preflight emits safe scalar diagnostics only; no real-response fixture or production history is claimed.
