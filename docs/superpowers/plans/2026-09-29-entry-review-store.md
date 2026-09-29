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
- [x] Exercise transaction interruption before and after commit, two-writer conflict and retry. Run full repository CI, review diff, prepare PROJECT_STATUS.md and PR #1 handoff without merging.

## Initial implementation record

Implementation resumed from 9f7de2073dbbea09e472144835fc3c16d360ac55 on feat/pilot-foundation. The user approved continuation of the existing next-task contract. Direct git access failed DNS; the initial implementer recorded an isolated partial workspace with original modules verified by Git blob hash. Full repository verification ran on GitHub CI. No independent reviewer tool is available; report author self-review.

Ruling: use SQLite transactions rather than adding another custom lock-file/rename journal. This avoids duplicating the alert archive and keeps a separate private editorial record, not a substitute alert data pipeline. Durability remains limited to verified local process-interruption cases. Sources: SQLite atomiccommit.html and pragma.html#synchronous; Python sqlite3 documentation.

The initial implementation recorded 16 failing store cases against explicit not-implemented methods, then CLI failures and a final local set of 38 Python tests. This included two os._exit interruption cases and a competing-writer scenario. Its author review reproduced unsupported WAL mode being accepted; inspecting header bytes 18/19 before SQLite opening repaired that case. This local evidence belongs to the initial implementation, not to the later review continuation.

## Continuation review and completion

The next continuation found da698d4a12553bb2ecc9d1f65eba9ec3c6c8b9cb already ahead of the stale handoff and preserved it. Verify pilot #38 (36570324360, job109412408594) had completed successfully. The new review inspected the actual store/model/I/O/CLI and recovery tests through GitHub rather than recreating the ledger.

Ruling: preserve exact JSON identity, not Python numerical equality. True and 1 are different wire values and must not silently share guidance identity or a reconstructed event. A canonical-byte comparison uses the existing serialization contract; no schema migration or policy duplication is needed.

Four new tests at61a1816ab53226af46b1df2f470d26b06cee8964 cover type-exact guidance/replay, a lost acknowledgement of a reviewer decision and competing reviewer decisions. Run#39 (36571477262, job109416293174) genuinely reproduced three failed assertions in two methods: rehashed Boolean event/register versions were accepted, and a Boolean-to-integer guidance change passed identity comparison. All138Node tests and the otherPython tests passed; build/browser steps were skipped after thePython failure. The two reviewer-decision tests already passed and confirm holds are preserved.

Fix67a24917c44567ede4424f3d558453ad825df240 changes three comparisons to canonical bytes and adds two comments in the existing model/store. No test was removed or weakened. The exact diff fromda698d4 adds one112-line test file and modifies only those two product files. All existing source/public data, gate/extractor, frontend, dependencies and workflow files remain unchanged.

**Full GREEN: Verify pilot #40, run36572571183, job109419924407.** Code/test head67a24917c44567ede4424f3d558453ad825df240; temporary PR merge1e7b2d5f204d1e673832d82dc168afb75afa1a2a against unchangedmain. Complete logs read:138Node+230Python+18generated-output+74Chromium=460passing tests; Astro24files,0errors/0warnings/0hints;14HTMLpages plusbuild.json. Artifact11035336902, CI-reported ZIP SHA-2561418bce04d4b0866811f24deab5031e1bc603b211587c59882f17bcb5b886db3. No independent artifact download or visual audit in this backend review.

Relative to the communicated416-test baseline,40tests arrived with the ledger implementation and4were added in this review. The final documentation-only commit requires a separateCI check recorded inPR#1. Review is self-review, not independent approval. No full local clone/test pass is claimed for the continuation.

The ledger milestone is complete within its offline, bounded, non-approving contract. Real captured-page validation, approved context baselines and final guidance reconciliation are not completed by it. Next prioritize actual capturedHTML compatibility before more monitoring infrastructure; preserve original guidance and all pending holds. No merge, deployment, live source request or key-configuration recheck occurred.
