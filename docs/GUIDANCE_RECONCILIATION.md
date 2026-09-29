# Private guidance reconciliation

## What this workflow does

Guidance reconciliation is an explicit human-review step for the private entry-source ledger. It resolves source-review holds only after a reviewer has inspected a retained source context and supplied the complete approved guidance inventory.

It does **not** publish the website, update public `data/` files, verify current park access, confer redistribution rights or authenticate the reviewer.

## Preconditions

Before reconciliation:

1. A private ledger already contains the source capture as an `observation` event.
2. The relevant proposals are still active.
3. The reviewer has inspected the complete retained context represented by that observation, not just the saved excerpt.
4. The replacement guidance records are prepared with the real review timestamp.
5. Any separate source-content/rights question has been considered independently.

Use `status` to obtain the current ledger revision and active proposal IDs.

## Request

A private reconciliation JSON file has:

```json
{
  "source_event_revision": "<observation-event-sha256>",
  "proposal_ids": ["<active-proposal-sha256>"],
  "reviewer": "operator-label",
  "rationale": "Why the complete retained source context supports this revision.",
  "reviewed_at": "2026-09-29T14:00:00Z",
  "records": ["<complete resulting private guidance inventory>"]
}
```

The file should be owner-only and outside the public repository.

Run:

```sh
uv run --frozen python -m tracker.entry_review_cli reconcile \
  --store /absolute/private/entry-review \
  --input /absolute/private/guidance-reconciliation.json \
  --expected-revision CURRENT_HEAD_SHA256
```

## Source-level atomicity

A source can supply multiple guidance records. Every active proposal for an affected source must be included in one reconciliation. The command refuses partial source-level approval.

The selected observation must be the latest retained source observation for every affected source. It may be newer than the original hold—for example, a later clean capture while an older proposal remains sticky—but it cannot be older than any hold being cleared.

A failed capture or parser failure cannot become an approved baseline because it has no accepted retained context.

## Guidance validation

The supplied `records` array is the complete resulting private inventory.

Unaffected records must remain exactly unchanged.

Affected records must:

- keep their ID, park and official source;
- retain the existing record/evidence schema;
- pass the existing dated-rule or undated-note validator;
- use `review_status: reviewed`;
- set record and evidence `reviewed_at` to the exact reconciliation review time;
- preserve `rights_basis` and `rights_reviewed_at`.

The selected retained context must contain each newly approved excerpt exactly once. Zero matches or multiple matches fail.

This permits a reviewer to approve a real guidance revision—summary, effective dates, requirement details, exception notes or excerpt—while preventing unrelated or rights metadata from changing accidentally.

## Evidence retained

The immutable reconciliation event contains:

- exact source observation revision selected;
- proposal IDs cleared;
- reviewer label, rationale and review time;
- complete new guidance inventory;
- hashes for previous and next guidance records;
- affected guidance/source identities;
- the derived reviewed context baselines.

The earlier observation and previous guidance remain in earlier events. The database head advances atomically.

## Baseline behavior

Explicit reconciliation creates schema-v2 baselines. Their clock order is:

```
source capture <= human review < future source capture
```

Future `record` operations use ledger-held baselines automatically. Caller-supplied baseline replacement is rejected.

Legacy schema-v1 baselines use the older workflow where context review followed an already approved guidance record. Unaffected validated v1 baselines are carried forward when the first v2 source is reconciled.

## Sticky holds

A matching later source check never clears an existing proposal automatically. The reviewer may use the newer retained observation as the reconciliation source, but the old hold remains explicit until the reconciliation event clears the complete affected source set.

## Safe output

CLI output is a summary only. It does not include retained page text, proposed excerpts, reviewer rationale or private paths.

`approval_performed: true` in a ledger summary means the ledger contains at least one explicit private reconciliation event. It does not mean public publication occurred.

## Current project boundary

The implementation is tested with synthetic private evidence. The earlier live compatibility diagnostic proved the five configured NPS pages can be captured/extracted/replayed, but it intentionally deleted its temporary ledger and created zero approved baselines.

A future real review must use owner-controlled durable private storage. No real NPS context should be described as approved until that separate operator action has actually occurred.
