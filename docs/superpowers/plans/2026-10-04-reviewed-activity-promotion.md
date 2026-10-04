# Reviewed activity promotion implementation plan

> **For agentic workers:** Use test-first implementation with independent tasks and a complete branch review before integration. Track verified results in the current handoff.

**Goal:** Make exact activity text review, private approval/recovery and paired public-data patch preparation possible without collecting or publishing real data during development.

**Architecture:** Extend the existing profile promotion pattern with a separate activity contract. Preserve complete normalized inventories; reuse only public neutral storage, encoding and clock APIs. Python, TypeScript, private release commands and release readiness share the contract below.

**Tech stack:** Existing Python 3.12+, frozen uv, Node 24, TypeScript and Astro. No new dependencies or infrastructure.

**Spec:** The agreed in-chat design, owner policy and source contracts in [ACTIVITY_FOUNDATION.md](../../ACTIVITY_FOUNDATION.md) and [ACTIVITY_COLLECTION.md](../../ACTIVITY_COLLECTION.md). This plan fixes the activity-specific interfaces and decisions.

## Global constraints

- Synthetic sources and truthful test metadata only; no real collection, approval, backup upload, public-data application or deployment.
- Complete five inventories in pilot order; each has a successful-fetch clock, including confirmed empty inventories. Retained failed/quarantined state and original clocks survive projection.
- Public dataset: `schema_version: 1`, `purpose: public_park_activities`, `inventories`.
- Exact separate rights manifest: `schema_version`, `purpose: public_park_activity_text_rights`, `reviewed_at`, `review_method: official_nps_policy_and_exact_activity_review`, existing exact NPS `policy`, and `records`.
- Rights records bind `park_code`, `activity_id`, fixed unkeyed API `source_url`, `content_hash`, `classification: nps_government_text`, `use_scope: normalized_activity_text_and_metadata`, and false `third_party_material_reproduced`, `nps_marks_reproduced`, `media_reproduced`.
- One rights row per retained record, ordered by pilot then sorted record ID. IDs may repeat across parks. Review covers every public string, including descriptions, relation labels and credit; metadata never proves rights. Review follows all attempted checks; no invented licence expiry.
- Projection/rights limits are each `42_008_576` canonical bytes. Public files allow one additional final LF. Private approved-bundle limit is checkpoint + projection + rights limits + 64 KiB; patch limit is twice the two public-file limits + 64 KiB. Never trim evidence or widen legacy defaults.
- Fixed outputs: `data/park-activities.json`, `data/activity-source-rights.json`, both `-text`. Both absent is optional; incomplete/noncanonical/invalid pairs fail build/readiness.
- Native Windows Git owns repository mutations. WSL tests use Node 24 and normal `umask 022`; private synthetic fixtures use existing owner-only Linux directories outside checkout.
- Owner delegates ordinary technical decisions and authorizes merging reviewed PRs after required checks. Continue without redundant technical/design/merge permission requests.

## Review focus

- A cross-park repeated ID needs two exact rights rows, while duplicate/omitted rows are refused.
- Large valid batches must encode, read, hash, restore and prepare replacement patches beyond legacy 8/10 MiB limits.
- An input named like the destination lock cannot be overwritten/unlinked; approval protects checkpoint and rights inputs.
- A valid private fork cannot erase public observation history or bypass the severe-drop guard.
- Recovery metadata extends existing readiness gates only downward and does not establish actual off-host transfer or deployment.

## Task 1: Python public contract and bounded paired-file reads

Files: create `tracker/activity_public.py`, `tests/test_activity_public.py`.

Interfaces: `ActivityPublicError`, `MAX_PUBLIC_BYTES`, `MAX_RIGHTS_BYTES`, `PUBLIC_FILES`, `POLICY`; `canonical_activity_json(value, *, max_bytes=MAX_PUBLIC_BYTES) -> bytes`, `activity_digest(value, *, max_bytes=MAX_PUBLIC_BYTES) -> str`, `parse_activity_json(raw, *, max_bytes) -> object`, `validate_public_activities(value) -> dict`, `project_checkpoint(value) -> dict`, `validate_activity_rights(value, dataset) -> dict`.

`read_public_activity_pair(root: Path) -> dict` returns `current` (the two fixed path-to-bytes-or-None entries), `dataset` and `rights` (both None if absent). It validates bounds, ordinary nonsymlink files/data directory, strict UTF-8/JSON, exact canonical bytes with optional single LF, and the complete pair. Private POSIX guards are not applied to public files.

- [x] Write tests for projection privacy/copies, preserved null/empty/false states, never-successful refusal, confirmed empty inventories, per-record rights ordering/bindings/clocks and tampering.
- [x] Run focused unittest discovery and confirm missing-contract failures.
- [x] Implement the exact public model using existing activity/checkpoint validators and explicit bounds; add secure bounded paired-file reads.
- [x] Verify large canonical objects, exact/one-byte-over limits, strict parsing, incomplete pairs, symlinks/nonregular inputs, Unicode and canonical file bytes.

