# Reviewed activity text and public promotion

This source-specific offline workflow follows
[private activity collection](ACTIVITY_COLLECTION.md). It prepares the paired
`data/park-activities.json` and `data/activity-source-rights.json` files. The
engineering increment uses synthetic sources and truthful synthetic review
metadata; no real listings, rights decisions, backup transfers or public-data
application are established by its tests. Things to Do rendering is subsequent
work. Profile and entry-guidance approvals cover different text scopes.

## Exact projection and rights scope

The [NPS API guide](https://www.nps.gov/subjects/developer/guides.htm) directs data
users to the [NPS disclaimer](https://www.nps.gov/aboutus/disclaimer.htm).
NPS-created government work is generally public domain unless indicated, but
the disclaimer also identifies third-party rights and requires determining
permission for the particular content. Consulted October 4, 2026. Source
provenance and an activity's credit field alone establish no reuse permission.
The technical team inspects exact retained text and official terms; consequential
licence or unclear-rights decisions belong to the owner under the permanent
policy. This workflow does not grant licences or authenticate reviewer identity.

The public dataset has `schema_version: 1`, `purpose: public_park_activities`
and five `inventories` in pilot order. It preserves every normalized record,
state, hash and original source/observation clock. Every park must have retained
successful-fetch evidence; confirmed empty inventories are valid. An initial
failed collection without successful evidence cannot become public data.
Failed/quarantined attempts may retain reviewed last-good listings, with their
degraded states intact. Empty, failed, removed and stale listings establish no
all-clear, reopening or activity availability.

Checkpoint ancestry and operational IDs are excluded. Null and empty fields,
explicit false flags, HTML-bearing text and source credits are preserved, without
inference or rendering. The complete normalized semantic hash retains its
`normalized_record` scope. Related parks remain attribution, physical geography
unconfirmed, and agency, difficulty and permit needs null. Source issue/update/
publication clocks remain null. Copying, review and publishing never renew source
age; the independent 168-hour activity freshness policy remains applicable.

The separate rights manifest has exactly `schema_version`, `purpose:
public_park_activity_text_rights`, `reviewed_at`, `review_method:
official_nps_policy_and_exact_activity_review`, the existing exact NPS ownership/
marks policy, and `records`. Review time must follow every attempted park check,
including confirmed empty inventories. This is not a separate licence-expiry
policy.

One rights record is required for each retained listing, in pilot then record-ID
order. Each binds `park_code`, `activity_id`, the fixed unkeyed API `source_url`
and `content_hash`, with `classification: nps_government_text`,
`use_scope: normalized_activity_text_and_metadata`, and false third-party,
marks and media reproduction flags. IDs may repeat across parks; the binding
includes the park. Review covers every public string, including long
descriptions, related-park labels and credit. Do not fabricate classification,
review time or flags to pass validation. Unclear or third-party text requires
resolution before this complete projection can be promoted; there is no hidden
partial-approval or omission mode. Images and NPS marks are outside this scope.
A future renderer must escape retained text and never activate embedded HTML,
media or arbitrary URLs.

## Private approval and recovery

Read [DURABLE_COLLECTION_SESSION.md](DURABLE_COLLECTION_SESSION.md) before a real
session. Use existing owner-only WSL/Linux parents outside the checkout and
`umask 077`. Paths below are placeholders. Commands read no API key, make no
requests and perform no public writes. Only explicit `approve --approve` records
an operator approval decision.

```sh
uv run --frozen python -m tracker.activity_release approve --approve \
  --checkpoint /absolute/private/activities/checkpoint.json \
  --rights /absolute/private/review/activity-rights.json \
  --output /absolute/private/review/reviewed-activities.json

uv run --frozen python -m tracker.activity_release verify \
  --bundle /absolute/private/review/reviewed-activities.json

uv run --frozen python -m tracker.activity_release restore \
  --bundle /absolute/private/downloaded/reviewed-activities.json \
  --output /absolute/private/recovery/reviewed-activities.json
```

The immutable `private_reviewed_park_activities` bundle includes the checkpoint,
exact `public_activities` projection, rights manifest and approval. Approval binds
checkpoint ID, complete projection hash and rights hash; approval time follows
rights review. Bundle identity binds the complete core. Hashes establish
integrity, not source authenticity, an authenticated human review or off-host
backup. Operator decision metadata must be truthful.

Public projection and rights each permit 42,008,576 canonical bytes (40 MiB plus
64 KiB). Their public files permit at most one additional final LF. An approved
bundle permits 126,091,264 bytes (120 MiB plus 256 KiB). A paired replacement
patch permits 168,099,844 bytes (160 MiB plus 320 KiB plus four final-LF bytes).
Every read, encoding, digest and installation uses the appropriate explicit
limit. Legacy 8/10 MiB defaults are unchanged. Never trim records or rights
bindings to fit; refusal precedes output locks where candidate size is known.
These ceilings support the existing per-record and per-inventory limits; they
are not a target visitor payload.

Neutral private-file primitives require canonical external paths, existing
owner-only parents, single-link regular inputs, fresh output/lock names and
0600 outputs. Checkpoint and rights inputs cannot coincide with the output or
its lock. No overwrite, parent creation, permission repair or lock stealing
occurs. Interrupted execution after installation can leave completed evidence;
preserve and verify it before retrying. Abandoned locks and uncertain multi-link
files require deliberate inspection. See the collection guide's commit boundary.

Before real backup, extend the exact selected inventory in
[GITHUB_PRIVATE_BACKUP.md](GITHUB_PRIVATE_BACKUP.md) with the verified approved
activity bundle. Preserve earlier ledger/alert/profile evidence; exclude keys,
raw responses, locks, temporary files and public CI artifacts. Reuse private
repository identity/visibility checks, byte-preserving Git settings, exact
staging, fresh authenticated download and fresh private restore. Verify bundle
identity and canonical bytes, and retain transfer/recovery receipts privately.
Checkpoint-only or earlier profile recovery cannot cover the activity approval.

## Prepare and recheck the public patch

```sh
uv run --frozen python -m tracker.activity_release prepare-promotion \
  --bundle /absolute/private/review/reviewed-activities.json \
  --output /absolute/private/review/activities.patch

uv run --frozen python -m tracker.activity_release check-promotion \
  --bundle /absolute/private/review/reviewed-activities.json \
  --patch /absolute/private/review/activities.patch \
  --candidate-id EXACT_PREPARATION_ID
```

Preparation reads the fixed two-file public base and writes only its paired Git
patch to private storage. Both public files absent is the initial case; any
present pair must be complete, ordinary nonsymlink files in an ordinary data
directory, strict UTF-8/JSON and canonical compact sorted bytes with at most one
final LF. Duplicate fields, pretty formatting, invalid bytes and partial pairs
are refused. The two exact activity paths use `-text` Git attributes to preserve
bytes on Windows. Only the public projection and manifest enter the patch;
private checkpoint/approval envelopes remain private.

Candidate identity binds the reviewed bundle, exact base bytes or absence, and
exact patch bytes. Source attempt/success clocks cannot rewind. Equal attempted
instants require exact snapshot equality. Retained IDs preserve first
observations; unchanged content preserves changed-observation clocks, while
changed/new content needs observations strictly after public last success.
Failed/quarantined candidates must preserve exact public last-good records and
successful-fetch clocks. An unpublished intermediate success followed by failure
cannot be inferred from one checkpoint's parent reference.

The populated-inventory half-drop guard is also checked against public state,
so a private fork cannot bypass it. A removed listing never proves reopening or
availability. There is no history replay or removal-approval override in this
increment.

Recheck regenerates the entire candidate and compares identity and patch without
writes. Run it immediately before separately authorized `git apply --check` and
application with unchanged inputs. This is point-in-time consistency, not a
production lock; changed inputs require another check. These tools never apply,
build, deploy, schedule, enable indexing or add ads.

CLI exit 0 means the named offline operation completed; exit 2 means sanitized
refusal/interruption. Reports contain only operation, identities/counts and
explicit action flags. No source text, private paths or credentials are emitted.
A refused post-install approval may still exist and must be verified before retry.

## Build gates and next step

The build validates an optional activity/rights pair with the same Python and
TypeScript scope, hashes, source URL, Unicode and microsecond-clock semantics.
When present, read-only release readiness additionally requires an exact matching
approved activity bundle and independently verified recovery copy under a
separate canonical private parent. This only reduces existing review, backup and
rights gate readiness; no profile or alert evidence covers activities. Matching
local copies prove integrity, not actual remote transfer. See
[RELEASE_READINESS.md](RELEASE_READINESS.md).

Next: conduct a deliberate real collection and exact text-rights review, verify
approved-bundle remote recovery and prepare/recheck the reviewed public pair.
Then build Things to Do from validated reviewed listings, with official links,
unknown fields and original freshness. A live release still needs refreshed
conditions, complete release checks and applicable deployment authorization.
