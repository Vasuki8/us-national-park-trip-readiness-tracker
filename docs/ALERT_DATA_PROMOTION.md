# Prepare alert data for operator review

The offline preparer turns an existing private preview bundle into a Git patch for the five public alert snapshots and their matching `data/history.json`. It performs no network request, approval, public-data write, backup or deployment. Preparing the patch is ordinary development; applying real source data remains a deliberate operator action.

Complete the owner-controlled capture, backup and review prerequisites in [the durable collection runbook](DURABLE_COLLECTION_SESSION.md). Use [the existing preview workflow](PREVIEW_BUNDLES.md) to freeze verified archive observations and inspect the candidate page. Keep the bundle and patch outside the checkout and all public outputs, on private Linux/macOS/WSL storage. On Windows, use the WSL Linux filesystem rather than a Windows drive for these private files.

## Preparation

From the repository root, using Node.js 24:

```sh
node --experimental-strip-types scripts/prepare-alert-promotion.ts \
  --bundle /absolute/private/preview-bundles/BUNDLE_ID.json \
  --output /absolute/private/review/alert-data.patch
```

Both paths must be absolute and normalized, outside the checkout, with no symlink ancestry. Their immediate parent directories must already exist, belong to the current user and have owner-only permissions (`0700`). The input must be a regular owner-only file (`0600`) with one hard link. The output is installed atomically with `0600` permissions. An identical retry preserves its bytes and timestamp; a conflicting file is refused without replacement. If a filesystem failure occurs after installation, inspect the retained patch before retrying. There is no automatic cleanup of earlier candidates.

The command prints only candidate/bundle hashes, changed-file and collection-status counts, and explicit review/publication flags. It never prints notice text, supplied private paths or underlying exceptions. Exit `0` means preparation succeeded, including an identical retry; exit `2` means refusal. The patch is bounded to 32 MiB, and bundle/public input files use the existing 10 MiB bound.

The strict existing loader checks the bundle identity, exact pilot inventory and paired snapshot/history contracts. Synthetic bundles are refused. The `unreviewed_source` label describes input kind; it does not authenticate a source or prove human review. A same-sequence candidate must match the public checkpoint exactly. A newer candidate must retain the complete previous public head observation and every overlapping public observation, with cumulative change counts advancing by the new observations' exact counts. After a successful public baseline, the preparer replays complete new changes over its record hashes and observation clocks and requires the resulting records to match the candidate. Missing removals, changed retained clocks, omitted new changes, reset baselines, rewinds, forks and unverifiable gaps are refused.

The bounded history normally retains 20 observations and at most 100 changes per observation. The successful-fetch clock advances only to a new successful observation's check time; otherwise it must retain the public clock, including null. New successes are checked oldest first: a null public success clock requires the first success to be a baseline with no changes, followed by comparisons; an existing public success requires comparisons. This remains required when earlier attempts or the last success are omitted from the visible histories. If an older public head has fallen outside that window, or new changes are omitted, use the explicit archive-backed check below. Without that check, these gaps remain refused. Do not reset the public history or edit bundle hashes to bypass refusal. Public input must be valid UTF-8; retry comparison uses exact bytes rather than lossy text decoding.

## Archive-backed continuity for omitted history

Supply the actual committed archive used to create the frozen bundle:

```sh
uv run --frozen node --experimental-strip-types scripts/prepare-alert-promotion.ts \
  --bundle /absolute/private/preview-bundles/BUNDLE_ID.json \
  --output /absolute/private/review/alert-data.patch \
  --archive-dir /absolute/private/alert-staging/archive
```

The frozen uv environment supplies Python 3.12+ for the read-only verifier. The archive must already exist outside the checkout, with no symlink ancestry. Its root and every contained directory/file must belong to the current user, have owner-only permissions, and contain no hard-linked regular files. Use the operator runbook's separate `umask 077` session for collection. The bundle and output must be separate from the archive, including its ancestors and descendants. Verification does not initialize, repair, chmod, recover or remove any archive state.

`tracker.alert_promotion_archive` reuses `HistoryStore.read()` to replay each complete committed park chain. It projects the precise public checkpoint and frozen candidate from those verified chains, compares both snapshot/history hashes, and reconstructs the exact five-park bundle identity. Missing, damaged, forked or changed checkpoints refuse before output installation. Archive observations newer than the frozen candidate are allowed: the candidate must remain an exact retained prefix, and can never rewind the public checkpoint. No global capture time or freshness claim is created.

