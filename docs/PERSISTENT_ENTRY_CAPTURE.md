# Persistent private entry capture

## Purpose

`tracker.entry_review_live` is the owner-operated bridge from the already-tested five fixed NPS entry pages into the existing private editorial ledger and reviewer packets.

It is intentionally not a scheduled collector and not a publication pipeline.

## Storage prerequisite

Run this only with owner-controlled private POSIX storage (Linux/macOS or an appropriate WSL/Linux environment). The existing ledger has not been certified for native Windows filesystems or network filesystems.

Create/choose a private parent directory outside the repository. The packet parent must be owner-only; the ledger itself creates its own `0700` directory and `0600` SQLite file.

Do **not** use public repository paths, GitHub Actions artifacts, public CI workspaces, synced public folders or temporary hosted files as the durable editorial ledger.

## First run

```sh
uv run --frozen python -m tracker.entry_review_live \
  --live \
  --store /absolute/private/entry-review \
  --packet-output-dir /absolute/private/review-packets \
  --expected-revision empty
```

Before any network request the command verifies explicit live opt-in, the expected empty/current ledger head and the private packet destination.

## Later runs

Read current state first:

```sh
uv run --frozen python -m tracker.entry_review_cli status \
  --store /absolute/private/entry-review
```

Then run the live command with the exact returned `revision`:

```sh
uv run --frozen python -m tracker.entry_review_live \
  --live \
  --store /absolute/private/entry-review \
  --packet-output-dir /absolute/private/review-packets \
  --expected-revision CURRENT_HEAD_SHA256
```

A stale head refuses before requests. The store rechecks the head when it takes its write transaction, protecting against a writer that races after preflight.

## Network contract

Only the five URLs in `tracker.entry_sources.PROFILES` are fetched.

For each source the reused transport makes one HTTPS GET to `www.nps.gov`:

- no API key or Authorization header;
- no cookies;
- no arbitrary URL;
- no redirect following;
- no retry loop;
- `Accept: text/html`;
- `Accept-Encoding: identity`;
- 15-second socket-operation timeout;
- maximum 1 MiB body;
- strict response status, MIME/charset/content-encoding, length and UTF-8 checks.

The five requests form one complete editorial observation batch.

## What is persisted

On successful response validation, the exact HTML string, fixed source URL, content type and capture time are stored in the existing hash-linked SQLite event and are replayed through the existing extractor/review gate.

On a failed response, the ledger retains a failed capture with its observation time. It is never rewritten as an empty successful page.

The command's safe report also includes HTTP status, transport reason and raw SHA-256 when available. Those receipt details are operator-report metadata; the ledger's authoritative source evidence remains the validated capture/event itself.

For an existing ledger, the command uses the ledger's current private guidance inventory. It does not silently replace that inventory from changed repository JSON; guidance changes continue to require explicit reconciliation.

If explicit reconciliation baselines exist, the ledger injects them internally as before. Before any reconciliation, the live operator preserves the latest validated legacy schema-v1 baseline input from the most recent observation. This prevents a reviewed legacy context from being silently dropped and converted into a new `context_not_reviewed` hold on the next live append.

## Reviewer packets

After the observation transaction commits, the command replays the ledger and prepares one packet per source that:

1. still has active proposals; and
2. has a retained comparison context in this latest observation.

A failed/context-less source gets `packet_status: context_unavailable`. A source with no holds gets `not_needed`. Packet-write failures are reported as `failed` and do not undo the source observation.

Use the returned `source_event_revision` and packet IDs for review. The packet itself remains read-only; see `docs/REVIEWER_PACKET.md`.

## Exit codes

### 0 — review batch ready

- ledger batch committed;
- all five source captures succeeded;
- every source with active holds has a packet, or no packet is needed.

This does not mean the guidance is approved or unchanged.

### 1 — committed but incomplete

The ledger batch **was committed**, but at least one capture or required packet is incomplete.

Inspect the JSON source rows and the ledger. Do not repeatedly retry merely to make the exit code green; a failed check is evidence.

### 2 — no normal completion report

Preflight, validation, stale-write or an unexpected failure prevented the command from returning the normal report.

Re-read ledger `status` before retrying. A concurrent writer or unusual post-commit failure must be resolved from the ledger, not inferred from this code alone.

## Safe report fields

The JSON report contains:

- committed ledger revision;
- committed source-event revision;
- batch/pending-proposal counts;
- capture/review readiness booleans;
- packet count;
- per-source fixed URL, checked time, HTTP status, capture reason, raw SHA-256, context reason/hash, active-proposal count, packet status and packet ID;
- `network_performed:true`;
- `ledger_committed:true`;
- `approval_performed:false`;
- `publication_performed:false`;
- `public_data_written:false`.

It does not include raw HTML, extracted text, reviewer rationale or private filesystem paths.

## What it deliberately does not do

The command never:

- reconciles or approves guidance;
- refreshes rights review;
- updates public `data/`;
- publishes visitor history;
- runs the alert API;
- reads `NPS_API_KEY`;
- deploys;
- schedules itself;
- indexes pages; or
- enables advertising/analytics.

## Current verification boundary

Automated tests use synthetic responses and real ledger/extractor/packet code. The underlying fixed-source transport separately passed real five-page NPS compatibility testing earlier on September 29, 2026.

This milestone did not create a real durable ledger because the development tool environment is not the user's owner-controlled persistent private filesystem.

The next real-world step is to run this command on the owner's private POSIX/WSL storage, inspect the generated packets and then use `reconcile` only for guidance a human actually approves.


## Legacy-baseline regression verification

Author review added a regression for an existing ledger with a validated schema-v1 Yellowstone context baseline. RED run #73 (`36600646532`) reproduced a false new hold because the live operator supplied `baselines: []` on every append. The fix now carries forward the latest validated legacy baseline input only while the ledger has no explicit reconciliation baselines.

Verify pilot #74 (`36600851931`, job `109517542233`) passed the full suite: 144 Node + 286 Python + 18 generated-output + 74 Chromium = **522 tests**, with Astro 24 files and zero errors/warnings/hints. Artifact `11049198460`, CI ZIP SHA-256 `1c0ba13ac55e14127d16ab396aa00b94d25bdc72822b522ebc28569b64273af5`.
