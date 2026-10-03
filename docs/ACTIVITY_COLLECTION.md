# Private activity collection

The separate NPS `/thingstodo` workflow collects individual listings for the five
pilots into an immutable private checkpoint. See
[ACTIVITY_FOUNDATION.md](ACTIVITY_FOUNDATION.md) for field interpretation, unknown
values, hashes, pagination and independent freshness. This engineering increment
uses synthetic sources; no real activities or remote backup were collected.

## Deliberate commands and storage

Read [DURABLE_COLLECTION_SESSION.md](DURABLE_COLLECTION_SESSION.md) before any
real operator session. Use Python 3.12+ with frozen uv dependencies, a separate
`umask 077` session and the WSL Linux filesystem on Windows. These absolute paths
are placeholders for existing owner-controlled private directories outside the
entire checkout. Immediate parents must already exist with owner-only access.
Commands do not create parents or repair permissions.

```sh
uv run --frozen python -m tracker.activity_stage collect --live \
  --output /absolute/private/activities/first-checkpoint.json

uv run --frozen python -m tracker.activity_stage collect --live \
  --previous /absolute/private/activities/first-checkpoint.json \
  --output /absolute/private/activities/next-checkpoint.json

uv run --frozen python -m tracker.activity_stage verify \
  --checkpoint /absolute/private/activities/next-checkpoint.json

uv run --frozen python -m tracker.activity_stage restore \
  --checkpoint /absolute/private/downloaded/activity-checkpoint.json \
  --output /absolute/private/recovery/activity-restored.json

uv run --frozen python -m tracker.activity_stage export-review \
  --checkpoint /absolute/private/activities/next-checkpoint.json \
  --output /absolute/private/review/activity-candidate.json
```

Only deliberate `collect --live` reads `NPS_API_KEY`. Before that read, every
baseline, source identity, batch/attempt clock and failure capacity has been
validated, the destination checked and its exclusive lock acquired. Invalid
storage, any malformed park baseline, a nonadvancing clock or insufficient
last-park failure capacity makes no key lookup or source request. Keys must be
nonempty printable ASCII without spaces/control characters. Do not pass them
through arguments, URLs, chat, committed files or frontend variables.

Offline commands never consult the key or source. No command approves rights,
writes public data, builds the site, deploys, schedules or creates a mutable
latest pointer. `--live` expresses the operator action; it is not evidence of
owner approval, source rights or release readiness.

## Requests and response refusal

`activity_transport.request_activity_page` requests only the fixed HTTPS NPS
`/thingstodo` endpoint, one supported pilot, `limit=50` and the actual requested
integer offset from 0 through 4,999. The collector advances by returned page
length, not an assumed multiple of 50. Authentication stays in `X-Api-Key`;
the default opener refuses redirects. Each page has a 20-second socket timeout,
at most three attempts and waits capped at 30 seconds. This is not a guaranteed
whole-batch deadline. Retryable statuses are 429, 500, 502, 503 and 504;
terminal HTTP and exhausted network/read failures produce failed attempts.

Read at most 4,000,001 bytes and accept at most 4,000,000 per response. This
intentionally bounds raw pages more tightly than a complete normalized inventory;
large provider pages may quarantine. Reject invalid JSON/UTF-8, duplicate object
keys, excessive nesting, nonfinite constants and numeric exponent overflow,
including ignored fields. A non-object response is refused. Inspect all decoded
object keys/string values for the configured key literally and after exactly
one URL-percent-decoding pass, including out-of-scope fields. Other arbitrary
encodings are not interpreted. Payload strings are not rewritten.

Parser/body/credential refusals become quarantined attempts; classified transport
failures become failed attempts. A late-page error discards the entire partial
candidate, preserving accepted records and their original successful/observation
clocks. No HTTP headers, raw bodies, rejected text or exception messages enter
checkpoints or reports. Unexpected programming exceptions stop the batch through
the sanitized CLI boundary. Listings retain attribution and unknown geography,
agency, difficulty and permit needs; descriptions and credits prove no rights.
Source issue/update/publication clocks stay null.

