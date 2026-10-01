# Private staging collection

This command connects the existing collector to the existing evidence archive. It does not modify `data/`, `public/`, `src/`, `dist/` or `dist-pages/`; it does not build, deploy, schedule or publish. A successful private archive write is not successful collection, public redistribution approval or proof of complete park conditions.

## Commands

Use Python 3.12+ and the project's frozen uv environment. Choose an explicit absolute path to owner-controlled private local storage outside the entire checkout. On Windows, use the WSL Linux filesystem for real evidence. Follow `docs/DURABLE_COLLECTION_SESSION.md` for the separate owner-only operator session and backup procedure; a Git-ignored checkout directory is not a private destination.

```sh
uv run --frozen python -m tracker.stage status --park yose --staging-dir /absolute/private/alert-staging
uv run --frozen python -m tracker.stage status --park all --staging-dir /absolute/private/alert-staging
uv run --frozen python -m tracker.stage collect --live --park yose --staging-dir /absolute/private/alert-staging
uv run --frozen python -m tracker.stage recover --park yose --staging-dir /absolute/private/alert-staging
uv run --frozen python -m tracker.stage collect --live --park all --staging-dir /absolute/private/alert-staging
```

`collect` alone is not enough: `--live` and a valid private `NPS_API_KEY` environment variable are both required. Do not put keys in command arguments, URLs, code, issues or chat. Status and recovery are offline and need no key. Codes: `yose`, `romo`, `yell`, `zion`, `grca`. `collect --park all` handles those five sequentially through the same private collector and archive. `status --park all` reads all five existing summaries without a key or network request; `recover` still takes one park at a time. The example absolute destination must be replaced with an owner-controlled local path outside the repository. There is no new GitHub Actions collection workflow or schedule.

The five-park command checks every park's archive, pending receipt, writer locks and collection clock before making its first request. This reduces avoidable partial batches; another writer or a provider/storage failure can still interrupt the sequential run. Its JSON `checks` list contains only completed archive summaries. Exit `0` means all five checks were successfully archived, **not** that the alerts were reviewed, published, or exhaustive. Exit `1` means all five attempts were archived but at least one provider check failed or was quarantined. Exit `2` means a precheck or execution failed; an `interrupted` report can contain earlier committed parks. Inspect each park with `status`, recover any pending receipt offline, and then decide whether another live collection is appropriate. Never assume that retrying the whole batch is atomic or resumes the original attempt.

The separate keyed read-only preflight and the subsequent owner-approved launch collection are recorded in the current handoff. Development regressions use synthetic transport; they do not establish a new real capture, backup, human approval or release.

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

The `status --park all` envelope has `operation: status_all` and a `parks` array in pilot order. It returns exit `0` only after reading all five summaries; a local error returns exit `2` with a safe refusal and no partial array. It creates no staging directory when none exists, and its summaries are still observations of local state rather than a batch transaction or permission to publish.

Exit `0`: status, no receipt to recover, or successful source candidate archived/recovered. Exit `1`: a failed/quarantined collection attempt was successfully archived/recovered. Exit `2`: configuration, local state, conflict, storage, or unexpected execution failure; inspect private state before retrying. Machine output always keeps `publication_performed` and `site_data_written` false. It never says an unsuccessful source check succeeded just because it was archived.

## Locks, bounds and storage assumptions

Staging and archive locks are never stolen or removed automatically. After abnormal termination, first confirm the writer process has stopped and inspect `status` and the archive. Back up the directory before manual recovery. Only then may an operator remove the abandoned `.stage.lock` and, when present, `archive/.writer.lock`, and run offline `recover`. Do not remove locks merely because a file is old; no automatic lock-repair command is provided.

Pending state is limited to 32 regular files and 60 MiB, with 10 MiB per receipt/object. A write reserves space for both temporary and final names before creation. Orphan temporary files are bounded and ignored as uncommitted state, not automatically pruned. The existing archive's disk, history-count and reconstruction limits still apply. A full/damaged archive leaves a durable receipt pending rather than promoting candidate data to the website.

Relative roots, every checkout descendant (including ignored `state/` and `.superpowers/` directories), the checkout and its ancestors, traversal paths, symlinks and non-regular pending files are refused. The staging and archive APIs share the destination guard; checks happen before collection requests or staging writes. This is trusted local-filesystem tooling, not protection against a hostile process with the same filesystem permissions. Hashes detect accidental corruption, not an attacker rewriting both content and hashes. Existing directory permissions and off-host backup remain the operator's responsibility.

Older in-checkout staging roots are refused even for status or recovery. This repair does not move, delete, chmod or recover retained stores. Follow the existing backup/recovery runbooks and deliberately prepare an external private copy before using these commands again.

Python documents `os.replace` atomic renaming and `os.fsync`; same-directory writes and the existing archive primitive are used here: https://docs.python.org/3.12/library/os.html#os.replace and https://docs.python.org/3.12/library/os.html#os.fsync . Process-interruption tests are not hardware power-loss, Windows durability or network-filesystem guarantees.

## Remaining release gates

The current pilot's reviewed data and verified hosting are recorded in the handoff. Staging does not clear source-content review, backup, public promotion or deployment gates. No collection schedule or automatic deployment is enabled. GitHub Actions ephemeral checkouts do not establish ongoing archive persistence; recurring operations still require their separate operator decision.
