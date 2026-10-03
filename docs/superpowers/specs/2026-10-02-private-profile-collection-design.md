# Private park-profile collection

## Purpose and scope

Extend the five-park profile normalizer with usable private collection and
review-candidate tooling. This implements the foundation assessment's next
source contract. The owner delegates ordinary technical design and execution
to Codex; no additional infrastructure, source licence or product decision is
needed for this synthetic implementation increment.

Public data, frontend behavior, dependencies, workflows and the deployed
artifact remain unchanged. No real collection, credentials, remote backup,
promotion, deployment or schedule is performed while implementing/testing.

## Transport

`tracker/profile_transport.py` exposes
`request_profile_page(park_code, start, key, *, opener=None, sleep=time.sleep)`.
Only the five pilot codes and integer offset zero are accepted. Requests use
the fixed HTTPS NPS `/parks` endpoint, `parkCode`, `limit=1`, `start=0`, a private
`X-Api-Key` header, JSON accept header and the existing project user agent.
Reject invalid keys before any request. Disable redirects in the default
opener. Bound each response to 4,000,000 bytes and each request to 20 seconds;
allow three attempts with existing transient HTTP/network retry conventions
and a maximum 30-second wait. Never retain response headers or raw bodies.

Decode strict JSON (duplicate keys and nonfinite constants refused). Reject a
configured-key echo anywhere in decoded payload strings or object keys,
checking literal values and one URL-percent-decoding pass before normalization.
Malformed/oversized/echoed bodies raise a fixed `ProfileError`
and become quarantined attempts through `collect_profile`; terminal transport
failures raise `ProfileCollectionError` and become failed attempts. Unexpected
programming exceptions propagate. Error messages never include source bodies,
URLs, keys or arbitrary exception text.

## Immutable checkpoint workflow

Use explicit files, not a mutable current pointer or a new event archive.
`tracker/profile_checkpoints.py` owns validation, collection, verification,
restore and review export. A checkpoint contains exactly `schema_version: 1`,
`purpose: private_park_profile_checkpoint`, nullable `parent_checkpoint_id`,
`checked_at`, `profiles` in pilot order and a canonical SHA-256 `checkpoint_id`
over the other fields. All five snapshots must have an attempted check at the
same explicit clock. No initial/unattempted snapshots are valid checkpoints.
Publisher clocks stay null. Input and return values are defensive copies.

`collect_checkpoint(destination, previous_path, now, fetch_for)` validates the
entire previous checkpoint, every destination boundary and a strictly
advancing collection clock before its first request. `fetch_for(code)` returns
the scoped callback consumed by `collect_profile`. Acquire an exclusive lock
beside the output before requests; refuse an existing output without fetching.
Collect all five in order, preserving last-good data on failed/quarantined
attempts. Atomically create one canonical output only after all attempts and
the final checkpoint validate. An interruption before installation leaves no
completed output; successful requests before that point cannot be recovered.
Installation is the commit point: a subsequent fsync/cleanup/report failure may
leave the output present. Preserve it and verify offline before retrying.
Locks are not stolen or automatically repaired. Different output paths may
produce concurrent branches from the same parent; no global latest head or
cross-output serialization is claimed.

`verify_checkpoint(path)` is offline/read-only. It validates the complete
bounded self-contained current state and returns its checkpoint. The parent
ID is a lineage reference, not independently verified history; old checkpoint
files are retained separately. No whole-chain replay is claimed.

`restore_checkpoint(source, destination)` verifies source before creating a
fresh destination, then verifies the exact restored ID. This is a local copy
and recovery primitive, not proof of a remote backup. A later operator session
must extend the private GitHub backup inventory for this new dataset, freshly
download, verify and restore; existing ledger/alert receipts do not cover it.

`export_review_candidate(source, destination)` writes a private JSON envelope
containing the verified checkpoint and its identity, with `approval_performed`,
`publication_performed` and `site_data_written` false and
`source_rights_status: not_checked`. It is not public data or an approval
record. Degraded profiles and all source clocks remain intact.

## Private filesystem and bounds

Reuse `entry_review_io.check_path`, `private_stat`, `read_private_json` and
strict parsing through thin source-specific wrappers. Require POSIX, absolute
external paths, no traversal or symlink ancestry, an existing owner-only
parent, and owner-only single-link regular inputs. Refuse existing insecure
files/directories without chmod or migration. Inputs/outputs are bounded to
8 MiB; canonical bytes plus the envelope must fit before writing. Use 0600
same-directory temporary files, flush/fsync and exclusive link creation,
then directory fsync. Never overwrite an output. Refuse overlapping source,
destination and lock paths before changing anything. This is trusted local
filesystem tooling, not protection against a hostile same-user process or a
hardware/network filesystem durability guarantee. Hashes are not signatures.

If interruption leaves a temporary hard link, verify refuses the multi-link
file until a deliberate operator inspection and cleanup. No automatic cleanup
of retained evidence or abandoned locks is provided.

## CLI and verification

`python -m tracker.profile_stage` provides `collect --live`, `verify`,
`restore` and `export-review`; file paths are always explicit. Only collection
reads `NPS_API_KEY`, after validating files/clocks/storage. Offline commands
need no key or transport. CLI reports bounded counts, IDs, statuses and fixed
codes; provider text, paths and argument echoes are excluded. Collection exit
0 means five successful checks, 1 means a completed degraded checkpoint, and
2 means refusal/interruption. Offline success exits 0. Argument errors are
sanitized. Neither CLI success nor export establishes publication readiness.

Synthetic tests cover scoped authentication, redirects, body/parser/retry
bounds, echo refusal, retention, immutable files, owner-only permissions,
corruption, locks, interruptions, input immutability, restore, private export,
offline CLI and safe errors. Full existing CI remains the integration gate.
