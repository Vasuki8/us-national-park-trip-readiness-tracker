# Selected entry-source review gate

## What this slice does

`scripts/entry-review.ts` accepts a complete batch of **already supplied plain-text source observations** for the current stored guidance. It compares the selected text, produces pending proposals with exact before/after evidence, and overlays `needs_review` on affected records for the existing website/evaluator/coverage paths. An existing `conflict` is preserved. It does not scrape NPS, locate HTML sections, infer policy meaning or approve a new rule.

The checked-in `data/entry-review.json` initially contains no proposals. Empty means no pending proposal has been supplied to this build, **not** that sources were checked or did not change. Automatic source monitoring remains inactive.

## Programmatic contract

Import `guidanceDigest`, `assessEntrySources`, `validateEntryReview` and `applyEntryReview` from `scripts/entry-review.ts` in trusted Node code. Run TypeScript with the repository's existing Node type stripping. No dependency is added.

1. Load the original approved `data/rules.json` and `data/entry-notes.json`, in that order. Validate them using the existing data/evidence validators. Never use status-overlaid output as an approved baseline.
2. For every record, supply exactly `{guidance_id, guidance_hash, source_url, checked_at, status, excerpt}`. `guidance_hash` is `guidanceDigest(originalRecord)` and binds the complete record, not just its excerpt. `source_url` must be the exact approved official page. `status` is `observed`, `missing` or `failed`. Only `observed` carries nonempty plain-text `excerpt`; the other states require null.
3. `checked_at` must be a real UTC instant in `YYYY-MM-DDTHH:mm:ssZ` or millisecond ISO form, strictly after that record's approval and not after the supplied `now`. The source check time is never an approval, source-update or restriction-effective time. All six current guidance records must appear once; partial and sparse batches fail rather than implying complete coverage.
4. `assessEntrySources(records, observations, pendingRegister, now)` returns `{register, checks}` without mutating inputs, reading files, writing files or contacting a service. Checks contain outcome metadata; the candidate register retains exact before/after selected text for review. A matching observation produces `matching_excerpt`, not approval.
5. `applyEntryReview(records, register, now)` validates the register against the original records and returns defensive copies plus minimal public `holds`. It changes only `review_status`. The site data boundary consumes this output, so the unchanged date evaluator refuses automatic conclusions from held dated rules, and coverage/evidence views reflect the hold. Undated notes remain undated.

There is deliberately no write/approve/resolve CLI or automated persistence in this slice. Trusted operator integration must preserve pending evidence, impose bounded strict JSON input handling, and review any proposed change before a register is committed or made public. Do not put credentials, raw HTTP responses or private paths in observations. Unknown fields are rejected; diagnostic errors contain fixed codes, not input payloads.

## Comparison semantics and limits

Only runs of ASCII whitespace and nonbreaking spaces are collapsed, with leading/trailing whitespace removed. Case, punctuation, dates, times, added text and negation are not ignored. The entire supplied selected text must match: merely finding the old sentence within a changed supplied region is not equality. This can generate conservative false positives; it does not claim language-level semantic understanding.

**A matching excerpt cannot detect new contradictory content elsewhere on the page.** The existing record has an excerpt baseline, not a verified complete-page baseline. A future source adapter must retain explicit selection scope, inspect surrounding/exception text, handle changed selectors and ambiguous/multiple matches, and require editorial review when scope cannot be established. Do not route whole-page HTML into this API and call it validated extraction.

Changed text, a missing excerpt and a failed check all create holds. This is conservative: a temporary source outage can require review even while the old approval is within seven days. Later matching text cannot clear a prior hold, cannot change `reviewed_at`, and cannot rescue an expired weekly review. Failed checks do not invent replacement evidence.

Exact duplicate pending observations are idempotent. Conflicting same-instant observations or attempts older than the latest pending observation are rejected. Matching observations are returned in the per-run checks but are not a durable all-attempt log; the register retains **unresolved proposals**, not complete collection history. This is not a second alert archive.

Limits are 32 approved bindings, 120 pending proposals, 32,768 UTF-16 code units per selected excerpt and 2 MiB canonical register JSON. Limits reject, never discard an older hold. These are programmatic object bounds, not a file reader or transport allocation guarantee. Malformed Unicode, invisible direction controls, unsupported clocks, source mismatches and unexpected fields fail validation.

## Review and approval boundary

Each proposal binds the entire original approved record and exact old text. If the approved summary, dates, source, review time or any other field changes, old proposals no longer validate against that record. A reviewer must explicitly reconcile them rather than allowing automatic clearance.

Until an approval/resolution workflow exists, any trusted repository edit resolving a hold needs a reviewed diff recording disposition, official evidence, effective scope, and original proposal identity. Preserve the old proposal in reviewed history; do not merely delete the register to make a build green. The application does not authorize Git changes or prove who reviewed them. Hashes check consistency, not authenticity, field truth or source-use permission.

The public warning receives only guidance identity, reason labels, official source URL and absolute pending-check times. It never receives candidate replacement text. The old approved excerpt stays available as historical evidence, clearly marked for re-review. Source text stored in a **public repository** is public even when it is not rendered by the website; item-level content review is still required before committing real proposals.

## Verification scope

Pure Node contracts cover strict schema, comparison, sticky holds, replay, immutability and bounds. Integration contracts use all six current bindings and the unchanged evaluator/coverage functions. Isolated Astro fixture routes exercise the production warning component; synthetic source changes are not production observations. Complete CI and final results are recorded in PROJECT_STATUS.md after verification.

No live source fetch, key check, schedule, deployment, indexability change, advertising or provider agreement is activated by this feature.
