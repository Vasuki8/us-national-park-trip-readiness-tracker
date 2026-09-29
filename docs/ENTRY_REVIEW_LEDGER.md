# Private entry-review ledger

## Purpose

`tracker.entry_review_store.EntryReviewStore` is a separate offline editorial ledger for entry-source captures, extracted context, review proposals, reviewer dispositions and explicit guidance reconciliations. It is not the alert archive and no website imports it directly.

The ledger is one owner-only SQLite database (`review.sqlite3`) outside the repository. SQLite comes from Python's standard library. This is local persistence, not hosted storage, encryption, authenticated identity or backup.

Every read replays the bounded event chain through the current extractor and review policy. Hashes verify consistency; they are not signatures, factual validation or proof of source-content rights.

## Observation record contract

The `record` input has exactly four fields:

- `records`: the complete current private guidance inventory.
- `captures`: one capture for every configured source represented by the inventory.
- `baselines`: legacy reviewed context baselines when no ledger-held explicit baselines exist; otherwise this must be empty.
- `seed_register`: the original proposal register seed. Later batches retain the same seed while accumulated ledger proposals are supplied internally.

A record event stores the supplied captures, extracted current/reference context, precise reasons, gate checks and resulting proposal register together. Matching checks are retained too. Importing never renews guidance approval dates.

Once a reconciliation has created ledger-held baselines, later record events automatically use those baselines and caller-supplied replacements are refused.

## Commands

Use absolute private paths outside the checkout and owner-only input files.

```sh
uv run --frozen python -m tracker.entry_review_cli status \
  --store /absolute/private/entry-review

uv run --frozen python -m tracker.entry_review_cli record \
  --store /absolute/private/entry-review \
  --input /absolute/private/capture-batch.json \
  --expected-revision empty
```

For later writes, replace `empty` with the exact current revision. Stale expected revisions are rejected. Exact retries of already committed operations are acknowledged without duplicating events or moving the head backwards.

CLI summaries expose safe counts, revision/proposal references, reasons and timestamps. They do not print source HTML/context, reviewer rationale, private paths or arbitrary exceptions.

## Read-only reviewer packet

Use `packet` to create a local inspection artifact before drafting or executing a reconciliation. It performs no network request and no ledger write.

```sh
uv run --frozen python -m tracker.entry_review_cli packet \
  --store /absolute/private/entry-review \
  --output-dir /absolute/private/review-packets \
  --park yose \
  --source-event-revision LATEST_OBSERVATION_EVENT_SHA256
```

The selected event must be the latest retained observation for that park's configured source, must contain a verified retained comparison context, and the source must still have at least one active hold.

The output root's parent must already exist with owner-only permissions. The command creates an owner-only output root if needed, then atomically installs `PACKET_ID/index.html` and `PACKET_ID/manifest.json`. CLI stdout contains safe manifest metadata only and does not echo the private output path or source text.

The HTML packet shows current approved guidance, the complete active source-level proposal set, before/replacement excerpts where available, retained normalized context, exact clocks, baseline metadata, reviewer dispositions and prior reconciliation history. Dynamic values are escaped. Link targets are displayed as text rather than clickable URLs.

The packet includes a strict Content Security Policy and no scripts, forms, buttons, images, frames, objects, external styles or hyperlinks. The manifest contains no source/context text and binds the HTML with SHA-256.

Packet creation is deterministic and idempotent for the same verified ledger state. An existing mismatched/corrupt packet is refused, never overwritten.

A packet is not an approval. It embeds the ledger revision it was created from; re-read `status` before any later write and use the current head for `reconcile`.

Full details: `docs/REVIEWER_PACKET.md`.

## Non-approving reviewer dispositions

A `disposition` request has `proposal_id`, `reviewer`, `decision` and `rationale`. Supported decisions remain:

- `retain_hold`
- `request_guidance_revision`

Both keep the proposal pending.

```sh
uv run --frozen python -m tracker.entry_review_cli disposition \
  --store /absolute/private/entry-review \
  --input /absolute/private/reviewer-disposition.json \
  --expected-revision CURRENT_HEAD_SHA256
```

Reviewer labels are operator-supplied identifiers, not authenticated identities.

## Explicit guidance reconciliation

`reconcile` is the only ledger action that can clear selected holds and advance the private approved guidance inventory.

The request has exactly:

- `source_event_revision`
- `proposal_ids`
- `reviewer`
- `rationale`
- `reviewed_at`
- `records`

```sh
uv run --frozen python -m tracker.entry_review_cli reconcile \
  --store /absolute/private/entry-review \
  --input /absolute/private/guidance-reconciliation.json \
  --expected-revision CURRENT_HEAD_SHA256
```

The selected event must be a committed observation whose affected source context was successfully extracted. For every affected source, it must be the latest retained source observation and cannot predate any cleared proposal.

All active proposals for an affected source must be selected together. This prevents partial approval of a page that supplies multiple guidance records.

The complete replacement inventory is validated using the existing rule/note validators and review-register policy. Unaffected records are unchanged. Affected records:

- keep the same record ID, park, official source and schema shape;
- use `review_status: reviewed`;
- use the exact supplied `reviewed_at` in both record and evidence;
- preserve `rights_basis` and `rights_reviewed_at`;
- must have their approved excerpt present exactly once in the retained reviewed context.

The reconciliation event records reviewer metadata, complete new records, previous/next guidance hashes, affected record/source identities and a reviewed context baseline. Old events remain unchanged.

This is private editorial approval, **not publication**. `publication_performed` remains false and the command does not write website data.

Full operator semantics: `docs/GUIDANCE_RECONCILIATION.md`.

## Context baseline versions

### Schema v1 — legacy baseline input

V1 retains the original semantics: guidance had already been approved, a later context was captured/reviewed, and a still-later source observation is compared to it.

### Schema v2 — explicit reconciliation baseline

V2 reflects the explicit review flow: a source context is captured first, a reviewer approves guidance against that retained context afterward, and future captures compare against it.

When reconciling only one source for the first time, already-validated legacy baselines from the latest observation for unaffected sources are preserved. Subsequent reconciliations replace only affected source baselines.

## Transactions and recovery

Every write is one hash-linked event plus head update inside SQLite `BEGIN IMMEDIATE`, DELETE journal mode and `synchronous=EXTRA`. The expected head is checked again inside the transaction.

A killed process may leave a rollback journal. Do not delete it manually. Use:

```sh
uv run --frozen python -m tracker.entry_review_cli recover \
  --store /absolute/private/entry-review
```

Recovery performs no source observation, reconciliation or publication. Corrupt/unrecognized databases remain errors.

WAL databases, symlinks, hard-linked databases, FIFOs, unexpected store contents, protected repository paths and nonprivate permissions are refused.

## Limits and threat model

Limits remain:

- 8 MiB input JSON
- 12 MiB per event
- 64 events
- 128 MiB aggregate event payload
- bounded Node bridge input/output and ten-second child timeout

The complete chain is replayed on reads. No automatic pruning, rotation or migration exists.

Verified guarantees concern trusted local POSIX filesystem/process-interruption cases. Not established: hardware power-loss durability, Windows/network filesystems, hostile same-user mutation, encryption, authenticated reviewer identity, multi-host operation, off-host backup/restore or indefinite retention.

Changing parser/policy code can make old events fail replay. Such failures require explicit operator investigation; never rewrite history or bypass validation to make an old chain pass.

No real NPS context was approved through this feature in the repository test suite.