The [official NPS guide](https://www.nps.gov/subjects/developer/guides.htm) documents
header authentication; the
[official schema](https://www.nps.gov/subjects/developer/customcf/swagger.json)
documents park scoping and pagination. Consulted October 3, 2026 for this source
contract; the implementation tests make no authenticated requests.

## Immutable checkpoints and limits

Each checkpoint contains five attempted inventories in pilot order, one batch
attempt clock, a nullable parent checkpoint ID and a canonical SHA-256 identity.
Verification checks the complete schema, source identities, states, hashes and
clocks. The parent ID references lineage only; it does not prove parent
availability, replayed history, source authenticity or a signature.

All baselines are validated and defensively copied before the first factory
callback. Collection strictly advances the prior batch clock. Each park remains
bounded to 8 MiB. The all-five checkpoint is bounded to 40 MiB plus 64 KiB
(42,008,576 bytes); the private review envelope permits an additional 4,096 bytes.
Encoding, hashing and reading use these explicit bounds. Existing callers retain
their 10 MiB canonical-object and 8 MiB private-read defaults; no profile or
editorial limit is silently widened. Future successful candidate data must also
fit before installation. An oversized complete candidate stops without a new
checkpoint, preserving the explicit previous file.

The neutral `private_checkpoint_io` primitives reuse existing editorial POSIX
path/permission guards. They reject relative paths, traversal, symlink ancestry,
checkout descendants/ancestors and canonical aliases, insecure parents,
hardlinked inputs and nonregular files. Retained files must be owner-only,
single-link regular files. Output locks, temporary files and installed outputs
use 0600. The destination must be fresh. Same-output competing writers are
refused; separate outputs can branch from one explicit parent. No global latest
head or cross-output ordering is claimed. Existing profile/release installers
remain unchanged.

Installation uses a same-directory temporary file, file fsync, an exclusive hard
link with no overwrite, temporary removal and directory fsync. Before linking,
interruption may lose in-memory results but leaves no completed checkpoint;
the baseline remains usable. After linking, sync, cleanup or reporting failure
may leave completed output. Preserve and verify it offline before retrying;
exit 2 does not establish that no checkpoint was installed.

Abandoned locks, preexisting temporary files and uncertain multi-link outputs are
not stolen, pruned or repaired automatically. Confirm writers stopped and inspect
private state before deliberate cleanup. A crash/cleanup failure between link and
temporary removal can leave two links; verification refuses that file until
operator inspection resolves it. This is trusted local POSIX filesystem tooling;
synthetic tests do not prove hardware power-loss or network-filesystem durability.

## Reports, recovery and next step

Reports include only operation, identity, batch clock, park/retained-record counts
and successful/failed/quarantined counts. Retained-record counts describe stored
evidence, not available activities. `network_attempted` means transport invocation,
including failure; it does not prove a connection or provider availability.
Argument/operation errors use fixed codes without echoing paths, keys or bodies.

Collection exit 0 means all five inventories were successfully checked and
retained. Exit 1 means a complete checkpoint was retained with degraded states.
Exit 2 means arguments, configuration, local state or execution failed/interrupted;
inspect any output before retrying. Offline successful verification exits 0 even
for a degraded checkpoint: integrity is distinct from a successful source check.

Fresh restore verifies the source, installs a canonical copy without new clocks
and reverifies its identity. Review export preserves the complete checkpoint and
degraded states with `source_rights_status: not_checked`, approval false,
publication false and public-data writes false. Neither is a public exporter.

Before real backup, deliberately extend the exact inventory in
[GITHUB_PRIVATE_BACKUP.md](GITHUB_PRIVATE_BACKUP.md) for selected verified activity
checkpoints. Reuse identity/visibility checks, owner-only transfer/recovery paths,
byte-preserving Git settings, exact staging and fresh authenticated download.
Exclude credentials, raw responses, locks, temporary files and public CI
artifacts; preserve earlier ledger, alert and profile checkpoints. Verify the
downloaded file, fresh restore, identity and canonical bytes, and retain receipts
privately. No off-host transfer or real recovery is claimed here.

Next, implement the separate reviewed activity text-rights/public-projection
contract before real collection and public promotion. Things to Do rendering
will consume only validated reviewed public data. Image publication, named
weather, schedules, indexing, ads and live deployment retain their own gates.
