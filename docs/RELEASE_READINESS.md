# Pilot release-readiness report

## Purpose

`tracker.release_readiness` is a conservative, read-only summary of the five-park pilot's remaining launch gates.

It does not decide that the product should launch. It reports what the repository and explicitly supplied private evidence can actually prove.

Missing evidence is never a pass.

The default target is an **ad-free, unindexed pilot**, matching the approved pilot scope. Search indexing and advertising are separate later targets. A disabled later feature does not block an otherwise reviewed pilot; detected ad integration or changed pilot indexing controls still requires review.

## Commands

Repository-only human-readable report:

```sh
uv run --frozen python -m tracker.release_readiness --format text
```

Repository-only JSON report:

```sh
uv run --frozen python -m tracker.release_readiness --format json
```

Later-target reports:

```sh
uv run --frozen python -m tracker.release_readiness --target indexed --format text
uv run --frozen python -m tracker.release_readiness --target advertising --format json
```

`--target` accepts only `pilot` (default), `indexed`, or `advertising`.

After an owner-controlled private ledger and verified backup exist:

```sh
uv run --frozen python -m tracker.release_readiness \
  --format text \
  --store /absolute/private/entry-review \
  --backup /absolute/private/backups/BACKUP_ID
```

`--backup` is refused unless `--store` is also supplied. The backup is replay-verified by the existing backup module before its manifest can affect the report.

When reviewed profiles have deliberately been promoted, supply their separate
private reviewed bundle and verified recovered copy:

```sh
uv run --frozen python -m tracker.release_readiness \
  --format json \
  --store /absolute/private/entry-review \
  --backup /absolute/private/backups/BACKUP_ID \
  --profile-review /absolute/private/profile-review/reviewed.json \
  --profile-backup /absolute/private/downloaded-profile-backup/reviewed.json
```

`--profile-backup` requires `--profile-review`. Both inputs use the existing
owner-only POSIX file boundary outside the checkout. Their canonical paths
and immediate parent directories must differ; the working review file cannot
serve as its own backup. Both complete bundles are independently verified
before comparison. These options perform no collection, approval, restore,
transfer or public-data write.

When reviewed activities have deliberately been promoted, also supply their
separate reviewed bundle and verified recovered copy:

```sh
uv run --frozen python -m tracker.release_readiness \
  --format json \
  --activity-review /absolute/private/activity-review/reviewed.json \
  --activity-backup /absolute/private/downloaded-activity-backup/reviewed.json
```

Combine these options with the ledger/profile inputs above for complete current
evidence. `--activity-backup` requires `--activity-review`; their canonical paths
and immediate private parent directories must differ. Both complete bundles are
independently verified with the explicit activity bounds before comparison.
These read-only options perform no approval, recovery or transfer. A matching
local recovered copy proves integrity, not off-host backup. See
[ACTIVITY_PROMOTION.md](ACTIVITY_PROMOTION.md).

The current owner-approved version 2 pair contains **136 original source
summaries, 129 published listings and seven withheld listings**, with rights
coverage for 129 views. Its separately retained approved-bundle remote recovery
has been verified. Repository-only reports still cannot infer that private
evidence; supply the exact working review and fresh recovered bundle alongside
the current ledger/profile evidence. Activity validity and backup do not prove
availability, clear other release gates or authorize deployment.

The CLI prints no supplied private path.

Exit codes:

- `0`: every required gate for the selected target is `pass`;
- `1`: a normal report was produced but at least one required gate is `blocked` or `not_checked`;
- `2`: arguments/evidence could not be safely evaluated.

## Gate statuses

Every gate has one of exactly three statuses:

- `pass` — the evidence required by this evaluator is present;
- `blocked` — available evidence explicitly shows the gate is not ready;
- `not_checked` — the needed evidence is absent or requires external validation.

Both `blocked` and `not_checked` block `release_ready` when the gate is required. All seven gates remain visible, including gates belonging to a later target.

## Release targets and report schema

| Gate | Pilot | Indexed pilot | Advertising |
|---|---|---|---|
| Durable source review | Required | Required | Required |
| NPS alert data | Required | Required | Required |
| Private backup | Required | Required | Required |
| Source rights | Required | Required | Required |
| Hosting and rollback | Required | Required | Required |
| Search indexing | Later, while all pilot controls remain intact | Required | Required |
| Advertising | Later, while no integration is detected | Required if integration is detected | Required |

