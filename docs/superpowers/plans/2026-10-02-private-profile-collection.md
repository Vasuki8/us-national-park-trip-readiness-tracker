# Private profile collection implementation plan

> **For agentic workers:** Use independent transport implementation and whole-branch review; coordinate shared interfaces before editing. Steps use checkboxes.

**Goal:** Provide bounded NPS profile transport and private checkpoint/review tools.

**Architecture:** Separate source transport and immutable checkpoint lifecycle.
Reuse existing POSIX guards and profile normalization; no mutable store or public writer.

**Tech stack:** Python 3.12 standard library, unittest, WSL and existing CI.

**Spec:** `docs/superpowers/specs/2026-10-02-private-profile-collection-design.md`.

## Global constraints

- Five pilot codes only; synthetic requests and temporary private storage.
- No public data/frontend/dependency/workflow changes, live requests or release.
- 4,000,000-byte response, 20-second request, three attempts, 30-second wait.
- Private checkpoints/envelopes at most 8 MiB; POSIX owner-only files outside checkout.
- Preserve normalized hashes, source missingness, last-good records and nullable clocks.

## Review focus

- Credential echoes, duplicate JSON keys and malformed bytes must quarantine safely.
- Unsafe destinations and invalid/future input must fail before keys or requests.
- An existing output/lock must prevent collection and never be overwritten.
- Pre-install failures produce no checkpoint; post-install failures require offline verification.
- Offline verify/restore/export must never read keys, fetch sources or approve data.

## Task 1: Scoped transport

Files: `tracker/profile_transport.py`, `tests/test_profile_transport.py`,
`tracker/park_profiles.py` and its existing tests.

Interface: `request_profile_page(park_code, start, key, *, opener=None, sleep=time.sleep)`.

- [x] Write/observe failing synthetic tests for fixed endpoint, pilot/offset/key refusal,
  headers, no redirects, retries/limits, strict parsing, body/echo quarantine and safe errors.
- [x] Implement the narrow transport without live collection or alert transport changes.
- [x] Test/fix `collect_profile` handling explicit `ProfileError` from injected transport;
  preserve unexpected-exception propagation and validated last-good state.
- [x] Run focused tests and independently review the transport contract.

## Task 2: Private checkpoint lifecycle

Files: `tracker/profile_checkpoints.py`, `tests/test_profile_checkpoints.py`.

Interfaces: `validate_checkpoint(value)`, `verify_checkpoint(path)`,
`collect_checkpoint(destination, previous_path, now, fetch_for)`,
`restore_checkpoint(source, destination)`, `export_review_candidate(source, destination)`.

- [x] Write/observe failing tests for schema/hash/clocks, all-five scope and source failures,
  immutable file boundaries, owner-only files, locks, interruption, restore and private export.
- [x] Implement strict wrappers around existing POSIX primitives and final atomic creation.
- [x] Run focused WSL tests, review source/input immutability and interruption behavior.

## Task 3: Explicit CLI and operator contract

Files: `tracker/profile_stage.py`, `tests/test_profile_stage.py`,
`docs/PROFILE_COLLECTION.md`, `docs/DEVELOPMENT.md`, `PROJECT_STATUS.md`.

- [x] Write/observe failing CLI tests for --live/key requirements, safe argument/error output,
  offline operation, check-before-key/network ordering and accurate source outcome exits.
- [x] Implement commands using Tasks 1/2; reports contain metadata only.
- [x] Document backup/download/restore procedure and explicit review/publication limitations.
- [x] Update the current handoff with verified work and next real-source/text-review milestone.

## Task 4: Verification and integration

- [x] Run complete Node/Python tests, Astro check, both builds and generated checks.
- [x] Obtain whole-branch review, repair findings, confirm exact-head supported browser CI.
- [x] Merge under standing authorization, synchronize main and record final receipts.
- [x] Keep live artifact unchanged; report next concrete development step.

Completed checkpoint: local 893 tests passed, zero Astro diagnostics and both
14-page builds. Independent reviews verified the envelope-bound and Ctrl-C
repairs and found no remaining actionable issue. Exact-head
[Verify pilot #209](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37089413134)
passed all 1,015 tests, both browser suites and retention of all three
accessibility screenshots. [PR #9](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/9)
merged checked head `2f34eb7bbfc8c55443656e3b8c721ffc4bc1ac4c` as
`866dcbeb766592955aacce78a10898ddd65de76a`; their trees match. Public data and the
live artifact are unchanged. The current handoff records new text-use review,
separate profile approval/rights/backup coverage and public promotion as next work.
