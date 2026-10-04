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

The legacy complete public dataset has `schema_version: 1`, `purpose: public_park_activities`
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

## Reviewed minimal catalog (version 2)

Version 2 uses the same public pair paths and purpose names. It offers exact
titles, safe official listing links and optionally the complete source category
list. It omits descriptions, source credits, flags, related-park labels and
embedded HTML. It does not reinterpret an existing version 1 approval. The first
real checkpoint remains private and unapproved; synthetic contract tests do not
establish rights or approval for any real listing.

A private disposition file has exactly `schema_version: 1`, `purpose:
private_activity_catalog_dispositions`, `checkpoint_id`, `reviewed_at` and
`records`. Include one ordered row for every retained listing, in pilot then ID
order, binding `park_code`, `activity_id`, `source_content_hash`, `decision:
selected|withheld` and `categories: published|withheld`. Whole-record withholding
requires categories withheld. Review must follow the checkpoint attempt.
There is no default selection, rewritten text or free-form reason in this file.

Every inventory retains all original source headers and clocks, with
`schema_version: 2` and an additional `source_records` array. This lists every
source ID, original normalized `content_hash`, its `hash_scope:
normalized_record`, first/changed observation clocks and `publication_status:
selected|withheld`. The original hash describes the private full record and
cannot be recomputed from its smaller public view. Editorial withholding is
distinct from source removal, confirmed empty and degraded source states.

The public `records` array contains selected listings only. Title and URL are
mandatory exact source values; categories are exact source values when published.
`category_scope: withheld` requires null categories, while published categories
preserve source null or an empty array. Titles/category names are nonempty plain
text, at most 1,024 Unicode scalars, with no angle brackets or control characters.
URLs must be official NPS links within the queried park or global `/thingstodo/`,
with neither query nor fragment markers. Unsafe fields require withholding,
not silent rewriting.

Each view preserves the original observations and `source_content_hash`, and
adds `view_hash` over all view fields except `view_hash` and `hash_scope`.
`hash_scope: catalog_view` identifies the narrower digest. Geographic relationship
stays unconfirmed, availability not verified, and responsible agency, difficulty,
permit requirement and source update time null. The catalog asserts no current
availability, reopening or permit exemption.

Rights version 2 adds `projection_hash` over the complete public dataset.
Each selected listing has one row binding park, activity ID, fixed unkeyed API
source URL, `source_content_hash` and `view_hash`, with
`classification: nps_government_text`,
`use_scope: activity_catalog_title_url_and_optional_categories` and the same
three false reproduction flags. The existing exact NPS policy and review method
remain required. Rights review follows every attempted source check, including
empty or wholly withheld inventories. This narrower assertion applies to the
published title/URL/category view; it grants no rights to omitted private prose.

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

For a separately reviewed version 2 catalog, add the private disposition input:

```sh
uv run --frozen python -m tracker.activity_release approve --approve \
  --checkpoint /absolute/private/activities/checkpoint.json \
  --dispositions /absolute/private/review/activity-dispositions.json \
  --rights /absolute/private/review/activity-catalog-rights.json \
  --output /absolute/private/review/reviewed-activity-catalog.json
```

Version 2 approval retains the unchanged checkpoint and exact dispositions.
It additionally binds `dispositions_hash`; verification regenerates the entire
public catalog and verifies its source/view/rights hashes. Disposition review
must precede or equal rights review, which precedes or equals approval. Without
dispositions, approval keeps the complete version 1 contract. Verify, restore,
backup and paired patch commands accept either version.

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
0600 outputs. Checkpoint, rights and optional disposition inputs cannot coincide with the output or
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
exact patch bytes. Source attempt/success clocks cannot rewind. For version
1-to-1 replacement, equal attempted instants require exact snapshot equality.
If either side is version 2, equal attempted instants require exact source
headers and original source summaries; a newly reviewed catalog may change its
selection/categories without renewing source clocks. Retained IDs preserve first
observations; unchanged content preserves changed-observation clocks, while
changed/new content needs observations strictly after public last success.
Failed/quarantined candidates must preserve exact original last-good source
hashes, observations and successful-fetch clocks. Version 1 retains its stricter
complete-record equality. An unpublished intermediate success followed by failure
cannot be inferred from one checkpoint's parent reference.

The populated-inventory half-drop guard is also checked against public state,
so a private fork cannot bypass it. Version 2 checks all source summaries, not
the smaller published selection. A removed listing never proves reopening or
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

Next: review the retained real checkpoint into explicit selected/withheld
catalog dispositions, resolve the exact published text-rights scope, verify
approved-bundle remote recovery and prepare/recheck the reviewed public pair.
Then build Things to Do from validated reviewed listings, with official links,
unknown fields and original freshness. A live release still needs refreshed
conditions, complete release checks and applicable deployment authorization.