For a pilot report, removal of **any** of the three repository indexing controls makes indexing review required, even if another control remains. This prevents selecting `pilot` to bypass a partially changed publication configuration. Detected ad integration makes advertising review required for either `pilot` or `indexed`.

An intact pilot exemption requires recognizable active controls: one literal robots meta tag in an unconditional HTML head, the canonical `User-agent: *` / `Disallow: /` group without exceptions, and an unqualified noindex header under global `/*` rules. Comments, conditional/component markup, named-agent-only rules, allow exceptions, narrowed header paths and scoped/removal headers are not proof. Unknown configurations require review; this is a conservative recognizer of the pilot configuration, not a complete Astro, robots or hosting-policy interpreter.

Parser references: [Robots Exclusion Protocol, RFC 9309](https://www.rfc-editor.org/rfc/rfc9309.html) and [Cloudflare Pages header configuration](https://developers.cloudflare.com/pages/configuration/headers/). Recognizing `_headers` does not establish that GitHub Pages serves those headers.

JSON is now **schema version 2**. The purpose remains `pilot_release_readiness`. It adds:

- `release_target`: the selected target;
- `required` and `required_reason` on every gate;
- `required_summary`: status counts for required gates only.

The existing `summary` still counts all seven gates. `blocking` now means **required and not passed** for this target. Consumers of schema version 1 must account for that changed meaning before accepting version 2. Gate status, evidence and reason remain visible even when a later gate is not required. The text output labels those gates explicitly and shows both summaries.

The optional profile inventory extends evidence within the existing durable
review, backup and source-rights gates; it adds no gate and retains schema 2.
With neither `data/park-profiles.json` nor `data/profile-source-rights.json`,
the report is unchanged, including when unrelated valid private profile
evidence is supplied. Either public file activates the profile requirements.
Missing paired files, malformed JSON, invalid five-park inventories or invalid
rights bindings block all three gates, even if the older guidance evidence
passes. Duplicate JSON keys, nonfinite constants and inputs above 8 MiB are
refused. Public profile inputs must be regular files under a nonsymlink
immediate parent and use canonical UTF-8 JSON with at most one final newline;
file symlinks and special files are refused before reading. No profile
validation result establishes provider compatibility,
freshness or release authorization.

The optional activity pair extends those same three gates only downward, with
no new gate or schema change. Both `data/park-activities.json` and
`data/activity-source-rights.json` absent preserves the existing report. Either
file activates activity requirements; an incomplete or invalid pair blocks all
three gates. Complete five-park inventories require a successful-fetch baseline,
including confirmed empty inventories; retained failed/quarantined attempts keep
their original clocks and records. Public files must be regular under ordinary
nonsymlink ancestry, use strict canonical UTF-8 JSON with at most one final LF,
and fit each explicit 42,008,576-byte canonical bound plus that optional LF.
Duplicate keys, nonfinite values, unknown fields and incorrect rights bindings
are refused. No validity result establishes activity availability or freshness.

Both the complete version 1 projection and minimal version 2 catalog use this
same evidence boundary. Version 2 approval additionally binds exact private
selected/withheld dispositions and regenerates the smaller public views from the
unchanged checkpoint. Activity evidence separately reports original source
total, published and withheld record counts; rights coverage counts published
listings only. Wholly withheld source inventories remain distinct from confirmed
empty sources. A matching checkpoint-only backup cannot cover a reviewed catalog
bundle, and catalog validity does not establish text rights or reviewer identity.

`release_ready` remains an evidence result for the named target, not deployment authorization. Target selection changes the report only; it does not change the site or activate features.

## Gates

### Durable source review

Without a private ledger: `not_checked`.

With a verified private ledger, this gate passes only when:

- all five fixed source URLs have exactly one schema-v2 context baseline created by explicit reconciliation;
- the current proposal register is empty;
- each baseline's guidance hashes exactly cover its current private records, including both Rocky Mountain records; and
- the complete current public `rules.json` / `entry-notes.json` inventory matches that reviewed private inventory by stable ID and full-record hash.

Legacy schema-v1 baselines do not satisfy this release gate.

Each current v2 baseline must match a baseline created for that source by a reconciliation event in the verified ledger. The event must select that source's active proposals from the preceding register, and its baseline must match the current context, hashes and timestamps in full. Imported v2 baselines carried through another source's reconciliation do not establish approval provenance. Later matching observations preserve an unchanged baseline's provenance. Missing provenance returns `context_approval_provenance_incomplete`.

A reviewed private revision cannot approve an older or independently edited public record. Summary, exceptions, effective dates, evidence, review timestamps and rights fields are all part of record identity. Record ordering and JSON object-key ordering are immaterial; missing, extra, duplicate or empty inventories fail closed. This compares guidance only and does not export private evidence or modify public data.

Schema 2 adds count/boolean evidence to this gate: `public_guidance_records`, `private_guidance_records`, `public_guidance_matches_ledger`, `reviewed_guidance_matches_baselines` and `reconciled_v2_sources`. The existing `approved_v2_sources` counts sources with v2 baseline metadata; `reconciled_v2_sources` counts current baselines with source-specific event provenance. A `null` means that comparison was not reached, for example because the ledger was not supplied, still has holds, lacks complete reviewed baselines, or failed an earlier inventory/binding check. No record contents, private paths, record IDs or hashes are emitted.

The Python `evaluate_readiness` API expects an already replay-verified private state and verified backup manifest; a caller-provided dictionary is not itself proof of an approval. The CLI obtains those inputs through `EntryReviewStore.read()` and `verify_backup()`.

This establishes approval provenance within the ledger; it does not authenticate the operator's identity or independently verify the truth of their review metadata.

For an active valid profile inventory, durable review additionally requires a
verified `private_reviewed_park_profiles` bundle whose complete public profile
projection and separate rights manifest exactly match the public files.
The bundle binds the immutable checkpoint, complete projection, rights and
explicit approval by canonical hashes. Collection states and source clocks
are part of the comparison; a semantic content hash alone cannot approve a
different check time, failed attempt or rights review. Existing guidance
baselines do not approve profiles.

Absent profile review is `not_checked`; a supplied review that differs from
the public files is `blocked`. Existing unresolved guidance requirements
continue to block this shared gate. Profile evidence consists only of
inventory presence/validity/counts and `public_profiles_match_review`;
the report emits no profile text, private paths or bundle/checkpoint hashes.
The Python API validates supplied profile dictionaries again; a dictionary
is not proof of authenticated human approval.

Active activities similarly require a verified `private_reviewed_park_activities`
bundle matching the complete public inventories and separate rights manifest.
The bundle binds checkpoint, full projection, rights and explicit approval;
attempted/successful/observation clocks are included. Missing activity review is
`not_checked`; a supplied mismatched review is `blocked`. Evidence includes
`activity_inventory_present`, `activity_inventory_valid`,
`activity_records_total` and `public_activities_match_review`, without text,
private paths or bundle hashes. Earlier guidance/profile reviews do not approve
activity text, and existing unresolved requirements remain blocking.

### NPS alert API

The read-only keyed provider integration has now been validated for all five pilot parks. Run **36628434444** returned `gate_passed:true` with successful normalization for Yosemite, Rocky Mountain, Yellowstone, Zion and Grand Canyon.

That diagnostic deliberately performs no public writes. The owner subsequently approved promoting five durably retained/reviewed public alert baselines, containing 17 notices. The report now reads five successful snapshots in `data/alerts/`.

Any `never_checked` snapshot blocks the public alert-data gate. An empty record list is never interpreted as “no alerts.”

For successful snapshots the automated gate remains `not_checked`, with reason `success_present_but_freshness_and_provider_compatibility_need_release_validation`. The launch's current freshness and read-only provider check were assessed separately in private operator receipts. The CLI does not ingest those external checks or automatically promote them into a pass. A successful preflight alone cannot self-promote unpublished data into a release pass.

### Private storage backup

Without a supplied private ledger: `not_checked`.

With a ledger but no verified backup: `blocked`.

A verified backup passes only when its manifest matches the exact current ledger revision and event count. A valid but older backup is blocked as stale for release purposes.

For active public profiles, the gate additionally requires a separately
verified recovered profile bundle matching the current reviewed bundle in
full, including its bundle ID and canonical bytes. An absent, older or
different profile backup blocks this gate even when the current ledger backup
passes. `profile_backup_verified` reports supplied bundle integrity;
`profile_backup_matches_review` reports exact current public-review coverage.
Neither field proves an off-host copy or remote recovery. Retain the separate
private-repository upload, fresh-download and restore receipts under
[GITHUB_PRIVATE_BACKUP.md](GITHUB_PRIVATE_BACKUP.md). Earlier ledger and alert
backup receipts do not cover profiles.

Active activities additionally require a separately verified recovered activity
bundle matching the current reviewed bundle ID and full canonical bytes.
Missing or different recovery blocks this gate; `activity_backup_verified` and
`activity_backup_matches_review` distinguish integrity from current coverage.
These fields do not prove off-host transfer or fresh authenticated download.
Earlier ledger, alert and profile recovery receipts do not cover activities;
retain the separate remote identity, upload, download and fresh-restore receipts.

### Source-rights review

The report requires both the record-level `rights_basis` / `rights_reviewed_at` fields and the exact-scope `data/source-rights.json` manifest.

The gate passes only when:

- the public guidance inventory is nonempty, has unique valid IDs and binds each record to its park's fixed official entry source, covering all five pilot sources;
- all six current public guidance records have rights metadata;
- the manifest exactly matches all six guidance IDs and official source URLs;
- every use remains `nps_government_text` limited to a short text excerpt plus original summary;
- no third-party material, NPS marks, or media are claimed as reproduced;
- the required commercial U.S. Government-work notice is present in the public footer; and
- no public media asset or NPS-hosted/mark media use is detected in the current application.

The manifest is grounded in the official NPS disclaimer and Arrowhead-use guidance. This pass applies only to the current six public text uses. It is not blanket clearance for NPS media, marks, third-party material, private raw captures, or future content.

Active public profiles also require the separate
`data/profile-source-rights.json` manifest. It must cover each of the five
profiles exactly, binding park code, profile ID, scoped API source URL and
normalized content hash. Its allowed use is
`normalized_profile_text_and_category_names`, with a separate official-policy
and exact-profile review clock and method. Third-party material, NPS marks,
media and private raw captures remain excluded. The rights review covers only
the normalized introduction, identity, seasonal context and category names;
categories are not individual activities and seasonal context is not a
forecast. A guidance rights manifest cannot provide this new coverage.

Successful profile validation contributes `profile_records_covered` to the
existing rights gate and retains its commercial-notice and media safeguards.
It does not turn an API response or a review-export flag into rights clearance.

Active activities require `data/activity-source-rights.json`, ordered by pilot
park and record ID and binding park code, activity ID and the fixed unkeyed API
source. Version 1 covers every retained listing's normalized content hash with
`normalized_activity_text_and_metadata`, including every projected description,
relation label and credit. Version 2 covers only selected listings with
`activity_catalog_title_url_and_optional_categories`, binding original source
and public-view hashes plus the complete projection digest. Both require false
third-party/marks/media reproduction flags. A credit or API response alone
cannot establish rights. The review clock follows every attempted inventory
check, including confirmed empty or wholly withheld inventories. Validation adds
`activity_records_covered` while preserving all existing notice/media safeguards.
This is exact reviewed scope, not blanket NPS clearance or an invented licence
expiry. Full details are in [ACTIVITY_PROMOTION.md](ACTIVITY_PROMOTION.md).

Inventory validation precedes manifest coverage. Empty inventories, duplicate/conflicting IDs, invalid park/source bindings or a missing pilot source return `public_guidance_inventory_invalid`, even if the rights manifest was reduced or edited to match. A matching manifest cannot establish that its inputs are a valid pilot inventory. Record and manifest ordering remain immaterial; report schema and evidence fields are unchanged.

The commercial notice must be recognizable literal text in one unconditional `<footer>` directly under the layout's HTML body. The source check excludes frontmatter, comments, attributes, scripts, styles, templates and other non-notice contexts. Explicit hiding, inline styles, dynamic/replacement attributes on notice ancestors, Astro conditionals, components and malformed/duplicate footers cannot establish this evidence. Ordinary inline formatting, HTML entities and whitespace are accepted. A missing or unrecognized notice blocks every release target with `commercial_government_work_notice_missing`; report schema and evidence fields are unchanged.

This is a conservative recognizer of the current static layout, not an Astro evaluator, CSS visibility audit or proof of a deployed footer. Stylesheet changes, runtime behavior and hosted output still require build/browser and operator review. An unfamiliar layout requires explicit review rather than a substring-based pass.

Complex Astro expressions anywhere in the layout require review because JavaScript comments, strings or JSX can contain HTML-like text that a plain HTML parser would otherwise mistake for document structure. Complete property lookups such as the current `{title}` remain accepted outside the footer. Markup-containing or truncated attribute expressions, default-hidden popovers and duplicate document elements also cannot supply notice evidence.

### Hosting and rollback

A manual GitHub Pages deployment/rollback workflow is now present, so this gate is `not_checked` rather than `blocked`.

The workflow can only reuse a successful default-branch `Verify pilot` artifact whose run ID and exact commit SHA are explicitly supplied. The owner-authorized launch has now verified deployment, older-version rollback, restoration and actual browser behavior at the live project URL. Reports and their exact artifact identities are retained privately; public run links are in `docs/PAGES_RELEASE.md`.

CI verifies root and GitHub project-path builds. The manual release workflow selects the existing verified output whose manifest `base_path` matches the configured Pages path and whose `code_commit` matches the requested commit. Missing or mismatched outputs fail before upload. The evaluator deliberately remains `not_checked` for hosting because it does not accept external deployment/browser receipts. The separate operator assessment records the verified evidence without modifying this conservative CLI behavior.

The evaluator never deploys.

### Search indexing

The evaluator checks three repository controls:

- the page `meta robots` directive;
- `public/robots.txt`; and
- the `X-Robots-Tag` directive in `public/_headers`.

If any still disables indexing, the gate's status is `blocked` for an indexed release. This gate is not required for a default pilot with all three controls intact.

If all are removed, the gate becomes `not_checked` because actual crawlability/indexability requires separate external validation. The evaluator does not ingest that review. A partial or complete removal requires review in a pilot report as well. Repository markers do not prove effective production response headers or domain-root robots behavior; GitHub project hosting is discussed in `docs/PAGES_RELEASE.md`. The evaluator never changes these controls.

### Advertising readiness

If no known advertising integration markers are present in `src/` or `public/`, the gate is `blocked` for the advertising target, but not required for the ad-free pilot or indexed pilot.

If ad integration is later present, the gate becomes `not_checked` because policy/consent/readiness review must be separately established. The evaluator does not ingest that review. It is required regardless of the selected target. Choosing `pilot` cannot bypass detected ad integration.

The evaluator never enables ads or analytics.

## Current repository result

After the owner-approved public-data promotion, a repository-only report (without private ledger/backup inputs) has:

- **1 pass**
- **3 blocked**
- **3 not checked**
- **release_ready: false**

Those are counts across all seven gates. With the public profile and activity pairs,
the default pilot's repository-only required summary is **1 pass, 1 blocked,
3 not checked**. No private evidence is implied by committed public JSON.

Two blocked statuses belong to later targets:

1. indexing is still disabled; and
2. advertising is not enabled.

Disabled indexing and ads remain visible as later-target gates, consistent with the approved ad-free pilot. They are still required for their respective later releases.

The required backup gate is also blocked because a repository-only command
does not supply the matching recovered ledger, reviewed-profile and
reviewed-activity bundles. The three
not-checked gates are:

1. durable source review, because a repository-only command does not receive the private ledger;
2. NPS alert API validation, because successful public snapshots still require separately assessed freshness/provider evidence; and
3. hosting/rollback, because the CLI does not ingest the verified external release/browser reports.

The current source-rights gate is the one passing gate, limited to the exact six
guidance uses in `data/source-rights.json`, the five normalized profile text
uses in `data/profile-source-rights.json` and the 129 exact title/link/category
views in `data/activity-source-rights.json`. These manifests cover no images or marks.

Supplying the current reviewed private ledger and matching recovered backup,
along with matching reviewed profile/activity bundles and their separately verified
recovered copies, changes durable review and backup to `pass`: **3 pass, 2 blocked,
2 not checked** overall, with **3 pass, 0 blocked, 2 not checked** required for the
pilot. The earlier owner-authorized launch separately verified its external
requirements; that historical assessment is not new source freshness or hosting
evidence. The automated report still returns `release_ready: false`. Retain each
current external assessment alongside the report instead of inventing a pass.

## Safety properties

The report:

- performs no network access;
- writes no files;
- does not mutate the private ledger or backup;
- does not deploy;
- does not change indexing;
- does not enable ads;
- does not call source capture or reconciliation;
- does not turn absent evidence into success; and
- does not claim that an empty alert list is an all-clear.

It is a release evidence dashboard, not a release action.
