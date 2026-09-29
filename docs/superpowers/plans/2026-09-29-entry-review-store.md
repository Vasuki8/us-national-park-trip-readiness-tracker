# Private entry-review ledger implementation plan

> **For agentic workers:** Use superpowers:executing-plans, one verified step at a time.

**Goal:** Retain source captures, extracted context, pending proposals and reviewer dispositions together without any production-data writes.
**Architecture:** A bounded SQLite ledger on a trusted private local filesystem stores immutable, hash-linked observation and disposition events. The Python extractor and a small bounded Node bridge to the existing TypeScript gate remain the only sources of extraction/review decisions. Writes require the expected head and use one SQLite transaction; reads replay committed evidence and check the head. A read-only status and offline record/disposition CLI expose only counts and revision IDs.
**Tech stack:** Existing Python/uv, Node TypeScript, Python standard-library sqlite3; no new packages.
**Spec:** PROJECT_STATUS.md next-task contract; docs/ENTRY_SOURCE_EXTRACTION.md and docs/ENTRY_CHANGE_REVIEW.md.

## Constraints and design decisions

- All source inputs stay private and outside the repository. No network, secret read, deployment, schedule, approval renewal, baseline approval or public proposal promotion.
- Reuse inspect_entry_sources and assessEntrySources. Do not duplicate the review policy in Python.
- The ledger binds one exact guidance inventory. Revised guidance requires a future explicit reconciliation workflow, not silently substituting records in old evidence.
- Reviewer dispositions are retain_hold / request_guidance_revision. They record an identified reviewer and rationale, but do not remove a proposal, change an approval, or attest redistribution permission. Full approval/reconciliation remains separate.
- Matching checks are retained too, so an older matching check cannot replay after a newer check.
- Expected-revision checks apply to writes and decisions. Exact retry of an already committed operation acknowledges it without duplicating history or moving the head backwards.
- Trust boundary: POSIX local filesystem, owner-only directory/database/input files, no symlinks/hard-linked database or FIFO inputs. No hostile same-user mutation or hardware power-loss guarantee. Use SQLite DELETE journal and synchronous EXTRA; never manually delete a hot journal.
- Limits: 8 MiB input, 12 MiB event, 64 events, 128 MiB ledger payload. Fail on capacity, never prune evidence automatically.

## Tasks

- [x] Write and observe failing tests for private reads, complete evidence retention, matching/sticky holds, stale/replayed inputs and explicit dispositions.
- [x] Add bounded Node bridge, Python event-model orchestration and transactional persistence. Validate/replay source extraction plus the original TypeScript gate.
- [x] Add offline CLI with strict private input handling and safe reports. Test rejected paths, mode, symlink/hard-link/FIFO, damaged/rehashed history and foreign databases.
- [ ] Exercise transaction interruption before and after commit, two-writer conflict and retry. Run full repository CI, review diff, update PROJECT_STATUS.md and PR #1 without merging.

## Execution ledger

Resumed from 9f7de2073dbbea09e472144835fc3c16d360ac55 on feat/pilot-foundation. The user approved continuation of the existing next-task contract. Direct git access failed DNS; local work uses an isolated partial workspace with original modules verified by Git blob hash. Full repository verification will run on GitHub CI. No independent reviewer tool is available; report author self-review.

Ruling: use SQLite transactions rather than adding another custom lock-file/rename journal. This avoids duplicating the alert archive and keeps a separate private editorial record, not a substitute alert data pipeline. Durability remains limited to verified local process-interruption cases. Sources: SQLite atomiccommit.html and pragma.html#synchronous; Python sqlite3 documentation.

Local evidence: 16 initial store cases ran against explicit not-implemented methods and failed. CLI tests then exposed missing command implementation. The final local set is 38 Python tests, including two os._exit process-interruption cases and a competing-writer scenario. The bounded bridge error test passes on local Node 22. Full six-guidance integration and the complete existing suite remain for CI on Node 24/Python 3.12. Original local dependency copies match the fetched Git blob hashes.

Author review reproduced a genuine failing WAL-format test: a read accepted that unsupported journal mode. Reading header bytes 18/19 before opening SQLite now refuses it without creating sidecars; the new regression and all 38 local Python tests pass. No old tests were changed.
