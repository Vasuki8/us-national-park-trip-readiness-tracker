# Private park-profile collection

This is the separate NPS `/parks` source contract for the five pilot parks.
It collects introductions, official identity, activity categories and labelled
seasonal weather context into an immutable private checkpoint. Categories are
not individual activities; seasonal text is not a forecast. It excludes photos,
coordinates, fees, contacts and other unrelated fields.

The commands never write public data, build the website, approve source rights,
deploy or schedule. A successful source request, checkpoint, local restore or
review export does not establish publication readiness. No real profiles were
collected while implementing this tooling.

## Storage and commands

Read [DURABLE_COLLECTION_SESSION.md](DURABLE_COLLECTION_SESSION.md) before a
real operator session. Use Python 3.12+ in the frozen uv environment, a separate
`umask 077` session and the WSL Linux filesystem on Windows. All example paths
are placeholders for existing owner-controlled private directories outside
the entire checkout. The immediate parent must already exist and be owner-only;
the tools never create parent directories or repair permissions.

```sh
# First collection: an explicit new checkpoint, all five parks.
uv run --frozen python -m tracker.profile_stage collect --live \
  --output /absolute/private/profiles/first-checkpoint.json

# Later collection: retain the explicit verified baseline and use a new output.
uv run --frozen python -m tracker.profile_stage collect --live \
  --previous /absolute/private/profiles/first-checkpoint.json \
  --output /absolute/private/profiles/next-checkpoint.json

# Offline integrity check; no key or requests.
uv run --frozen python -m tracker.profile_stage verify \
  --checkpoint /absolute/private/profiles/next-checkpoint.json

# Offline rehearsal into a fresh private destination.
uv run --frozen python -m tracker.profile_stage restore \
  --checkpoint /absolute/private/downloaded/checkpoint.json \
  --output /absolute/private/recovery/restored-checkpoint.json

# Private review material; this is not a public export or approval record.
uv run --frozen python -m tracker.profile_stage export-review \
  --checkpoint /absolute/private/profiles/next-checkpoint.json \
  --output /absolute/private/review/profile-candidate.json
```

Only `collect --live` reads the private `NPS_API_KEY` environment variable,
after validating the previous checkpoint, clock, destination and output lock.
Do not pass keys through command arguments, URLs, chat, source files or frontend
variables. Invalid or missing keys prevent requests. Offline commands do not
consult the key. Malformed argument and operation reports use fixed codes and
never echo paths, provider text, keys or arbitrary exception messages.

## Request and source interpretation

The transport constructs only the fixed HTTPS `/parks` endpoint with one of
`yose`, `romo`, `yell`, `zion`, `grca`, `limit=1` and `start=0`. Authentication is
in `X-Api-Key`; the default opener refuses redirects. Each request has a
20-second timeout, at most three attempts and waits capped at 30 seconds.
Bodies are bounded to 4,000,000 bytes. Duplicate JSON keys, nonfinite JSON constants,
invalid JSON/UTF-8, oversized bodies and configured-key echoes are refused.
Echo checks inspect decoded string values and object keys, including ignored
fields, both literally and after one URL-percent-decoding pass. Arbitrary
other encodings are not interpreted. HTTP headers, raw bodies and rejected
source text are never written to checkpoints or reports.

Malformed/scoped/echoed responses produce quarantined attempts; exhausted
HTTP/network failures produce failed attempts. Each preserves its park's
validated last-good profile and successful-fetch clock. A first failed attempt
has no profile or successful-fetch time. Unexpected programming failures stop
the batch. Source issue/update/publication timestamps remain null because this
API contract supplies no trustworthy clocks for these normalized fields.
Observation and attempted/successful-fetch clocks describe collection only.

Profile freshness has its own initial 168-hour policy, independent of alert
freshness. Failed/quarantined attempts never count as a successful refresh.
An offline verify, copy, build or future publication must not reset that age.

