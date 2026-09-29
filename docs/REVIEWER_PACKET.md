# Private reviewer inspection packet

## Purpose

The reviewer packet is a local, read-only view of evidence already retained in the private entry-review ledger. It exists to make human review practical before `reconcile`.

Creating or opening a packet does **not** fetch NPS, approve guidance, clear a hold, write public product data, or publish anything.

## Create a packet

Use the current private ledger and the latest retained observation event for one pilot park:

```sh
uv run --frozen python -m tracker.entry_review_cli packet \
  --store /absolute/private/entry-review \
  --output-dir /absolute/private/review-packets \
  --park yose \
  --source-event-revision LATEST_OBSERVATION_EVENT_SHA256
```

Supported park codes are the five fixed pilot profiles: `yose`, `romo`, `yell`, `zion`, and `grca`.

The output directory must be absolute, outside the repository, free of symlink ancestry and under an owner-only parent. The command creates the packet root with mode `0700` and packet files with mode `0600`.

The CLI returns metadata only. It deliberately does not print private filesystem paths or source text. Given the output directory you supplied and the returned `packet_id`, open:

`OUTPUT_DIR/PACKET_ID/index.html`

The sibling `manifest.json` is the metadata/integrity record.

## What the packet shows

For the selected source, the HTML includes:

- ledger and source-event revisions;
- exact source check time and normalized context hash;
- every currently active proposal ID that must be reconciled together;
- current private approved guidance;
- pending reason and before/replacement excerpts when a replacement was supplied;
- retained normalized body text, H1 values and link targets;
- current reviewed baseline metadata;
- reviewer disposition history; and
- prior reconciliation review metadata and old/new guidance hashes.

A failed/context-less latest source event cannot produce a packet. An older source event cannot be selected while a newer retained observation exists. A source with no active holds does not produce a reconciliation-review packet.

## Browser safety

The packet is self-contained and intentionally non-interactive.

Dynamic source/reviewer/guidance values are HTML-escaped. Link targets are text only. There are no anchors, images, frames, objects, embedded content, forms, buttons or scripts.

A Content Security Policy denies all resources by default, including connections, media, frames, objects and forms; only the packet's inline static CSS is allowed.

Actual `script` elements never enter the extractor's comparison text in the first place. Literal text that looks like markup is escaped and displayed as text.

This is defense in depth, not a browser sandbox. Store and open packets only in the private operator environment.

## Integrity and retries

The deterministic packet identity binds:

- current ledger revision;
- park/source identity;
- selected source observation;
- source check time and context hash;
- complete active proposal IDs; and
- current guidance hashes.

The manifest also records SHA-256 of `index.html` and flags `network_performed:false`, `approval_performed:false`, `publication_performed:false`, and `ledger_modified:false`.

An exact retry reuses an identical packet without modifying it. If a packet directory already exists with different bytes or unexpected files, preparation fails rather than overwriting evidence.

Packet installation uses a temporary owner-only directory and an atomic same-directory rename. Packet creation never changes `review.sqlite3`; tests verify the ledger bytes remain unchanged.

## Relationship to reconciliation

The packet is an inspection snapshot, not a write authorization. It does not take `--expected-revision`.

Before reconciliation:

1. inspect the packet;
2. prepare the complete resulting private guidance inventory;
3. run `status` again;
4. confirm the relevant holds/source event are still current; and
5. call `reconcile` using the ledger's current expected revision.

If the ledger changed after packet creation, generate a new packet rather than treating the old HTML as current.

## Current project boundary

Repository tests use synthetic private evidence only. The earlier live NPS compatibility diagnostic did not retain a durable ledger, so no real NPS reviewer packet or durable approved baseline was created by this milestone.

A real five-park editorial review still requires owner-controlled durable private capture storage. Public website data remains unchanged.
