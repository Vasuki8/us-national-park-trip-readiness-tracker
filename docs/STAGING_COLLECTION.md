# Private staging collection

This command connects the existing collector to the existing evidence archive. It does not modify `data/`, `public/`, `src/` or `dist/`; it does not build, deploy, schedule or publish. A successful private archive write is not successful collection, public redistribution approval or proof of complete park conditions.

## Commands

Use Python 3.12+ and the project's frozen uv environment. Choose owner-controlled local storage. Under this repository, `state/` is already ignored by Git.

```sh
uv run --frozen python -m tracker.stage status --park yose --staging-dir state/staging
uv run --frozen python -m tracker.stage collect --live --park yose --staging-dir state/staging
uv run --frozen python -m tracker.stage recover --park yose --staging-dir state/staging
```

`collect` alone is not enough: `--live` and a valid private `NPS_API_KEY` environment variable are both required. Do not put keys in command arguments, URLs, code, issues or chat. Status and recovery are offline and need no key. Codes: `yose`, `romo`, `yell`, `zion`, `grca`. Each invocation handles one park; run sequentially. There is no new GitHub Actions collection workflow or schedule.

These are operating instructions, not evidence that real NPS transport/schema compatibility was tested. The separate read-only preflight remains the live compatibility gate. No live requests were made while implementing or testing this increment.

## Transaction and recovery

1. Acquire the staging writer lock, validate the existing archive and reject an unresolved receipt or non-advancing clock before fetching.
2. Use the actual existing NPS collector. It retains last-good records on provider failure or suspicious feed loss. The stricter archive validator additionally quarantines rejected normalized records (for example, a credential-like URL fragment) without storing the rejected candidate text.
3. Write a bounded, integrity-checked receipt containing the validated candidate and the archive parent against which it was collected. No API headers or raw responses are retained.
4. Append with the expected-parent guard inside the archive writer lock. Another offline importer advancing the archive during collection cannot silently change that baseline.
5. Remove the receipt only after verified archival. Only an archive head commit establishes accepted history; a pending receipt is not a public snapshot.

Receipt layout: `pending/{park}.json`. Archive layout: `archive/`, using the existing history store. Do not point this staging root at an existing standalone archive; this increment does not migrate storage. Repeated unchanged notices generate collection observations without invented semantic changes.

A recoverable receipt permits offline retry using exactly the original candidate and check timestamp. A candidate already committed before interruption is acknowledged without duplication, including when it is now an ancestor of a newer accepted observation. An uncommitted receipt whose expected parent no longer matches is a conflict: retain it for operator review, never rewrite history or overwrite newer data.

A crash during network access or before the receipt becomes durable does not leave a recoverable completed response. The prior archive remains authoritative; a later collection is a new attempt with a new check timestamp. Raw in-flight responses are not reconstructable. Source update, human review, effective-date and publication clocks are never advanced here. `last_checked_at` follows the existing collector's attempt-clock convention, not a newly invented source update time.

## Operator status and exit codes

Status has `stage_state` of `idle`, `pending`, `committed_needs_cleanup` or `conflict`; it separately reports staging/archive writer locks, accepted collection status, last checked/successful times and pending candidate status/time. Reports contain counts, hashes and fixed operational labels, not provider notice text or raw exception messages. An idle state does not mean fresh data or a safe trip. Status is an observation of local files, not a publication gate or a cross-process transaction snapshot.

Exit `0`: status, no receipt to recover, or successful source candidate archived/recovered. Exit `1`: a failed/quarantined collection attempt was successfully archived/recovered. Exit `2`: configuration, local state, conflict, storage, or unexpected execution failure; inspect private state before retrying. Machine output always keeps `publication_performed` and `site_data_written` false. It never says an unsuccessful source check succeeded just because it was archived.

## Locks, bounds and storage assumptions

Staging and archive locks are never stolen or removed automatically. After abnormal termination, first confirm the writer process has stopped and inspect `status` and the archive. Back up the directory before manual recovery. Only then may an operator remove the abandoned `.stage.lock` and, when present, `archive/.writer.lock`, and run offline `recover`. Do not remove locks merely because a file is old; no automatic lock-repair command is provided.

Pending state is limited to 32 regular files and 60 MiB, with 10 MiB per receipt/object. A write reserves space for both temporary and final names before creation. Orphan temporary files are bounded and ignored as uncommitted state, not automatically pruned. The existing archive's disk, history-count and reconstruction limits still apply. A full/damaged archive leaves a durable receipt pending rather than promoting candidate data to the website.

Roots inside source/site/Git directories, traversal paths, symlinks and non-regular pending files are refused. This is trusted local-filesystem tooling, not protection against a hostile process with the same filesystem permissions. Hashes detect accidental corruption, not an attacker rewriting both content and hashes. Existing directory permissions and off-host backup remain the operator's responsibility.

Python documents `os.replace` atomic renaming and `os.fsync`; same-directory writes and the existing archive primitive are used here: https://docs.python.org/3.12/library/os.html#os.replace and https://docs.python.org/3.12/library/os.html#os.fsync . Process-interruption tests are not hardware power-loss, Windows durability or network-filesystem guarantees.

## Remaining release gates

No public-history projection, actual live source fixture, automatic source-change review, scheduled persistent store, deployment or rollback was enabled. GitHub Actions ephemeral checkouts do not establish ongoing archive persistence. Resolve operator-controlled storage and validate live compatibility before scheduling. Public-history projection, source-content review and deployment gates remain separate.