## Task 2: TypeScript parity and build gate

Files: create `scripts/validate-park-activities.ts`, `tests/park-activities.test.ts`; modify `scripts/validate-data.ts`, `.gitattributes` only for the two activity outputs.

Interfaces: export `MAX_ACTIVITY_BYTES`, `MAX_ACTIVITY_RIGHTS_BYTES`, `canonicalActivityJson`, `activityDigest`, `validatePublicActivities`, `validateActivityRights`, `validateActivityFiles(root: string)`. The last function takes the public data directory, matching `validateData(root)` without inferring its parent/name, and returns the validated dataset or null. Python-generated synthetic fixtures are the parity oracle; use Unicode scalar ordering, Python whitespace and microsecond instants.

- [x] Write/run RED Node tests before implementation.
- [x] Implement strict complete activity/rights validation with the same unknown fields, semantic hashes, bounds, URLs and original clocks as Python.
- [x] Reuse or extract only neutral canonical helpers when justified; preserve profile behavior and avoid profile-private helpers.
- [x] Add optional paired-file build validation and byte-preserving Git attributes. Test absent/incomplete/invalid/canonical/duplicate-key/file-type cases and Python parity beyond 10 MiB.
- [x] Run focused Node tests and affected profile/build-gate tests.

## Task 3: Private reviewed bundle and paired promotion

Files: create `tracker/activity_release.py`, `tests/test_activity_release.py`.

Consume Task 1 exports and public `activity_checkpoints`/`private_checkpoint_io`/`entry_review_io` helpers; do not import profile private helpers. Export `ActivityReleaseError`, `MAX_BUNDLE_BYTES`, `MAX_PATCH_BYTES`, `build_release_bundle`, `validate_release_bundle`, `create_release_bundle`, `verify_release_bundle`, `restore_release_bundle`, `build_promotion`, `prepare_promotion`, `check_promotion` with profile-equivalent signatures.

Bundle fields: `schema_version: 1`, `purpose: private_reviewed_park_activities`, `checkpoint`, `public_activities`, `rights`, `approval`, `bundle_id`. Approval binds decision `approved`, `approved_at`, checkpoint ID, complete projection hash and rights hash; time follows review. Bundle digest binds the complete core.

- [x] Write/run RED tests for exact review bindings, explicit approval flag, tampered bundles, large batches and safe private no-overwrite writes.
- [x] Implement bounded immutable approval, verify and fresh restore. Encode/refuse before lock; protect destination and lock against both inputs, preserve completed outputs after post-install errors.
- [x] Implement pure paired patch preparation and identity binding to bundle/base bytes/patch bytes. Current pair must be valid/canonical; refuse clock rewind, equal-attempt changes and altered degraded last-good evidence.
- [x] For retained IDs preserve first observation and unchanged-content change clocks. Changed/new IDs require observations after public success. Reapply populated-inventory half-drop guard against public state. Parent IDs are references, not replay proof.
- [x] Implement CLI `approve --approve`, `verify`, `restore`, `prepare-promotion`, `check-promotion`, fixed safe errors and metadata-only reports; no key/network/public writes. Test real synthetic Git patch application, fresh recheck, tampering, newline base changes, source/input collisions and interruptions.

## Task 4: Read-only release readiness

Files: modify `tracker/release_readiness.py`; create `tests/test_activity_readiness.py`.

Consume Task 1 paired-file reader and Task 3 bundle validators. Add `activity_review`/`activity_backup` optional kwargs to `evaluate_readiness`; CLI adds `--activity-review`/`--activity-backup` and requires separate canonical private parents for the two supplied copies.

- [x] Write/run RED tests for optional absence, incomplete/invalid public pair, missing/mismatched review/recovery, and safe CLI evidence paths.
- [x] Extend existing `durable_source_review`, `storage_backup`, `source_rights` gates only downward with exact activity evidence. Preserve older profile/alert semantics and gate order. Invalid supplied private evidence is a static refusal.
- [x] Verify large bundles with explicit limits; matching local recovered copies prove integrity only, not remote transfer. No source clock or existing blocker is renewed/cleared.

## Task 5: Documentation, review and integration

- [x] Document exact operator commands, rights scope, bounds, interruption/recovery, paired patch/CAS and readiness in `docs/ACTIVITY_PROMOTION.md`; update README, development, foundation/collection next steps and release-readiness docs.
- [ ] Review code and contract independently, fix reproduced findings, run complete Python/Node/Astro/root/project-build/site checks and required CI browser suites.
- [ ] Review staged diff/private boundaries; create/attach PR, merge checked head after all required checks/review pass, verify identical trees and update current handoff with actual receipts.
- [x] Leave real collection, rights decisions, verified remote backup, public promotion, Things to Do rendering and live release as explicit subsequent work.
