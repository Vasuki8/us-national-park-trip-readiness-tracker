# Reviewed minimal activity catalog design

October 4, 2026. Implements the current handoff's technical next step under the
owner's schema/implementation autonomy. No real source decision, approval,
backup transfer, public-data application or deployment is authorized by this spec.

## Purpose and choice

Visitors need useful individual activity discovery without reproducing unresolved
quotations, embedded link metadata or unsupported availability claims. Retain
private source evidence unchanged and add a versioned, fixed minimal projection.
Whole-record exclusion under v1 still publishes unnecessary prose in other records;
HTML stripping does not settle text-use rights and would break existing hashes.
A fixed catalog is smaller and easier to review than a general text rewriting engine.
Visitor rendering and real review/promotion remain subsequent operator work.

## Exact schema and interfaces

Use existing public pair paths and purpose names with schema_version 2. Version 1
projection, rights and approved-bundle verification retain their exact meaning.
No new packages, credentials, network calls, schedules, indexing or ads.

New tracker/activity_catalog.py exports validate_dispositions(value, checkpoint),
project_catalog(checkpoint, dispositions), validate_catalog(value), and
validate_catalog_rights(rights, dataset). All return detached validated dictionaries
and raise the existing ActivityPublicError with fixed codes. Reuse canonical
UTF-8, scalar ordering, clocks and explicit limits from activity_public; avoid
module cycles through lazy version dispatch in the existing validator.

Private dispositions have exactly schema_version:1,
purpose:private_activity_catalog_dispositions, checkpoint_id, reviewed_at and
records. Each ordered row has exactly park_code, activity_id, source_content_hash,
decision:selected|withheld and categories:published|withheld. Require one row per
retained source record in pilot/ID order, including all withheld records. Withheld
rows require categories:withheld. Review follows checkpoint.checked_at. No default
selection or guessed decision. No rewritten source fields or free-form reasons.

Public outer object retains exactly schema_version:2,
purpose:public_park_activities and inventories in pilot order. Each inventory has
all v1 inventory fields with schema_version:2, plus source_records. Copy source
header states/clocks unchanged; require a successful baseline even when degraded.
source_records retains exactly id, content_hash, hash_scope:normalized_record,
observed_first_at, observed_changed_at and publication_status:selected|withheld
for every original source record in ID order. These hashes bind original private
semantics; they cannot be recomputed from the public subset. Source summaries
contain no source descriptions, credit, URLs or withholding reason text.

records contains selected listings only, with exactly id, park_code, title, url,
activity_categories, category_scope:published|withheld,
geographic_relationship:unconfirmed, responsible_agency:null, difficulty:null,
permit_required:null, availability_status:not_verified, source_updated_at:null,
observed_first_at, observed_changed_at, source_content_hash, view_hash and
hash_scope:catalog_view. category_scope:withheld requires activity_categories:null;
published retains the original null, empty list or complete categories unchanged.
Selected title and URL are mandatory exact source values. A selected record's
source hash/clocks must match its selected source summary. Withheld summaries
have no public record; no extra or missing selected records are accepted.
view_hash hashes exactly all public record fields except view_hash and hash_scope.
Never publish omitted source text, flags, related-park names, media or HTML.

Catalog text is bounded nonempty plain text: title/category names at most 1,024
Unicode scalars, no control characters U+0000..001F/007F..009F, '<' or '>'. IDs use
existing identifier bounds/controls. Categories retain existing sorted unique
IDs, maximum 1,000. URL must pass existing official NPS path validation scoped to
the queried park or global /thingstodo/, and must contain neither '?' nor '#'.
This is conservative refusal, not URL rewriting. A source link outside this
catalog scope requires whole-record withholding. Maximum records 5,000 and
source summary observation clocks follow v1 semantics. Keep existing per-record,
per-inventory and public canonical limits. No new geographic/permit inference.

Rights v2 retains v1 top-level fields plus projection_hash (canonical full
catalog digest). Require schema_version:2 and the existing exact policy/method.
One ordered row per selected public record, with exactly park_code, activity_id,
source_url, source_content_hash, view_hash, classification:nps_government_text,
use_scope:activity_catalog_title_url_and_optional_categories,
third_party_material_reproduced:false, nps_marks_reproduced:false,
media_reproduced:false. These assertions apply only to the published catalog
strings; no assertion covers withheld private prose. Review time follows every
attempted park check, including empty or wholly withheld feeds. Full projection
hash binds withheld source summaries and all catalog metadata as well.

## Approval, promotion and readiness

Extend build_release_bundle(checkpoint, rights, approved_at, *, dispositions=None)
and create_release_bundle(..., approve=False, dispositions=None). A supplied
validated private disposition plan selects v2, otherwise unchanged v1. CLI approve
accepts optional --dispositions PATH; no implicit approval or selection.

Private v2 bundle keeps v1 purpose/fields plus dispositions; schema_version:2.
Approval keeps v1 fields plus dispositions_hash. Regenerate projection from exact
checkpoint/dispositions, compare complete canonical public/rights bytes, verify
bundle ID, and require disposition review <= rights review <= approval. Protect
all input files from overlap with output/lock. Reuse unchanged private installer,
verify/restore and paired patch commands/limits. No public writer is introduced.

For v1-to-v1 promotion preserve existing strict behavior. When either side is v2,
compare source evidence independently of editorial selection: same attempted
instant requires identical source headers and source summaries excluding
publication_status; degraded candidates retain source hashes/observations and
successful clock. Original first/changed observation checks and the half-drop
guard apply to all source summaries, not published count. Editorial selection or
category review may change at the same source clock with a newly reviewed exact
bundle. Neither withholding nor category selection is an NPS removal or refresh.
Transitions between versions require explicit compatible bundles, never silent
reinterpretation of v1 approvals.

Python/TypeScript public validators dispatch by version at existing build gates.
Readiness accepts exact v2 reviewed/recovered evidence through the same gates;
report source total, published and withheld counts separately, and rights covered
count for published records. Equality proves local integrity, not remote origin,
source authenticity or human review. Gates only become stricter, never relaxed.

## Verification and continuity

Use synthetic fixtures and private temporary directories only. Test absence of
quotation/contact/tracking markers in every public patch byte, exact per-record
selection/withholding, null/empty/withheld distinctions, missing/duplicate/stale
plans, view/source/rights tampering after outer rehash, clock boundaries and
Unicode parity, degraded retention and source-removal/drop guards, review changes
without renewed source clocks, v1 compatibility, private path/input protection,
fresh restore, paired CAS recheck and readiness binding. Run full Node/Python,
Astro, both builds/site checks and supported CI browser suites before merge.
Update operator guides and current handoff with actual evidence and next task.
