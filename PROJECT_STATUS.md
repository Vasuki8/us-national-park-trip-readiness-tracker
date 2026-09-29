# Project status and handoff

Updated: **September 29, 2026 (America/Toronto)**.

**Private content-addressed backup/verify/restore is now implemented and CI-verified for the entry-review ledger, in addition to the persistent live capture → ledger → reviewer-packet path. No real durable NPS capture, real ledger backup, or real context approval was performed in this development environment. Public guidance and alert data remain unchanged.**

Repository: `Vasuki8/us-national-park-trip-readiness-tracker`.  
Branch: `feat/pilot-foundation`. Draft PR #1 remains unmerged.  
Main remains `a9d9c19e8307828c5bdb6f331e24ca3fe7afffce`. No deployment was performed.

## Standing product direction

The eventual product remains AdSense-first, light-theme and free of paid-data dependencies. Validate the five-park pilot before expanding to 20 parks. Trustworthy source evidence precedes indexing or advertising. Never infer an all-clear, reopening, permit exemption or annual validity from missing information.

The public build remains 14 HTML pages plus `build.json`, with park/state search, five park pages, date-aware entry guidance, source evidence, checklists, notice history and seven official planning links per park. Yosemite and Rocky Mountain have dated rules; Yellowstone, Zion and Grand Canyon retain undated source observations. Public alert snapshots remain `never_checked`; public histories and the public entry-review register remain empty.

Existing alert collection/archive/staging, candidate previews, visitor history, accessibility repairs, source-change gate, HTML extraction, live entry-page compatibility diagnostic and private review ledger remain in place. Do not rebuild them.

## New: explicit private reconciliation

The private ledger now supports a fourth write operation, `reconcile`, in addition to `record`, `disposition` and recovery/status operations.

A reconciliation request contains exactly:
- `source_event_revision`: a committed observation event containing the source context the reviewer inspected.
- `proposal_ids`: the active holds being resolved.
- `reviewer` and `rationale`: operator-supplied review metadata.
- `reviewed_at`: the actual editorial review time.
- `records`: the complete resulting private guidance inventory.

Reconciliation is source-level. If a source has multiple active proposals, all of them must be selected; Rocky Mountain's shared source cannot be partially approved. The selected source observation must be the latest retained observation for that source and at least as new as every cleared proposal.

The replacement guidance inventory is validated through the existing rule/note validators. Unaffected records must remain byte-equivalent. Affected records keep the same identity, park and official source, use the exact approved review time, and preserve their existing rights basis and rights-review timestamp. Extra top-level or evidence fields are refused.

The approved excerpt for every affected record must occur exactly once in the retained source context. Missing or duplicated replacement text fails closed. The reconciliation event stores the complete new records plus hashes of the previous and next guidance revisions; prior events remain immutable and reconstructable.

### Reviewed context baseline semantics

Reconciliation derives a persistent **schema-v2 context baseline** from the retained source observation. V2 distinguishes the real editorial sequence: source captured first, then human review/approval. Legacy schema-v1 baselines keep their previous clock semantics.

Subsequent observations automatically consume ledger-held baselines. A caller cannot replace them through a new capture request. When the first explicit reconciliation affects only one source, already-validated legacy baselines for unrelated sources are carried forward rather than silently dropped.

A later matching source observation does not automatically clear a sticky hold. A reviewer may explicitly reconcile from that newer observation if it is the latest retained evidence and the complete source-level hold set is selected.

This is **private editorial approval inside the ledger**, not public publication. The reconcile command does not write `data/`, the website, alert snapshots, public history, deployment state or advertising configuration.

Contract: `docs/GUIDANCE_RECONCILIATION.md` and `docs/ENTRY_REVIEW_LEDGER.md`.

## New: private read-only reviewer packets

`tracker.entry_review_packet` turns one verified ledger snapshot into a deterministic owner-only review packet without network access, ledger mutation, reconciliation, approval or publication.

The operator selects a pilot park and the **latest retained observation event** for that source. Packet generation refuses an unknown/stale event, a source with no retained comparison context, or a source with no active hold.

The packet contains:

