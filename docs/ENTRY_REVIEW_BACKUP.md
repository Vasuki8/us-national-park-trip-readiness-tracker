# Private entry-review backup and restore

## Purpose

`tracker.entry_review_backup` creates, verifies and restores owner-only backups of the private entry-review SQLite ledger.

It is a storage/recovery utility only. It performs no NPS request, source capture, reviewer decision, reconciliation, public-data write, deployment or publication.

## Storage requirements

Use private POSIX storage outside the repository. The backup-root parent and restore-destination parent must already exist and be owner-only. Symlink ancestry, protected repository paths and insecure parent permissions are refused.

This mechanism is tested for local POSIX filesystems. It does not certify native Windows filesystems, network filesystems, cloud-sync folders or removable media.

## Create a backup

```sh
uv run --frozen python -m tracker.entry_review_backup backup \
  --store /absolute/private/entry-review \
  --backup-root /absolute/private/entry-review-backups
```

The operation:

1. fully reads/replays the source ledger;
2. refuses an empty/uninitialized ledger;
3. uses SQLite's backup API to create a transactionally consistent temporary database snapshot;
4. fully replays that copied database and requires the logical state to equal the verified source snapshot;
5. computes the copied database byte length and SHA-256;
6. creates a metadata manifest; and
7. atomically installs the bundle under its content-addressed backup ID.

The source SQLite file is not modified.

## Bundle format

A completed bundle contains exactly:

```text
BACKUP_ROOT/
  BACKUP_ID/
    review.sqlite3
    manifest.json
```

Directories are owner-only (`0700`) and files are owner-only (`0600`).

The manifest contains:

- schema/purpose;
- ledger revision;
- event count;
- guidance-record count;
- pending-proposal count;
- database filename;
- exact database byte length;
- database SHA-256;
- `network_performed:false`;
- `approval_performed:false`; and
- `publication_performed:false`.

`backup_id` is the SHA-256 digest of the canonical manifest core excluding the ID itself.

There is no capture text or private filesystem path in the manifest. The SQLite database necessarily contains the full private editorial evidence and must be protected accordingly.

## Idempotency

Running backup again against the same logical ledger produces the same content-addressed bundle in the tested environment. If that destination already exists, it must verify exactly before reuse.

A mismatched/corrupt existing bundle is refused rather than overwritten.

No automatic pruning, rotation or deletion is implemented.

## Verify a backup

```sh
uv run --frozen python -m tracker.entry_review_backup verify \
  --backup /absolute/private/entry-review-backups/BACKUP_ID
```

Verification is read-only. It checks:

- owner-only directory/files;
- exact two-file bundle inventory;
- manifest schema and backup ID;
- database size and SHA-256;
- SQLite database format;
- complete database integrity/replay through the existing ledger model; and
- manifest ledger revision/counts against the replayed state.

Renaming the bundle away from its content-addressed `BACKUP_ID` directory is refused.

## Restore a backup

```sh
uv run --frozen python -m tracker.entry_review_backup restore \
  --backup /absolute/private/entry-review-backups/BACKUP_ID \
  --destination /absolute/private/restored-entry-review
```

Restore only accepts a destination that does **not** already exist.

The operation verifies the backup, copies the database into a temporary owner-only directory under the destination parent, fully replays that copied ledger, checks the manifest head/counts again, then atomically renames the temporary directory into place.

A restore never overwrites an existing ledger or directory. Interrupted restore attempts leave no completed destination.

The restored directory contains only `review.sqlite3`; the backup manifest remains in the backup bundle.

## Interruption behavior

Both backup and restore build in temporary directories and use an atomic same-directory rename for final installation.

Tests simulate interruption at the rename point:

- an interrupted backup leaves no completed content-addressed bundle;
- an interrupted restore leaves no destination ledger; and
- retry remains possible.

These tests establish process-interruption behavior on the CI POSIX filesystem. They do not certify hardware power-loss behavior on a particular storage device.

## What is not backed up

The backup is for the authoritative private editorial ledger only.

Reviewer HTML packets are derived inspection artifacts and are not included. They can be regenerated from ledger evidence for sources that still satisfy packet requirements.

Public website files, alert-history archives and application source code are separate systems and are not included by this command.

## Operational backup policy still required

This feature provides the mechanism, not the actual redundancy policy.

Before a real NPS editorial session, the owner should choose where the second verified copy will live and how it will be protected. A useful minimum is:

1. working ledger on owner-controlled private POSIX/WSL storage;
2. create a backup after a meaningful capture/reconciliation checkpoint;
3. run `verify` on that bundle;
4. copy the verified bundle to a second owner-controlled storage location;
5. verify the copied bundle there before relying on it.

The project does not currently automate that second copy, encryption, retention/rotation, cloud storage or removable-media handling.

Do not use GitHub repositories, Actions artifacts or public/synced folders as the private editorial backup.

## Threat-model boundary

Hashes detect accidental corruption and bind internal consistency. They are not signatures and do not defend against an actor who can rewrite both database and manifest and recompute hashes.

Not established: encryption at rest, authenticated reviewer identity, hostile same-user mutation, hardware-specific power-loss durability, network filesystems, native Windows behavior, multi-host coordination, automated off-host replication or indefinite retention.