The [official NPS guide](https://www.nps.gov/subjects/developer/guides.htm)
documents header authentication and private-key handling; the
[official schema](https://www.nps.gov/subjects/developer/customcf/swagger.json)
documents park scoping and pagination. Consulted October 2, 2026. New text-use
scope and any future images still require their separate rights review.

## Checkpoints, concurrency and interruptions

Each checkpoint contains all five attempted snapshots in pilot order, one
batch attempt clock, a nullable parent checkpoint ID and a canonical digest.
Inputs are fully checked before requests, and later collection clocks must be
strictly newer. Existing checkpoint files stay unchanged. The parent ID is a
lineage reference: verifying a checkpoint does not verify that its parent
exists or establish a replayed history chain.

There is no mutable current pointer. Operators explicitly select the baseline.
Concurrent writers to the same output are refused by its exclusive `.lock`;
different outputs may form branches from the same parent. There is no global
latest-head or cross-output ordering claim.

The final filename is installed without overwrite only after all attempts and
the complete candidate validate. Before installation, interruption can lose
earlier in-memory source results; it leaves no completed checkpoint and the
previous baseline remains usable. A later retry is a new source attempt.
After installation, directory fsync, cleanup or reporting can fail while the
checkpoint remains present. Preserve it and run offline `verify` before
retrying; never assume a nonzero exit means that no file was installed.

Abandoned locks and orphan temporary files are not stolen, pruned or repaired
automatically. Confirm writers have stopped and inspect/copy the private state
before deliberate cleanup. A crash between final linking and temporary removal
can leave two hard links; verification refuses that file until deliberate
inspection/cleanup. Do not remove locks merely because they are old.

Relative paths, traversal, symlinks, checkout descendants/ancestors and their
canonical aliases are refused. Existing parents must be owner-controlled and
have no group/other access. Retained inputs must be owner-only, single-link
regular files. Locks, temporary files and outputs use 0600. Checkpoints and
review envelopes are bounded to 8 MiB. This is trusted local-filesystem tooling;
hashes are integrity checks, not signatures, and synthetic interruption tests
do not prove hardware power-loss or network-filesystem durability.

## Reports and exit codes

Reports contain checkpoint IDs, clocks, park/profile counts and collection
status counts. `network_attempted` means the scoped transport was invoked,
including a failed attempt; it is not proof of provider availability. Reports
always keep approval, publication and public-data-write flags false.

Collection exit 0: all five attempts successfully checked and retained.
Collection exit 1: the checkpoint was retained with failed/quarantined states.
Exit 2: arguments, configuration, local state or execution failed; inspect and
verify any output before retrying. Offline command success exits 0 even if the
verified checkpoint contains degraded states; integrity is distinct from a
successful source check. Export reports `source_rights_status: not_checked`.

## Backup and public-promotion boundaries

`restore` creates a fresh canonical copy and re-verifies its checkpoint ID.
This proves local checkpoint recovery, not an off-host backup. Earlier verified
ledger and alert backups do not cover this new dataset.

Before a real profile backup, extend the exact private inventory described in
[GITHUB_PRIVATE_BACKUP.md](GITHUB_PRIVATE_BACKUP.md) for the selected profile
checkpoint. Apply its private-repository identity/visibility checks, owner-only
WSL transfer/recovery storage, byte-preserving Git configuration, exact staging
inventory, normal push and fresh authenticated download. Select only verified
immutable checkpoint files; exclude keys, locks, temporary files, raw responses,
working directories and public CI artifacts. Preserve earlier checkpoints.
Verify the freshly downloaded checkpoint and restore it into a new destination;
compare ID and canonical bytes and retain remote/recovery receipts privately.
No remote copy or real recovery is claimed by this development increment.

The review envelope retains the exact checkpoint, its identity, unchanged clocks
and degraded states. Source rights remain not checked and approval remains
false. It is not accepted by the existing alert promotion tools or website.
A source-specific reviewed public-profile schema, approval/rights binding and
promotion tool remain subsequent work before Overview/When to Visit consume
real profiles. No release gate is cleared by these commands.
