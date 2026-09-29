# Project status and handoff

Updated: **September 29, 2026 (America/Toronto)**.

**The explicit persistent live entry capture → private ledger → reviewer packet operator path is now implemented and CI-verified. Actual NPS entry-page compatibility remains verified for all five pilot parks, but this milestone did not run a real durable capture session or approve any real context baseline. Public guidance and alert data remain unchanged.**

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

All five capture attempts form one complete ledger observation event. Successful raw HTML is retained inside the owner-only SQLite event; failed captures are retained as failed observations rather than discarded or converted into empty success. Existing reconciled baselines are reused automatically. An existing ledger keeps its own current private guidance inventory rather than silently adopting changed repository guidance.

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

Code/test head: **`60ed64031272a428010cc493f4a4d946699b5554`**.

**Verify pilot #71, run `36596713485`, job `109503397710`, completed successfully.**

| Check | Verified result |
|---|---:|
| Node core/data/review tests | 144 passed |
| Python collector/archive/extraction/ledger/reconciliation/packet/live-operator tests | 285 passed |
| Generated-output tests | 18 passed |
| Chromium browser tests | 74 passed |
| **Total automated tests** | **521 passed** |
| Astro check | 24 files; 0 errors, 0 warnings, 0 hints |
| Production static build | 14 HTML pages plus `build.json` |

The live-operator increment adds eight Python methods. RED #66 (`36595233082`) failed because `tracker.entry_review_live` did not exist. The first implementation runs then exposed two test-harness errors rather than product failures: a helper named `run` overrode `unittest.TestCase.run`, and a second synthetic batch reused the first event's write clock. Both harness issues were corrected without changing product semantics. Full #70 passed; #71 reverified the final direct-digest refactor.

Coverage includes deliberate live opt-in, pre-network expected-revision/path checks, complete five-source persistence, current-head append behavior, failed-source retention without fake packets, post-commit packet failure without rollback, safe CLI output and exit-1 partial-completion semantics.

Verification artifact `pilot-verification`, ID **11045953817**, contains the production build, existing screenshots and lockfile—not live editorial ledgers, source captures or reviewer packets. CI-reported ZIP SHA-256: `713fa9eb758a75d0dc8e12e838e904cd241a4ba59dd6385770d005aeb9f67956`.

Review was author self-review, not independent approval. This documentation-only handoff receives a separate CI run; do not infer it from #71.

## Previously verified real-page compatibility

Diagnostic run `36575873171`, job `109431220513`, captured the five exact configured NPS entry pages on September 29, 2026. All five returned HTTP 200; all body-text/link contexts extracted; all six saved guidance excerpts were uniquely present; temporary ledger replay succeeded.

Every source reason was `context_not_reviewed`, with six temporary holds and **zero approved context baselines**. Those captures were deliberately discarded after the diagnostic. They are compatibility evidence, not a durable reviewed reference archive and not proof that park requirements are unchanged.

Exact safe retrieval metadata and hashes remain in `docs/LIVE_ENTRY_COMPATIBILITY.md`.

## Remaining gates

No real reviewer has used the new reconciliation command on a durable NPS capture. Therefore there are still **zero durable real approved context baselines** created by this workflow.

The private ledger is owner-only local POSIX storage, not hosted durable storage, encryption, authenticated reviewer identity, multi-host storage or off-host backup. Hardware power-loss, Windows/network filesystems and hostile same-user mutation remain outside verified guarantees.

Source-content redistribution/rights review remains separate from guidance review. Hashes prove internal consistency, not factual truth, source authenticity or permission to republish.

The keyed NPS alerts API was not checked during this milestone. The last historical key diagnostic remains the earlier empty-key/no-request result; do not treat it as current configuration.

No scheduler, deployment, indexing, advertising, tracking, account system, spending or provider agreement was activated. Neither pilot release milestone is declared complete.

## Next coherent task

The persistent operator path now exists. The next source-review milestone is an **owner-controlled real five-source capture and human review session** using this command, followed by explicit `reconcile` actions only for guidance actually approved against those retained contexts.

That real session was **not** performed in this development environment because the current tools do not provide the user's durable private POSIX/WSL filesystem. Do not substitute public GitHub Actions artifacts or repository files for the private editorial ledger.

If a suitable owner-controlled POSIX/WSL storage location is not available yet, prioritize the remaining durable-storage/backup decision instead of inventing a temporary hosted source archive.

The keyed NPS alert API remains a separate gate and should use the existing preflight/staging/preview path once an owner-controlled `NPS_API_KEY` is configured.

## Verification lineage

Prior communicated totals: 79 foundation; 109 source coverage; 167 private history; 206 staging; 246 visitor history; 293 previews; 309 planning links; 347 accessibility; 380 selected-source gate; 416 extraction; 460 ledger/identity; 488 live entry compatibility. Current verified implementation: **521 tests** at `60ed640`, run #71. PR #1 remains draft and unmerged.