- current private approved guidance for the source;
- every active proposal ID that must be reconciled together at source level;
- pending reasons, before excerpts and source-supplied replacement excerpts when present;
- the retained normalized text/H1/link comparison context and context hash;
- exact capture/proposal/review clocks;
- current baseline metadata;
- prior reviewer disposition history; and
- prior reconciliation metadata and old/new guidance hashes.

Dynamic material is escaped. Real `script` elements remain outside the extractor scope; literal script-looking source text is rendered as text. The generated HTML contains no links, images, frames, forms, buttons or scripts and carries a strict Content Security Policy that denies network/connect/object/frame/form activity. Source link targets are shown only as text.

The output directory and packet files are owner-only (`0700` directories, `0600` files) and must live outside the repository under an owner-only parent. Each packet is installed atomically as:

`OUTPUT_DIR/PACKET_ID/index.html`  
`OUTPUT_DIR/PACKET_ID/manifest.json`

The manifest contains metadata/hashes only, including the ledger revision, source event revision, context hash, complete active proposal IDs, guidance hashes and SHA-256 of the HTML. It contains no retained context or private filesystem path. Exact retries are idempotent; a corrupted existing packet is refused rather than overwritten.

A packet is only an inspection snapshot. It deliberately has no `expected_revision` write argument and cannot approve anything. Before a later reconciliation, the operator must re-read the ledger and use its then-current revision.

Operator contract: `docs/REVIEWER_PACKET.md`.

## New: explicit persistent live capture operator path

`tracker.entry_review_live` is the first retained live-entry operator workflow. It reuses the existing fixed NPS transport, source extractor, transactional editorial ledger and read-only reviewer packets; it does not create a second source store.

Before the first network request it requires:

- explicit `--live`;
- an absolute private ledger path accepted by the existing POSIX ledger boundary;
- an absolute packet-output path outside the repository under an owner-only parent; and
- `--expected-revision empty` for a new ledger, or the exact current ledger SHA-256 for a later batch.

A stale expected revision or unsafe packet destination refuses **before network**. The SQLite write still rechecks the expected revision inside its transaction, so a concurrent writer cannot be silently overwritten after capture.

The command then makes one credential-free HTTPS GET to each of the five fixed NPS entry sources using the already-tested transport: no API key, cookies, redirects, retries or arbitrary URL input. Each response remains bounded to 1 MiB and is validated for status, content type/encoding, length and UTF-8 before it can become a successful capture.

All five capture attempts form one complete ledger observation event. Successful raw HTML is retained inside the owner-only SQLite event; failed captures are retained as failed observations rather than discarded or converted into empty success. Existing reconciled baselines are reused automatically. The live append also preserves the latest validated legacy schema-v1 baseline input until explicit reconciliation creates ledger-held baselines, so a later capture cannot manufacture a fresh `context_not_reviewed` hold merely by dropping prior reviewed context. An existing ledger keeps its own current private guidance inventory rather than silently adopting changed repository guidance.

After the ledger commit, the command prepares reviewer packets for every source that has active holds and retained comparison context. A failed source receives no fabricated packet. Packet-generation failures do **not** roll the already committed live evidence back.

Operator command:

```sh
uv run --frozen python -m tracker.entry_review_live \
  --live \
  --store /absolute/private/entry-review \
  --packet-output-dir /absolute/private/review-packets \
  --expected-revision empty
```

For every later run, first use `entry_review_cli status` and replace `empty` with the exact returned revision.

Exit semantics:

- **0** — the complete batch was committed, all five captures succeeded, and every source requiring review has a packet (or no packet is needed).
- **1** — the batch was committed, but at least one capture or required packet is incomplete. This is retained evidence, not a rollback; inspect the safe JSON report and ledger.
- **2** — configuration, validation, stale-write or unexpected failure prevented a normal report. Re-read ledger status before retrying because concurrent/post-commit failures must never be guessed from an exit code alone.

The safe JSON report exposes source URL, HTTP status, capture reason, capture/context hashes, active-hold counts, packet IDs and the committed ledger/source-event revisions. It excludes raw HTML, retained normalized text and private filesystem paths.

