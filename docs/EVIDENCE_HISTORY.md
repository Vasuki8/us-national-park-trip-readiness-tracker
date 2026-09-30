# Private alert evidence and observation history

This increment adds **offline archival capability**, not live NPS integration or a public change feed. No actual park alert observations are included in the repository. Tests use explicitly synthetic notices. The date evaluator, human entry reviews and current site snapshots are unchanged.

## Operator commands

Use Python 3.12+ through the existing uv environment. Import a normalized schema-v1 snapshot produced by `tracker.alerts.collect`, not raw NPS response JSON:

```sh
uv run --frozen python -m tracker.history record --snapshot state/candidate-alerts/yose.json --archive-dir state/alert-history
uv run --frozen python -m tracker.history report --park yose --archive-dir state/alert-history --limit 20
```

These commands do not need or read an API key, make network requests, change the input snapshot, update `data/alerts`, or publish a website. `record` returning zero means the observation was archived, **not** that its source check succeeded. Inspect `source_collection_status` or the report's separate status and success clock. The report omits notice titles, descriptions and input exception text.

Collection remains the existing explicit operation. It must first be validated with an owner-controlled NPS key. A future producer integration should archive every resulting attempt in order, including failures, before considering publication. Do not chain archival after collection only with `&&`: collection deliberately exits nonzero for a failed/quarantined response. Do not enable a schedule merely because these synthetic tests pass.

`state/` is ignored by Git. The CLI rejects archive destinations in this repository's website, data, source, documentation and Git directories, including both `dist/` and `dist-pages/` and their descendants. Destination checks happen before importing a snapshot or writing an archive. Choose an owner-controlled private local directory. Do not upload the archive as an Actions artifact or add it to static assets without a separate source-use and publication review.

## Evidence and commit structure

```text
state/alert-history/
  evidence/<normalized-record-sha256>.json
  parks/yose/head.json
  parks/yose/observations/<observation-sha256>.json
  .writer.lock                    # exists only during an append
```

Evidence objects retain the exact normalized source id, title, description, category and URL. Their digest uses the existing collector's sorted-key UTF-8 JSON representation and `normalized_record` hash scope. This is **not a hash of the full HTTP response**. Unchanged evidence is stored once, including when repeated checks advance the collection clock. Changed and removed evidence remains retrievable.

Observation objects contain the collection metadata, record references, original first/change observation clocks, predecessor hash, sequence number and semantic changes. A read reconstructs the normalized snapshot, validates hashes/schema and re-derives every difference across the committed chain. The objects do not contain request headers, private keys or raw provider responses. Unknown schema fields are rejected rather than silently archived.

An archive-wide exclusive lock serializes cooperating writers. The writer creates and flushes complete immutable objects before atomically replacing the small per-park head. A reader follows one head and immutable predecessors. A failed append can leave unreferenced objects, but they are not committed history. An identical retry verifies/reuses those objects. An explicit initial null head supports first-append retry; a missing head with existing observations fails closed.

This is process-interruption recovery on a trusted local filesystem. Files are flushed with `fsync`; directory sync is performed on POSIX. Windows directory durability and sudden power loss are not asserted by the Linux tests. Network shares, hostile same-user writers, ACL hardening and off-host backup/restore are not supported or verified here. Hashes are not signatures: someone who controls the entire archive could replace its head/history. Do not treat this as tamper-proof storage.

## What history means

| Observation | Result |
|---|---|
| First successful response, including empty | Baseline; no invented new-closure events |
| Same notices, changed collection time or order | New observation; zero semantic changes |
| New id after the baseline | Added to the checked feed |
| Changed text/category/URL for an existing id | Edited in the checked feed; before/after hashes retained |
| Id missing from a validated, non-suspicious response | No longer present in the checked feed; not a reopening |
| Failed/quarantined check | Attempt retained; zero changes; last-good records and success clock preserved |
| Recovery after a failed attempt | Compare against retained last-good records |
| Byte-equivalent normalized retry at the latest timestamp | Return existing observation id; no duplicate append |
| Older or conflicting same-instant observation | Reject; do not rewrite the head |

An initial failure carrying last-good records without their earlier accepted baseline is rejected: import that baseline first. Changed observation clocks are checked against the predecessor. The store also rejects a purported successful response with fewer than half the retained records, preserving the collector's conservative dropout rule. There is no override to approve a bulk deletion in this increment.

No history timestamp is a claim about when a road actually closed or reopened. `source_updated_at` and `published_at` remain null under the current collector contract. Human review timestamps are never refreshed by the archive.

## Limits and recovery

Limits are deliberate pilot safeguards: 10 MiB per normalized snapshot/object; 4096 committed observations per park; 256 MiB total archive files; 65536 filesystem entries; 64 MiB total reconstructed snapshot JSON per read/append. Deduplicated evidence can expand in memory, so both stored and reconstructed data have limits. The Python interface allows smaller bounds for tests/operations, not larger unchecked bounds.

The report verifies the committed chain, then shows the latest 1–100 observations (20 by default) and at most 100 changes per observation. It explicitly reports omitted observation/change counts. The archive retains the full committed data regardless of report truncation.

At a limit, lock conflict, malformed JSON, missing object, hash mismatch or inconsistent chain, the operation stops. **Nothing is automatically pruned or repaired.** Back up the private directory and investigate before changing limits or migrating storage. Do not clear `.writer.lock` until its owner process is confirmed stopped. A crash after head replacement but before acknowledgement can leave a completed append; retry the identical snapshot to resolve that ambiguity.

The private archive is not backed up or persisted by GitHub Actions. Its contents must live on operator-controlled persistent storage before scheduled collection is enabled. Public-history generation, raw-response capture, rights approval, publication/rollback and editorial source-change detection remain separate release gates.

## Verification

The new tests cover semantic differences, retained failures, replay conflicts, source/hash validation, orphan objects, interrupted head writes, writer exclusion, missing/corrupt chains, reconstructed-memory limits, protected output paths, CLI sanitization/truncation and integration with the unchanged collector using synthetic responses. Run the entire repository suite, not just these tests:

```sh
uv run --frozen python -m unittest discover -s tests -p 'test_*.py' -v
```

Implementation references: Python 3.12 standard-library documentation for `os.replace`, `os.link`, `os.fsync`, `json.object_pairs_hook` and `parse_constant`:
https://docs.python.org/3.12/library/os.html
https://docs.python.org/3.12/library/json.html
