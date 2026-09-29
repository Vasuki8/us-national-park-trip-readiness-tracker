# Private entry-review ledger

## What this adds

`tracker.entry_review_store.EntryReviewStore` persists the existing source-extraction and review-gate results together. It does not replace the park-alert archive. It is a separate, offline editorial ledger for supplied page captures, context evidence, pending proposals and non-approving reviewer dispositions. No website imports it, and no public dataset is written.

The ledger is stored as `review.sqlite3` in an owner-only POSIX directory outside the repository. SQLite is provided by Python's standard library; no server, paid service, new package or account is introduced. This is local persistence, not provisioned hosted storage, encryption, access authentication or a backup service.

## Record contract

An input JSON object has exactly four fields:

- `records`: the full original approved guidance records (the current rules plus undated notes), unchanged, not the copies with overlaid review status.
- `captures`: the complete distinct-source capture batch accepted by `inspect_entry_sources`. Capture timestamps are the actual original observation times, not the import time.
- `baselines`: separately reviewed context baselines, or an empty array. Missing baselines create holds, not automatic approvals.
- `seed_register`: the initial pending register to preserve. On subsequent batches this must remain identical to the first seed; the ledger's accumulated register, not the seed, is passed to the gate.

The first batch binds the exact supplied guidance inventory. Subsequent batches must retain it. Revised approved guidance requires a separately designed reconciliation/migration, not substituting it into this ledger. Starting a new ledger does not resolve the old one's holds.

The importer runs the existing Python `inspect_entry_sources`, then invokes `scripts/entry-review-bridge.ts` to run the existing TypeScript `assessEntrySources`. Captures, extracted current/reference context, precise failure reasons, checks and the resulting proposal register are included in the same event. Matching checks are retained as well as failed/held checks. No approval date, effective period or source timestamp is renewed by importing.

Reads replay all committed observation events through those same implementations. A changed proposal or context does not pass merely because someone recomputes its stored digest. Hashes and replay are consistency checks, not source authenticity, reviewer authentication or a defence against an actor who can rewrite the entire store and source inputs.

## Commands

Run from the repository with its existing Node and Python/uv setup. Use real absolute paths outside the checkout. The parent of the new store directory must already exist. Protect capture/decision input files with owner-only permissions, for example `chmod 600` on files you control; do not put credentials into them.

```sh
uv run --frozen python -m tracker.entry_review_cli status \
  --store /absolute/private/entry-review

uv run --frozen python -m tracker.entry_review_cli record \
  --store /absolute/private/entry-review \
  --input /absolute/private/capture-batch.json \
  --expected-revision empty
```

For later writes, use the exact revision returned by `status`, rather than `empty`. A stale revision is refused, including when another writer commits after initial validation. Exact retries of already committed operations return `replayed:true`, the original `committed_revision`, and the current read-snapshot revision without adding an event or moving the head backwards.

Status and write summaries include revision IDs, counts, pending proposal references, safe reasons and timestamps. They exclude HTML, context, rationale, private paths and raw exception messages. Full evidence remains in the protected ledger and is available to local code through `EntryReviewStore.read()`; do not dump it into public CI logs or issues.

## Reviewer disposition is not approval

A disposition input has exactly `proposal_id`, `reviewer`, `decision` and `rationale`. The reviewer is an operator-supplied identifier, not an authenticated identity. Valid decisions are `retain_hold` and `request_guidance_revision`. Both append an immutable record and keep all pending proposals active. Rationale must be nonempty and bounded. There is no approve/resolve or clear-hold command.

```sh
uv run --frozen python -m tracker.entry_review_cli disposition \
  --store /absolute/private/entry-review \
  --input /absolute/private/reviewer-disposition.json \
  --expected-revision EXISTING_HEAD_SHA256
```

Unknown proposals, stale heads, unsupported approval actions and invalid reviewer metadata are rejected. Final disposition of revised guidance, renewed context approvals and reconciliation of historical holds remain a separate acceptance gate.

## Transactions and recovery

Every write is a hash-linked event and head update in one SQLite `BEGIN IMMEDIATE` transaction using DELETE journal mode and `synchronous=EXTRA`. The expected head is checked again within that transaction. An unsuccessful transaction cannot commit half an evidence/proposal pair. Prior events are never rewritten or pruned by this API.

A process killed during a write may leave a rollback journal needed by SQLite. Do not remove that file or copy only the database while a writer might be active. `status` uses a read-only connection and may refuse a database requiring recovery. Explicitly request SQLite recovery:

```sh
uv run --frozen python -m tracker.entry_review_cli recover \
  --store /absolute/private/entry-review
```

Recovery takes the write lock, lets SQLite recover, then verifies/replays the committed ledger. It adds no source observation, decision or approval. A corrupt or unrecognized database remains an error; the command does not reconstruct lost records or accept an invalid store. An interruption during initial database creation may leave an unrecognized empty file; retain it for operator inspection rather than silently treating it as new history.

WAL-format databases are refused by inspecting their documented header before opening SQLite, because opening a read-only WAL connection can otherwise create sidecar files. Other databases are not adopted. Symlinks, hard-linked files, FIFO inputs, unexpected store contents and nonprivate permissions are refused without automatically changing existing permissions.

## Limits and threat model

Limits: 8 MiB input JSON, 12 MiB per event, 64 events, 128 MiB aggregate event payload. Files are checked against a payload-plus-overhead bound before use. The complete bounded chain is replayed on reads; this deliberately trades throughput for simple verification in the offline pilot. Capacity errors preserve existing evidence. No automatic pruning, rotation or migration is implemented.

Inputs are bounded UTF-8 JSON with duplicate-key/nonfinite-value rejection. The Node bridge gets only PATH and a warning setting, not API keys, NODE_OPTIONS, proxies or arbitrary parent environment variables. The child uses trusted local code, a ten-second timeout and bounded protocol payloads. This is not sandboxing a hostile Node binary or third-party dependency.

Supported guarantee: tested local POSIX process-interruption and transaction/replay behavior with trusted filesystem ancestry and tools. Not established: power-loss behavior on specific hardware, hostile same-user changes or race-proof pathname traversal, network filesystems, Windows, encryption, multi-host operation, off-host backup/restore, indefinite retention or production approval. Native filesystem permissions are not a cryptographic confidentiality guarantee.

No real source captures, new context approvals, reviewer decisions or pending proposals were added to public product data. Real DOM compatibility, reviewed source content, final guidance reconciliation, hosted storage and publication/rollback still precede source monitoring or launch.

## Implementation references

SQLite atomic commit and recovery: https://www.sqlite.org/atomiccommit.html
SQLite synchronous modes: https://www.sqlite.org/pragma.html#pragma_synchronous
SQLite header write/read format bytes: https://www.sqlite.org/fileformat2.html
Python SQLite URI, transaction and timeout behavior: https://docs.python.org/3.12/library/sqlite3.html

These describe engine behavior, not an independent durability certification of this application.