This command never calls `reconcile`, never updates public `data/`, never deploys, and never schedules itself. No `NPS_API_KEY` is read or needed.

Contract: `docs/PERSISTENT_ENTRY_CAPTURE.md`.

## New: private ledger backup, verification and restore

`tracker.entry_review_backup` provides an owner-only backup/restore mechanism for the private editorial SQLite ledger. It does not back up public site data and performs no network request, source capture, review decision, reconciliation or publication.

Backup first performs a full ledger replay. It then uses SQLite's backup API to create a transactionally consistent database snapshot in a temporary owner-only directory. The copied database is replayed again and must equal the previously verified logical ledger state before it can be accepted.

A content-addressed manifest binds:

- ledger revision;
- event, guidance-record and pending-proposal counts;
- exact database byte length;
- SHA-256 of the backed-up SQLite database; and
- explicit `network_performed:false`, `approval_performed:false`, and `publication_performed:false`.

The backup ID is SHA-256 over that manifest core. A completed bundle is:

`BACKUP_ROOT/BACKUP_ID/review.sqlite3`  
`BACKUP_ROOT/BACKUP_ID/manifest.json`

Backup roots and files are owner-only and must be outside the repository under an owner-only parent. Exact retries reuse an identical verified bundle. Corrupt/mismatched bundles or unexpected files are refused rather than overwritten.

`verify` checks private permissions, exact bundle contents, manifest identity, database size/SHA-256 and full semantic ledger replay without modifying the backup.

`restore` accepts only a fully verified bundle and only a brand-new destination. It copies into a temporary owner-only ledger directory, replays the restored database, and atomically renames it into place only after the restored head/counts match the backup manifest. Existing destinations are never overwritten. Interrupted backup/restore tests confirm no completed destination is exposed.

Commands and limitations: `docs/ENTRY_REVIEW_BACKUP.md`.

This mechanism makes local backup/restore testable, but it does **not** create an off-host backup service, choose backup media, encrypt the database, authenticate reviewers, certify native Windows/network filesystems, or prove hardware power-loss durability. Those remain operator/storage decisions.

## New: read-only release-readiness report

`tracker.release_readiness` consolidates the pilot launch gates into one deterministic, non-mutating report. It never contacts providers, deploys, changes indexing, enables advertising, writes public/private state, or interprets missing evidence as success.

Default repository-only command:

```sh
uv run --frozen python -m tracker.release_readiness --format text
```

Machine-readable form:

```sh
uv run --frozen python -m tracker.release_readiness --format json
```

When owner-controlled private evidence exists, the report can also replay the private ledger and verify a specific content-addressed backup before evaluating those private gates:

```sh
uv run --frozen python -m tracker.release_readiness \
  --format text \
  --store /absolute/private/entry-review \
  --backup /absolute/private/backups/BACKUP_ID
```

The seven gates are:

1. durable source review;
2. NPS alert API validation;
3. private storage backup;
4. source-rights review;
5. hosting and rollback;
6. search indexing; and
7. advertising readiness.

Status values are only `pass`, `blocked`, or `not_checked`. Every non-pass status is release-blocking.

The current repository-only result is deliberately **BLOCKED**:

- durable source review — `not_checked`: no owner private ledger supplied;
- NPS alert API — `blocked`: all five public snapshots are still `never_checked`;
- storage backup — `not_checked`: no owner private ledger/verified backup supplied;
- source rights — `not_checked`: all six public guidance records carry rights metadata, but broader source-content/commercial rights review is external and is not self-certified by those fields;
- hosting/rollback — `blocked`: no production deployment path is configured;
- indexing — `blocked`: HTML meta robots, `robots.txt`, and response headers all still disable indexing;
- advertising — `blocked`: no ad integration is enabled.

The alert gate intentionally never describes `never_checked` snapshots as “no alerts” or an all-clear. If future public snapshots become successful, the static report still returns `not_checked` until freshness/provider compatibility has release evidence rather than self-promoting collection success.

The private source-review gate passes only when the verified private state has schema-v2 reviewed context baselines for all five fixed entry sources and zero pending proposals. The private backup gate passes only when a previously verified backup manifest matches the exact current ledger head and event count.