Only a small hash/count request and bound metadata reply cross the subprocess boundary. Provider keys, arbitrary Python options and caller-supplied module paths are not inherited. The bridge has a 16 KiB request/reply bound and a 60-second process timeout. Existing archive limits remain 4,096 observations per park, 256 MiB/65,536 entries overall and 64 MiB reconstructed snapshot bytes per park. Refusal emits generic diagnostics; raw archive contents and private paths are not printed.

Successful archive verification permits gaps in the visitor projection because the underlying complete changes and clocks have been replayed. The patch still contains only the bounded public snapshots/history, with all omission counts preserved. It never exports raw responses, archive objects or a full private chain. The patch header identifies archive versus bounded-preview continuity; the report adds `archive_continuity_verified` and `verified_archive_parks`. These fields prove consistency with the supplied archive, not source authenticity, human approval, current conditions, rights clearance, storage durability or release readiness.

Never-checked, failed, quarantined and stale evidence stays unchanged in meaning. Failed/quarantined candidates retain their original successful-fetch times. No new review, source-update, publication or global collection timestamp is invented. Preparing a degraded candidate does not make it eligible for release. An unchanged dataset produces no empty patch.

## Deliberate review and application

Before applying real data, the owner must review the exact private patch and matching preview, source-content/rights scope, archive backup and remaining trust gates. No preparation flag or hash substitutes for that review. Raw captures, ledger events, packets, archive files, pending receipts and credentials must never be included in the public change.

Retain the `candidate_id` printed during preparation alongside the operator's review record. Immediately before a separately authorized application, check that exact candidate against the current checkout:

```sh
uv run --frozen node --experimental-strip-types scripts/prepare-alert-promotion.ts \
  --check \
  --bundle /absolute/private/preview-bundles/BUNDLE_ID.json \
  --patch /absolute/private/review/alert-data.patch \
  --candidate-id RECORDED_CANDIDATE_ID
```

Replace `RECORDED_CANDIDATE_ID` with the original 64-character lowercase SHA-256 value, rather than computing a new hash from a changed patch. If preparation used `--archive-dir`, append that same option and actual private archive path to the check. The verifier replays the archive again; the patch header alone is not archive proof. The frozen bundle must still be available.

This mode rebuilds the exact candidate using the same path, bundle, public-pair and continuity checks as preparation, then compares its bytes and recorded candidate ID with the existing private patch. Its regenerated header binds all six current public base files, including parks whose files are unchanged by the patch. A formatting-only base edit, changed bundle, different continuity mode, edited patch or wrong candidate ID refuses. Inputs retain the same private path/permission requirements, and the patch must be a single-link owner-only regular file bounded to 32 MiB. Missing patches, symlinks, named pipes and oversized inputs refuse without creation or repair.

Exit `0` reports `mode: alert_promotion_check`, `public_base_files_checked: 6`, `patch_bytes_matched: true` and the existing candidate counts/hashes. `human_review_required` remains true, with public-data/publication flags false. Exit `2` produces only a generic refusal. The check creates no file or directory and preserves input bytes and modification times. It is a point-in-time consistency check, not a record of approval or permission to apply. Keep the checkout and private inputs unchanged between checking and authorized application; an already applied candidate will refuse against the new public base.

The patch header also exposes the source bundle and SHA-256 of all six public base files for manual inspection:

```sh
sha256sum data/alerts/{yose,romo,yell,zion,grca}.json data/history.json
git apply --check /absolute/private/review/alert-data.patch
```

If any base hash differs or the read-only check refuses, prepare and review a new candidate. Patch hunks carry the complete old contents of changed files, including their original line endings. A Git check alone does not inspect unchanged base files or establish human approval. Do not use whitespace-ignore, three-way or reject/partial-application options to force an outdated candidate through.

Only after explicit operator authorization, apply the reviewed patch:

```sh
git apply /absolute/private/review/alert-data.patch
git diff -- data/alerts data/history.json
npm run validate:data
npm test
npm run check
npm run build
npm run test:site
npm run build:pages
npm run test:site:pages
```

Run the Python and both browser suites as documented in `README.md` before integration. Review the resulting public pages, especially removals and retained failures. Commit only the reviewed public JSON change through the normal code-review process; keep the private patch outside Git and CI artifacts. The command does not alter entry guidance or source-rights manifests.

Read [release readiness](RELEASE_READINESS.md) again with the current reviewed ledger and verified backup. Real public-data application, integration, hosting/rollback verification, indexing and ads remain separate decisions. This preparer does not clear any of those gates.
