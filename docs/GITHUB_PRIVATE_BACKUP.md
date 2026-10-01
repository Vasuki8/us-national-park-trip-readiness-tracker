# Owner-selected private GitHub backup

The owner selected GitHub for the separate backup on September 30, 2026. Use a dedicated **private** repository, `Vasuki8/parkreadiness-private-backups`, separate from the public website repository. This replaces the earlier blanket restriction against GitHub backups for this owner-selected destination. Public repositories, Pages outputs and Actions artifacts remain unsuitable for private evidence.

Keep the authoritative working ledger, alert archive and local verified backups on the WSL Linux filesystem outside the website checkout. GitHub is the remote second copy. A local clone on C: or D: is a transfer/recovery workspace, not a separate physical backup. GitHub access controls protect this private repository; this procedure does not claim client-side encryption or indefinite retention.

## Repository and local setup

Before uploading evidence, confirm through authenticated GitHub repository metadata that the exact repository is private, owned by Vasuki8 and writable by the owner. Keep Actions disabled and do not enable Pages or add collaborators. Check privacy again before each upload and recovery. If visibility or identity is wrong or cannot be checked, stop.

Use owner-only WSL directories with no symlink ancestry for the working root, transfer clone and recovery parent. The existing `tracker.entry_review_backup` verifier still enforces private local files and parents. Clone and copy under `umask 077`; set `core.autocrlf=false` and use `* -text` in the backup repository's `.gitattributes` so database and manifest bytes are preserved. Git does not preserve POSIX privacy permissions remotely: enforce and verify them again on materialized WSL files.

The repository may contain only its setup files, explicitly selected verified entry-review bundles, committed alert-archive snapshots and clearly labeled synthetic transport probes. Never copy an entire home/configuration/staging directory. Keep API keys, credentials, live working databases, writer locks, pending receipts, packet output, website builds and source checkout files excluded. Retained ledger evidence is private source material and belongs only in this private repository.

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

## Setup evidence versus real backup evidence

A labeled synthetic push/download/restore probe may verify credentials, Git transport, byte preservation and the existing restore path. It does not establish a backup of real evidence, physical durability, human review or release readiness. Keep any probe separate under `probes/`. Every real session requires actual current-head ledger and alert-archive uploads, fresh-download verification and the owner's review before public-data application or deployment.

## First real recovery receipt

On September 30, 2026 (Toronto time), the owner explicitly approved the real upload. Private commit `5b112b8590d69d85853210044b71a7e5885c5c7c` contains the selected two-file ledger backup and separate 27-file alert archive with its manifest. A fresh authenticated remote clone verified the current ledger checkpoint, exact database bytes and a restore into a new private directory with full-state equality. All five downloaded alert chains replayed and matched the original checkpoints, retaining 17 notices. Credentials and reviewer packets were excluded. The original working ledger did not change.

The current-head backup gate now passes. Six source-review proposals remain pending, public alert data is unchanged and no deployment has occurred. The backup becomes historical when reconciliation advances the ledger; repeat this procedure for that new head. Exact checkpoint IDs and the current handoff are in `PROJECT_STATUS.md`; detailed recovery receipts remain outside the website checkout.

Reference: [GitHub repository visibility](https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories) and [ordinary Git repository limits](https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits).