This report is an evidence summary, not an authorization to launch. Removing `noindex`, adding deployment/ad code, or supplying a private ledger changes individual evidence but does not itself approve release.

Contract: `docs/RELEASE_READINESS.md`.

## New: NPS alert preflight gate hardening

The read-only keyed NPS alert preflight was rerun on the current feature branch after expanding its validation trigger to changes in the workflow, `tracker/preflight.py`, and `tracker/alerts.py`. It remains unscheduled and has read-only repository permissions.

Current run **36607959537**, job **109541744290**, head **16dda2f20c504ada6d9740c1de38f458e47cb7f9**, returned:

```json
{"schema_version":1,"mode":"read_only","status":"not_configured","gate_passed":false,"publication_performed":false,"checks":[]}
```

The runner still received no usable `NPS_API_KEY`, so it made zero provider requests and changed no data. This establishes the current branch configuration state for that execution; it does not expose or directly inspect repository secrets.

The preflight exit contract is now release-gate aligned:

- `verified` / `gate_passed:true` → exit 0;
- `needs_review` → exit 1;
- `not_configured` or `invalid_configuration` → exit 2.

Therefore the current preflight workflow is intentionally **red** while the key is unavailable. A successful Actions job can no longer visually imply that the alert integration is verified when `gate_passed:false`.

The public alert snapshots are untouched and remain `never_checked`; this diagnostic does not publish or stage data. Configure the owner-controlled repository secret named exactly `NPS_API_KEY` before expecting this gate to pass. Do not send the key through chat, issues, or committed files.

Contract and exact run evidence: `docs/NPS_PREFLIGHT.md`.

## New: gated GitHub Pages deployment and rollback path

`.github/workflows/pages-release.yml` adds a production-hosting path without making the site live. The workflow is **manual-only** (`workflow_dispatch`); it has no push, pull-request, or schedule trigger.

Every deployment or rollback requires all four explicit inputs:

- `mode`: `deploy` or `rollback`;
- `target_sha`: an exact lowercase 40-character commit SHA;
- `verify_run_id`: the GitHub Actions run ID containing the verified build artifact; and
- `confirmation`: exactly `DEPLOY_VERIFIED_PILOT` or `ROLLBACK_VERIFIED_PILOT` for the selected mode.

The workflow queries GitHub for that run and refuses unless it is a **successful `Verify pilot` push run on the repository default branch** and its `head_sha` exactly matches `target_sha`. It then downloads that run's existing `pilot-verification` artifact. It does not check out source or run a fresh build during release, so deployment and rollback use the exact static output that already passed verification.

Only `_verified/dist` is repackaged as the Pages artifact. The workflow requires `dist/index.html` and `dist/build.json` and refuses symlinks.

The current verified frontend uses root-absolute links and Astro asset URLs. Default GitHub **project Pages** would serve under `/us-national-park-trip-readiness-tracker/` and would therefore break those URLs. The workflow reads the official `actions/configure-pages@v5` `base_path` output and refuses any nonempty Pages base path **before** artifact upload/deployment. The current build therefore requires root hosting, such as an appropriately configured custom domain, unless the application is later made base-path aware.

The workflow grants only `contents: read`, `actions: read`, `pages: write`, and `id-token: write`. Deployment uses the standard `github-pages` environment and `actions/deploy-pages@v4`.

Rollback is the same artifact path with `mode: rollback` and an older successful default-branch Verify run. It never runs `git revert`, `git reset`, or pushes source changes. The current `pilot-verification` artifact retention is seven days, so this rollback mechanism only covers verified runs whose artifacts have not expired.

No release workflow was dispatched during this milestone. The website remains unpublished, PR #1 remains draft/unmerged, and all existing `noindex` controls remain unchanged. `public/_headers` is retained in the build, but GitHub Pages does not by itself establish that those custom response headers are effective; real hosting/header behavior remains part of the post-deployment verification gate.

The release-readiness `hosting_rollback` gate now moves from `blocked` to **`not_checked`**: a deployment/rollback mechanism exists, but no real production URL or rollback has been exercised.

Contract: `docs/PAGES_RELEASE.md`.

