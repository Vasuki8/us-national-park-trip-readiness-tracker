# Owner-selected private GitHub backup

The owner selected GitHub for the separate backup on September 30, 2026. Use a dedicated **private** repository separate from the public website repository. Record the exact selected repository identity privately. This replaces the earlier blanket restriction against GitHub backups for this owner-selected destination. Public repositories, Pages outputs and Actions artifacts remain unsuitable for private evidence.

For each authorized operator session, use the selected private destination and
exact verified evidence inventory. Extending the supported inventory below does
not itself establish upload approval, source-rights approval, public-data
application or deployment. New destinations, access changes and paid Git LFS
retain their owner-decision boundaries.

Keep the authoritative working ledger, alert archive, profile/activity checkpoints and local verified backups on the WSL Linux filesystem outside the website checkout. GitHub is the remote second copy. A local clone on C: or D: is a transfer/recovery workspace, not a separate physical backup. GitHub access controls protect this private repository; this procedure does not claim client-side encryption or indefinite retention.

## Repository and local setup

Before uploading evidence, confirm through authenticated GitHub repository metadata that the exact selected repository is private, owned by the expected owner and writable by that owner. Keep Actions disabled and do not enable Pages or add collaborators. Check privacy again before each upload and recovery. If visibility or identity is wrong or cannot be checked, stop.

Use owner-only WSL directories with no symlink ancestry for the working root, transfer clone and recovery parent. The existing `tracker.entry_review_backup` verifier still enforces private local files and parents. Clone and copy under `umask 077`; set `core.autocrlf=false` and use `* -text` in the backup repository's `.gitattributes` so database and manifest bytes are preserved. Git does not preserve POSIX privacy permissions remotely: enforce and verify them again on materialized WSL files.

The repository may contain only its setup files, explicitly selected verified entry-review bundles, committed alert-archive snapshots, immutable park-profile checkpoints or reviewed bundles, immutable activity checkpoints or separately reviewed activity approval bundles, and clearly labeled synthetic transport probes. Never copy an entire home/configuration/staging directory. Keep API keys, credentials, live working databases, writer locks, pending receipts, packet output, website builds and source checkout files excluded. Retained ledger evidence is private source material and belongs only in this private repository.

## Upload a verified entry-review checkpoint

1. Stop ledger writers and use the existing backup command to create a transactionally consistent, content-addressed bundle. Verify it before copying, as described in [ENTRY_REVIEW_BACKUP.md](ENTRY_REVIEW_BACKUP.md).
2. Copy exactly the resulting `BACKUP_ID` directory containing `manifest.json` and `review.sqlite3` into `entry-review/BACKUP_ID` in the private transfer clone. Refuse an existing destination unless it already verifies identically. Verify the copied bundle with the same command.
3. Inspect the exact staged inventory. Stage only that two-file bundle; do not use a whole-working-directory add. Refuse symlinks, unexpected files and any file larger than 50 MiB before upload. This conservative pilot limit stays below GitHub's ordinary Git object limit; do not silently enable paid Git LFS or truncate a backup when it is exceeded.
4. Commit with a metadata-only message and push normally to the private repository. Preserve earlier checkpoints; do not force-push, prune or delete backups as part of this procedure. Record the remote commit and backup ID privately.
5. Perform the fresh-download recovery checks below. An acknowledged push alone does not establish recovery or clear the backup gate.

## Download, verify and rehearse recovery

From an existing owner-only recovery parent, make a fresh authenticated clone directly from the GitHub URL under `umask 077`. Do not clone from the transfer workspace, copy its `.git` directory, use alternates/shared objects or substitute a local cache. Use the exact recorded remote commit and refuse any missing or changed bundle.

Run the unchanged verifier on `entry-review/BACKUP_ID` in that fresh clone:

```sh
uv run --frozen python -m tracker.entry_review_backup verify \
  --backup /absolute/private/recovery-clone/entry-review/BACKUP_ID
```

Compare its backup ID, ledger revision, event counts and database byte identity with the local verified checkpoint. Restore that downloaded bundle into a **new** owner-only destination using the existing restore command; replay the restored ledger and compare the same revision/counts. Never replace the working ledger during a rehearsal. Repeat upload/download verification after reconciliation advances the head; a valid earlier backup is then historical.

Use the downloaded and verified current-head bundle for the existing release-readiness check. The verifier proves ledger integrity; the separately retained GitHub commit/download/restore receipts establish the selected remote-copy procedure. Neither invents human source approval.

## Alert archives are separate

The entry-review backup contains no alert archive. After collection has stopped, use `HistoryStore.read()` to verify each complete committed park chain, copy only its committed archive state into a new checkpoint under `alert-archives/`, and verify the copied and freshly downloaded chains again against the original heads/counts. Exclude staging pending receipts and writer locks. Apply the same private repository, byte-preservation, inventory and size checks. Do not count a ledger-only upload as an alert-archive backup.

## Park-profile checkpoints and reviewed bundles

Profiles have a separate source and review contract; entry-review and alert
backups do not cover them. Before approval, a selected immutable checkpoint may
be retained under `profiles/checkpoints/CHECKPOINT_ID.json`. Use the unchanged
`tracker.profile_stage verify` command before copying and after a fresh download,
then `restore` into a new private destination. Compare checkpoint ID and exact
canonical bytes. This protects collected evidence only: it does not approve text
reuse, clear a profile publication gate or authorize public-data application.

