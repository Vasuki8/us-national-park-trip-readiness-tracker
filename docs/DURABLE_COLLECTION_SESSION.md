# Durable private collection session

Use this sequence for the first real five-park capture and review session. Run from the repository root with Python 3.12+, Node 24 and the project's frozen uv environment. The individual command contracts remain in [persistent capture](PERSISTENT_ENTRY_CAPTURE.md), [backup/restore](ENTRY_REVIEW_BACKUP.md), [reviewer packets](REVIEWER_PACKET.md), [reconciliation](GUIDANCE_RECONCILIATION.md) and [alert staging](STAGING_COLLECTION.md).

## 1. Choose the working and backup storage

The owner must choose durable private Linux/macOS/WSL storage outside the repository and a separate owner-controlled backup destination. Both roots below must already exist, be owner-only (`0700`) and have no symlink ancestry. Keep the second root on storage separate from the working ledger. An ephemeral development workspace, repository, Actions artifact or public/synced folder does not meet this prerequisite.

Replace these example absolute paths before running any command:

```sh
umask 077
trip_private=/absolute/durable/private
trip_second=/absolute/separate/private-backup
```

The commands create child directories as needed. This runbook does not create, mount or certify the storage roots. Stop if either destination is unavailable or its durability is unknown.

## 2. Check setup, then capture the five entry pages

For a new ledger:

```sh
uv run --frozen python -m tracker.entry_review_live \
  --check-only --store "$trip_private/entry-review" \
  --packet-output-dir "$trip_private/review-packets" \
  --expected-revision empty
```

Exit `0` means the offline setup check passed. It makes no requests or writes. Then explicitly capture:

```sh
uv run --frozen python -m tracker.entry_review_live \
  --live --store "$trip_private/entry-review" \
  --packet-output-dir "$trip_private/review-packets" \
  --expected-revision empty
uv run --frozen python -m tracker.entry_review_cli status \
  --store "$trip_private/entry-review"
```

Keep the returned `source_event_revision`, current `revision` and each source's `packet_id` available privately for review. Entry-page capture needs no API key.

For an existing ledger, read `status` first and replace `empty` in both capture commands with its exact current `revision`. Never reset or delete an existing ledger to make this first-run example work.

Live exit `0` means the observation committed and required packets are ready. Exit `1` means it committed with incomplete captures or packets. Exit `2` requires reading `status` before deciding whether to retry; an unusual post-commit failure can occur without a normal report. Inspect incomplete evidence before proceeding to approval. A failed capture is not an empty successful source.

## 3. Back up before human review

```sh
uv run --frozen python -m tracker.entry_review_backup backup \
  --store "$trip_private/entry-review" \
  --backup-root "$trip_private/entry-review-backups"
```

Replace the placeholder with the returned `backup_id`, then verify:

```sh
trip_backup_id=RETURNED_BACKUP_ID
uv run --frozen python -m tracker.entry_review_backup verify \
  --backup "$trip_private/entry-review-backups/$trip_backup_id"
```

Copy that entire verified bundle to the separate root, retaining its ID directory name and owner-only permissions. This copy refuses an existing destination:

```sh
uv run --frozen python - \
  "$trip_private/entry-review-backups/$trip_backup_id" \
  "$trip_second/$trip_backup_id" <<'PY'
import shutil
import sys
shutil.copytree(sys.argv[1], sys.argv[2])
PY
uv run --frozen python -m tracker.entry_review_backup verify \
  --backup "$trip_second/$trip_backup_id"
```

If the destination already exists, verify it rather than overwrite it. An interrupted or unverifiable copy is not a usable backup. Compare both verification reports: backup ID, ledger revision and event count must match the capture checkpoint. The owner remains responsible for storage separation, protection and retention.

A recovery rehearsal can restore the verified second copy to a new destination:

```sh
uv run --frozen python -m tracker.entry_review_backup restore \
  --backup "$trip_second/$trip_backup_id" \
  --destination "$trip_private/restored-entry-review"
uv run --frozen python -m tracker.entry_review_cli status \
  --store "$trip_private/restored-entry-review"
```

The destination must not exist. Compare its revision and counts with the original; restoration does not replace the working ledger or approve evidence.

## 4. Human review and reconciliation

A human must open each ready packet at `review-packets/PACKET_ID/index.html` on the private machine and inspect the complete retained context. The five park codes are `yose`, `romo`, `yell`, `zion` and `grca`. A ready packet or matching excerpt does not approve guidance.

Use current `status` for active proposal IDs. Prepare an owner-only reconciliation JSON outside the repository according to [the reconciliation contract](GUIDANCE_RECONCILIATION.md): the latest retained source observation, all active proposals for each affected source, the complete resulting private record inventory, a reviewer label, rationale and the actual review time. Preserve unaffected records and rights metadata exactly. Do not invent a human review or reuse an example timestamp.

After that review, replace the revision placeholder with the current `status` revision:

```sh
trip_head=CURRENT_LEDGER_REVISION
uv run --frozen python -m tracker.entry_review_cli reconcile \
  --store "$trip_private/entry-review" \
  --input "$trip_private/guidance-reconciliation.json" \
  --expected-revision "$trip_head"
```

Inspect status after each reconciliation. Repeat the backup, verification and second-copy steps for the resulting head before relying on the reviewed checkpoint. A pre-review backup becomes historical once the ledger advances. Private reconciliation does not update public guidance.

## 5. Collect alerts privately

Provide `NPS_API_KEY` privately in the local environment using the owner's secret-management method. Keep it out of chat, arguments, URLs, repository files and frontend variables. The cloud development environment does not inherit the Actions secret.

```sh
uv run --frozen python -m tracker.preflight
```

Inspect a successful preflight before collecting:

```sh
uv run --frozen python -m tracker.stage collect --live --park all \
  --staging-dir "$trip_private/alert-staging"
uv run --frozen python -m tracker.stage status --park all \
  --staging-dir "$trip_private/alert-staging"
```

Batch exit `1` retains failed/quarantined attempts; exit `2` can follow partial committed progress. Read all-park status before any retry. Pending receipts can be recovered offline one park at a time:

```sh
uv run --frozen python -m tracker.stage recover --park yose \
  --staging-dir "$trip_private/alert-staging"
```

Choose the affected park; do not remove or steal writer locks. Follow the staging contract for a conflict or abandoned writer. Successful archival is not public review or an exhaustive all-clear. The entry-ledger backup does **not** include alert archives; keep and verify a separate owner-controlled archive backup under the owner's backup policy before relying on that evidence.

## 6. Read the remaining release gates

Use the latest verified backup for the current ledger head:

```sh
uv run --frozen python -m tracker.release_readiness --format json \
  --store "$trip_private/entry-review" \
  --backup "$trip_second/$trip_backup_id"
```

Exit `1` means release gates remain blocked, not that the report failed. Public guidance must separately match the reviewed private inventory; public alerts must separately be reviewed and published; hosting/rollback evidence is still required. The existing preview bundle can feed the offline [alert-data patch preparation and operator review path](ALERT_DATA_PROMOTION.md). Preparation writes no public data. This session does not publish data, deploy the website or activate indexing or ads.

## Development rehearsal

On September 30, 2026, this sequence was rehearsed with disposable synthetic source captures: five packets, six unresolved holds, backup and second-copy verification, and an exactly matching restored ledger. Offline all-park status created no staging files. Public data remained unchanged and readiness stayed blocked. No real network request, human approval or durable-storage proof was produced by that rehearsal.