## New: exact public NPS text source-rights evidence

`data/source-rights.json` now records the commercial-use evidence for the **exact six public guidance records** and their five NPS source pages. This is deliberately narrower than a claim about all material on NPS websites.

The review is grounded in the current official NPS disclaimer and Arrowhead-use guidance:

- NPS-created material on the NPS website is generally considered public domain unless otherwise indicated;
- NPS asks for source acknowledgement, and commercial republication should include a reference to the original U.S. Government work, such as **“No protection is claimed in original U.S. Government works.”**;
- third-party material must not be assumed public domain; and
- the NPS Arrowhead and other protected marks are not covered by the public-domain rule and require separate authorization.

The manifest therefore allows only:

- the six already-reviewed short NPS text excerpts;
- the project's original planning summaries tied to those records; and
- source attribution/links.

It explicitly records **no third-party material, NPS marks, photographs, graphics, audio/video, or private raw captures** as approved for public reproduction.

`scripts/validate-source-rights.ts` makes exact manifest coverage part of the normal build gate. Omitting or duplicating a guidance record, changing its source URL, claiming marks/media/third-party content, changing the policy URLs, or changing the commercial notice fails validation.

The site footer now includes the commercial U.S. Government-work notice while retaining the existing independent/non-endorsement statement.

The release-readiness source-rights gate now passes only when:

- all six public guidance records retain their record-level rights metadata;
- `source-rights.json` exactly covers all six record/source pairs;
- every covered item remains classified as NPS government text with no third-party/mark/media reproduction;
- the commercial notice is present in the public layout; and
- the public application contains no media asset or reproduced NPS mark/media reference outside this text-only scope.

This **passes the current public-text scope only**. It is not legal advice or blanket clearance for other NPS pages/content. Adding photos, graphics, logos/marks, audio/video, third-party material, or public raw source captures requires a new rights review and evidence update.

Contract: `docs/SOURCE_RIGHTS.md`.

## TDD and self-review record

The reconciliation contract was developed test-first.

- Verify pilot #47 (`36579697560`) failed because `reconcileEntryReview` did not exist.
- Initial implementation exposed a clock-model mismatch between legacy baselines and explicit review-after-capture; schema-v2 baselines were introduced without weakening v1.
- Verify pilot #51 (`36581315199`) reproduced acceptance of extra unreviewed schema fields; exact record/evidence shape is now required.
- Verify pilot #53 (`36581590068`) reproduced rejection of a valid newer matching source observation while an older hold remained; reconciliation now binds to the latest retained source observation.
- Verify pilot #56 (`36582585446`) reproduced loss of an unrelated reviewed legacy baseline when reconciling one source; unaffected latest validated baselines are now preserved.

The final review-focus tests also cover absent and duplicated approved excerpts, partial source-level proposal selections, exact retry, caller baseline override, stale source observations, CLI redaction and unchanged rights metadata.

Review was **author self-review**, not independent approval.

## Exact implementation verification

Code/test head: **`df908a6b4d608ef5c57ca12a2b8bc872ac039bd4`**.

**Verify pilot #103, run `36619784653`, job `109581929909`, completed successfully.**

| Check | Verified result |
|---|---:|
| Node core/data/review/rights tests | 147 passed |
| Python collector/archive/extraction/ledger/reconciliation/packet/live/backup/readiness/Pages/rights tests | 320 passed |
| Generated-output tests | 18 passed |
| Chromium browser tests | 74 passed |
| **Total automated tests** | **559 passed** |
| Astro check | 24 files; 0 errors, 0 warnings, 0 hints |
| Production static build | 14 HTML pages plus `build.json` |

The source-rights increment adds three Node tests and five Python tests. RED #94 (`36618285770`) confirmed the manifest, footer notice, and passing rights gate were absent. RED #97 (`36618654174`) then confirmed the build-boundary validator itself was still missing. During implementation, #100–#102 exposed two malformed Python patch remnants in `release_readiness.py`; those were traced to duplicated/truncated generated edits and removed without weakening the rights policy. #103 passed the complete implementation.

