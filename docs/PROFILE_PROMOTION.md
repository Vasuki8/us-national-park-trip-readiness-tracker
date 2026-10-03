# Reviewed park-profile text and public promotion

This source-specific offline workflow follows [private profile collection](PROFILE_COLLECTION.md).
It prepares two public files, `data/park-profiles.json` and
`data/profile-source-rights.json`. Both now contain the first owner-approved
five-park profiles and exact text-rights bindings. Real private collection,
reviewed-bundle recovery and paired promotion are recorded in the
[current handoff](../PROJECT_STATUS.md). No real profiles or approvals were
produced while initially developing these tools. The website consumes the
validated pair for Overview and When to Visit; see the
[development guide](DEVELOPMENT.md) for rendering and freshness behavior.
The existing entry-guidance manifest approves a different
text scope and cannot approve descriptions or seasonal context.

## Rights and exact review

The [official NPS API guide](https://www.nps.gov/subjects/developer/guides.htm)
directs API users to the [NPS disclaimer](https://www.nps.gov/aboutus/disclaimer.htm).
NPS-created works are generally public domain unless indicated, but the disclaimer
also covers third-party material and requires determining reuse permissions.
The [Arrowhead policy](https://www.nps.gov/subjects/partnerships/arrowhead-requests.htm?fullweb=1)
protects the service mark. Consulted October 2, 2026. API provenance alone does
not settle exact text rights. The technical team reviews the retained material
and official terms; consequential licence or unclear-rights decisions belong to
the owner under the permanent policy.

The public projection preserves the complete five normalized snapshots and
their original clocks. It excludes checkpoint ancestry and operational IDs.
All five must contain a successfully retained profile, even if the most recent
attempt failed or was quarantined. Missing optional fields remain null; category
names are not individual activities, and seasonal context is not a forecast.
Source issue/update/publication clocks remain null. Copying or publishing never
renews successful-source age.

The separate rights manifest has exactly:

- `schema_version: 1`, `purpose: public_park_profile_text_rights`;
- `reviewed_at`, at or after every snapshot's attempted check;
- `review_method: official_nps_policy_and_exact_profile_review`;
- `policy`, the existing official ownership/marks URLs and government-work notice,
  with third-party material, marks and raw private captures excluded; and
- five `records` in pilot order, each binding `park_code`, `profile_id`, the fixed
  unkeyed API `source_url` and normalized `content_hash`, classified as
  `nps_government_text` with `use_scope: normalized_profile_text_and_category_names`
  and all three reproduction flags false.

Prepare this manifest in private storage only after reviewing the exact text.
Do not fill in a fabricated review time or classification to pass validation.
Images, marks, attribution-dependent third-party content and raw captures are
outside this scope. The normalized semantic hash covers identity, introduction,
seasonal text and category names; the approval additionally binds every field
and clock in the complete public projection and manifest.

## Private approval and recovery

Read [DURABLE_COLLECTION_SESSION.md](DURABLE_COLLECTION_SESSION.md) before a
real session. Use WSL/Linux POSIX storage, existing owner-only parents outside
the checkout, and `umask 077`. The following paths are placeholders. Offline
commands require no source key. Only the explicit `approve --approve` operation
records approval; verification, restore and patch preparation do not approve.

```sh
uv run --frozen python -m tracker.profile_release approve --approve \
  --checkpoint /absolute/private/profiles/checkpoint.json \
  --rights /absolute/private/review/profile-rights.json \
  --output /absolute/private/review/reviewed-profiles.json

uv run --frozen python -m tracker.profile_release verify \
  --bundle /absolute/private/review/reviewed-profiles.json

uv run --frozen python -m tracker.profile_release restore \
  --bundle /absolute/private/downloaded/reviewed-profiles.json \
  --output /absolute/private/recovery/reviewed-profiles.json
```

The immutable bundle contains the verified checkpoint, exact public projection,
manifest and decision. Approval binds checkpoint ID, complete projection and
rights hashes, with an approval time at or after rights review. A bundle digest
also binds the full retained envelope. Hashes are integrity checks, not
signatures, proof of source authenticity or independent proof that review
actually occurred. The operator is responsible for truthful decision metadata.

The existing private-file guards and writer enforce owner-only, single-link
regular inputs, no symlink/traversal/checkout aliases, no overwrite, exclusive
output locks and 0600 outputs. Bundles and patches are bounded to 8 MiB before
writing. Parent directories are not created or repaired. The collection guide's
interruption boundary also applies: failure after installation can leave an
output. Verify it before retrying; abandoned locks and temporary files are not
automatically repaired or removed.

Extend the exact selected private GitHub backup inventory in
[GITHUB_PRIVATE_BACKUP.md](GITHUB_PRIVATE_BACKUP.md) with this verified immutable
bundle, including its checkpoint and approval/rights bindings. Preserve earlier
evidence. Exclude credentials, raw responses, locks, temporary files, working
directories and public CI artifacts. Check private repository identity and
visibility, preserve bytes, push only the reviewed inventory, freshly download,
verify and restore to a new private destination, and compare bundle ID and
canonical bytes. Retain remote and recovery receipts privately. A local copy
does not prove an off-host backup; earlier ledger/alert receipts do not cover
profile data. Checkpoint-only recovery cannot substitute for this approved-bundle
recovery.

## Prepare, recheck and apply

```sh
uv run --frozen python -m tracker.profile_release prepare-promotion \
  --bundle /absolute/private/review/reviewed-profiles.json \
  --output /absolute/private/review/profiles.patch

uv run --frozen python -m tracker.profile_release check-promotion \
  --bundle /absolute/private/review/reviewed-profiles.json \
  --patch /absolute/private/review/profiles.patch \
  --candidate-id EXACT_PREPARATION_ID
```

Preparation reads the repository's fixed two-file public base and produces only
their paired Git patch. Existing files must be valid as a pair; both absent is
the initial case. The candidate identity binds the reviewed bundle, exact base
bytes or absence, and exact patch bytes. Only public projection/manifest text
crosses into the patch. The public outputs use canonical UTF-8 JSON with one
final newline, without private checkpoint/approval envelopes. The repository's
two exact profile JSON paths use `-text` Git attributes so Windows checkout or
patch application cannot silently convert that required LF to CRLF.

Clocks cannot rewind. A same-check-clock replacement must preserve the entire
snapshot. For a retained record, first observation remains unchanged; unchanged
content keeps its changed-observation clock, and changed content needs an
observation after the public last successful confirmation. A replacement ID
also needs its first observation after that confirmation; newer fetch clocks
cannot conceal a conflicting earlier branch. A failed/quarantined candidate must preserve the public last-good
record and successful-fetch clock exactly. A single checkpoint cannot prove
intermediate source success before a later failure; that unsupported gap is
refused rather than inferred from checkpoint ancestry.

The `check-promotion` operation regenerates everything and compares the exact
patch and candidate identity without writes. Run it immediately before separately
authorized application with unchanged inputs. Then `git apply --check` must
pass before `git apply` in the reviewed branch. Recheck if any input changes.
These commands never apply, deploy, schedule, enable indexing or add ads.

Build validation requires the public pair together, strict normalized scope and
exact rights bindings. Both files must be ordinary nonsymlink files in an
ordinary data directory, encoded as canonical compact sorted UTF-8 JSON with
an optional single final newline. Duplicate fields, pretty formatting and
invalid encoding are refused. Release readiness also requires a matching reviewed
bundle and verified recovery copy under a separate private parent; see
[RELEASE_READINESS.md](RELEASE_READINESS.md). Schema/build success does not
establish current source freshness, external recovery or hosting readiness.

CLI exit 0 means the named offline operation completed. Exit 2 is a static
refusal/interruption report. Reports exclude paths, source text and credentials;
approval is true only after successful explicit approval creation. An interrupted
post-install approval may exist despite a refused report; verify before retry.

Overview and When to Visit consume the verified public profiles. Subsequent data
refreshes repeat exact review, approved-bundle
recovery and paired promotion without renewing source clocks during copying.