After exact text-use approval, select the verified immutable bundle described in
[PROFILE_PROMOTION.md](PROFILE_PROMOTION.md) under
`profiles/reviewed/BUNDLE_ID.json`. It contains the checkpoint and complete
projection, rights and approval bindings. Use `tracker.profile_release verify`
before copying and after the fresh download, then `restore` into a new private
destination. Compare bundle ID and exact canonical bytes. A checkpoint-only copy
cannot substitute for recovery of that reviewed bundle.

Apply the same authenticated repository identity/privacy checks, owner-only
storage, byte-preserving Git configuration, exact staging, per-file size limit
and preservation of historical evidence to both types. The selected inventory
is the one verified JSON file and any explicitly reviewed setup documentation;
exclude review HTML, proposals, operator receipts, raw responses, credentials,
locks and temporary files. Recheck privacy before recovery and clone directly
from the selected GitHub URL. Record remote commit, selected type/ID, byte
comparisons and restore result privately. Approval remains a separate decision.

## Activity checkpoints and reviewed approval bundles

Activities have their own [collection](ACTIVITY_COLLECTION.md) and
[reviewed promotion](ACTIVITY_PROMOTION.md) contracts. Ledger, alert and profile
backups do not cover activity evidence or approval. Before approval, select the
verified immutable checkpoint under
`activities/checkpoints/CHECKPOINT_ID.json`. Use the unchanged
`tracker.activity_stage verify --checkpoint PATH` before copying, on the copied
file and after a fresh authenticated remote download. Use
`tracker.activity_stage restore --checkpoint PATH --output NEW_PATH` to restore
the downloaded file into a new owner-only private destination. Compare checkpoint
ID and exact canonical bytes with the local verified checkpoint. Checkpoint-only
backup proves recovery of unapproved collected evidence; it does not establish
text-use rights approval, recovery of a reviewed approval bundle or public
readiness.

After exact text-use review and explicit approval under the promotion contract,
select the verified immutable approval bundle under
`activities/reviewed/BUNDLE_ID.json`. It retains the checkpoint, complete public
projection, rights manifest and approval bindings. Use the unchanged
`tracker.activity_release verify --bundle PATH` before copying, on the copied
file and after the fresh authenticated remote download. Use
`tracker.activity_release restore --bundle PATH --output NEW_PATH` to restore
the downloaded bundle into a new owner-only private destination. Compare bundle
ID and exact canonical bytes with the local verified bundle. Verify the restored
file and compare identity and canonical bytes again for either type. Copying and
restoration preserve original source clocks; backup never supplies a rights
decision or authorizes public-data application.

Apply the same authenticated repository identity, expected-owner, write-access
and privacy checks before each upload and recovery. Keep Actions disabled, Pages
unconfigured and access unchanged. Use existing owner-only WSL Linux parents
outside the checkout with no symlink ancestry, `umask 077`, `core.autocrlf=false`
and `* -text`; enforce file privacy again after download. Stage only the selected
verified JSON at its exact inventory path, inspect the staged bytes and refuse
symlinks, unexpected files or any file larger than 50 MiB. A valid approved
bundle can exceed this unchanged transport limit: refuse its upload without
splitting or trimming evidence, changing destinations or enabling paid Git LFS.
Exclude credentials, raw HTTP responses, review HTML, proposals, operator
receipts, writer locks and temporary files. Preserve earlier activity, profile,
alert and ledger checkpoints; do not force-push, prune or delete history.

Clone directly from the same selected GitHub URL into a fresh owner-only
recovery workspace at the recorded remote commit, following the remote-download
requirements above. A transfer clone, shared objects, local cache or acknowledged
push cannot substitute for this recovery check. Record selected type/ID, remote
commit, download, byte comparisons and fresh restore result privately. Neither
checkpoint-only recovery nor an approved-bundle recovery clears the remaining
source, freshness, review, public-data or deployment gates by itself.

## Setup evidence versus real backup evidence

A labeled synthetic push/download/restore probe may verify credentials, Git transport, byte preservation and the existing restore path. It does not establish a backup of real evidence, physical durability, human review or release readiness. Keep any probe separate under `probes/`. Before public guidance and alert application or deployment, verify their actual current-head ledger and alert-archive backups, fresh downloads and applicable owner review. Profile and activity evidence follow the separate checkpoint/reviewed-bundle scopes above; a private collection-only session does not change the ledger or public data.

## Record recovery privately

Retain the exact private repository identity, remote commit, selected checkpoint IDs, byte/count comparisons, restore/replay outcomes and recovery paths outside the website checkout. Check that the working ledger remains unchanged during the rehearsal. Exclude these detailed real-session receipts from public documentation and PR descriptions.

Use the verified downloaded current-head backup for the local readiness report and keep that operator report privately. A backup becomes historical when reconciliation advances the ledger; repeat this procedure for that new head. Recovery does not approve source context or authorize public-data application or deployment.

Reference: [GitHub repository visibility](https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories) and [ordinary Git repository limits](https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits).