Coverage verifies exact six-record/source pairing, official NPS policy URLs, the commercial U.S. Government-work notice, refusal of omitted/duplicated rights evidence, refusal of marks/media/third-party claims, absence of public NPS marks/media, and the source-rights readiness gate passing only for this exact text scope.

Implementation verification artifact `pilot-verification`, ID **11056593722**, had CI-reported ZIP SHA-256 `f7b4fadbe2dc207049a37dc19a8080d3bfb6c36468d9ec0f18dd4cbf5cc9d12d`.

The documentation head **`a0ebdc23a6b66391fcfea4b92cd04c714774b92e`** then passed **Verify pilot #105**, run `36620211515`, job `109583902805`, with the same 559-test suite/build. Its artifact ID was **11056884522**, ZIP SHA-256 `44217eeb7fb194eca35814ba951aa444366433db8787b78f4e836c870522c090`.

Review was author self-review because no independent reviewer/subagent tool is available. No deployment, indexing, advertising, or live-data state changed. This final status-only handoff edit receives its own CI run.

## Previously verified real-page compatibility

Diagnostic run `36575873171`, job `109431220513`, captured the five exact configured NPS entry pages on September 29, 2026. All five returned HTTP 200; all body-text/link contexts extracted; all six saved guidance excerpts were uniquely present; temporary ledger replay succeeded.

Every source reason was `context_not_reviewed`, with six temporary holds and **zero approved context baselines**. Those captures were deliberately discarded after the diagnostic. They are compatibility evidence, not a durable reviewed reference archive and not proof that park requirements are unchanged.

Exact safe retrieval metadata and hashes remain in `docs/LIVE_ENTRY_COMPATIBILITY.md`.

## Remaining gates

No real reviewer has used the new reconciliation command on a durable NPS capture. Therefore there are still **zero durable real approved context baselines** created by this workflow.

The private ledger remains owner-only local POSIX storage, not hosted durable storage, encryption, authenticated reviewer identity or multi-host storage. Backup/verify/restore mechanics are now tested, but no off-host target, retention schedule, removable-media policy or cloud backup has been configured. Hardware power-loss, native Windows/network filesystems and hostile same-user mutation remain outside verified guarantees.

The exact six-record public NPS **text-only** rights scope now has explicit evidence and passes its release-readiness gate. This does not clear private raw captures, NPS marks/media, third-party material, or future source uses. Hashes prove internal consistency, not factual truth or source authenticity.

The keyed NPS alerts preflight was rechecked on the current branch and is still blocked because the runner received no usable `NPS_API_KEY`. No provider request was made. See run 36607959537; do not treat its red conclusion as a product-test regression.

No scheduler, real deployment, indexing, advertising, tracking, account system, spending or provider agreement was activated. A manual Pages deployment/rollback workflow now exists but was not dispatched. Neither pilot release milestone is declared complete.

## Next coherent task

The code-side private storage gates now include capture, ledger replay, reviewer packets, reconciliation, backup/restore, and a manual verified-artifact hosting/rollback path. The next trust milestone remains an **owner-controlled real five-source capture and human review session** on durable private POSIX/WSL storage, plus successful keyed NPS alert preflight.

Before reviewing or reconciling real guidance, create a content-addressed ledger backup with `entry_review_backup backup`, run `verify`, and keep a second verified copy on owner-controlled storage separate from the working ledger. Then inspect the generated packets and use `reconcile` only for guidance a human actually approves.

That real session cannot be performed in this development environment because the current tools do not provide the user's durable private POSIX/WSL filesystem or backup destination. Do not substitute GitHub Actions artifacts, repository files or public hosted storage for the editorial ledger/backup.

The keyed NPS alert API remains a separate gate and should use the existing preflight/staging/preview path once an owner-controlled `NPS_API_KEY` is configured.

## Verification lineage

Prior communicated totals: 79 foundation; 109 source coverage; 167 private history; 206 staging; 246 visitor history; 293 previews; 309 planning links; 347 accessibility; 380 selected-source gate; 416 extraction; 460 ledger/identity; 488 live entry compatibility. Current verified implementation: **559 tests** at `df908a6`, run #103. PR #1 remains draft and unmerged.
