# Approved guidance reconciliation implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add an explicit private reviewer action that turns a previously captured source context into a durable reviewed baseline and a reconciled guidance revision without touching public site data.

**Architecture:** Extend the existing hash-linked SQLite ledger with a `reconciliation` event. The event references an exact prior observation event and every active proposal for the affected source, validates a complete replacement guidance inventory through the existing TypeScript rules/notes validators and review-register policy, derives reviewed context baselines from the retained source evidence, and atomically advances the ledger's private guidance inventory. Later source observations use those stored baselines automatically. No command writes `data/`, publishes, deploys or removes unrelated holds.

**Tech Stack:** Existing Python 3.12/uv, Node 24 TypeScript bridges, SQLite ledger; no new packages.

**Spec:** `PROJECT_STATUS.md`, `docs/ENTRY_REVIEW_LEDGER.md`, `docs/ENTRY_SOURCE_EXTRACTION.md`, `docs/LIVE_ENTRY_COMPATIBILITY.md`.

## Global Constraints

- Public guidance, alert snapshots, histories and website output remain unchanged.
- Reconciliation is an explicit reviewer action; hashes, HTTP success and matching excerpts never approve content by themselves.
- Preserve old events, prior guidance, source capture clocks, reviewer identity/rationale and unresolved proposals.
- A source shared by multiple guidance records is reconciled as one source unit; no partial source-level approval.
- Rights metadata is not renewed by guidance reconciliation.
- Reviewed context comes only from an already committed successful extraction event.
- Expected-revision checks, exact retry behavior, event/ledger size limits and private-path controls remain.
- No network request, scheduler, deployment, indexing, advertising or public promotion in this plan.

## Review Focus

- A reconciliation that omits one active proposal for the same source must fail rather than partially clear the source hold.
- A stale source observation must not reconcile guidance after a newer proposal exists.
- New guidance whose excerpt is absent or duplicated in the selected retained context must fail.
- Unaffected records and rights-review metadata must remain byte-identical.
- After reconciliation, later observations must use the ledger-approved baseline and cannot replace it with caller-supplied context.

---

### Task 1: Reconciliation policy bridge

**Files:**
- Create: `scripts/entry-reconcile-bridge.ts`
- Test: `tests/entry-reconcile.test.ts`

**Interfaces:**
- Consumes: current complete guidance records, current review register, proposal IDs, replacement records, reviewer review timestamp.
- Produces: validated remaining register, affected guidance IDs and affected source URLs.

- [x] Write failing Node tests for complete-source proposal selection, unchanged unrelated records/rights, full rule/note validation and safe failures.
- [x] Run the tests and observe missing bridge behavior.
- [x] Implement the bridge using `validateEntryReview`, `validateRule` and `validateEntryNotes`.
- [x] Run targeted Node tests to green.

### Task 2: Ledger reconciliation event and persistent baselines

**Files:**
- Modify: `tracker/entry_review_model.py`
- Modify: `tracker/entry_review_store.py`
- Modify: `tracker/entry_review_cli.py`
- Test: `tests/test_entry_review_reconciliation.py`
- Test: `tests/test_entry_review_cli.py`

**Interfaces:**
- Consumes: `reconcile` request with `source_event_revision proposal_ids reviewer rationale reviewed_at records`.
- Produces: immutable `reconciliation` event, updated private guidance inventory, active reviewed context baselines, remaining proposal register and safe summary counts.

- [x] Write failing tests for explicit reconciliation, source-event binding, partial/stale proposal refusal, excerpt-in-context validation, replay, and CLI redaction.
- [x] Run targeted Python tests and observe the missing event/command failures.
- [x] Implement baseline derivation from the referenced retained extraction, atomic event replay, state updates and CLI command.
- [x] Make subsequent observations consume stored baselines and reject caller replacement of them.
- [x] Run targeted Python/Node integration tests to green.

### Task 3: Regression, documentation and handoff

**Files:**
- Modify: `docs/ENTRY_REVIEW_LEDGER.md`
- Create: `docs/GUIDANCE_RECONCILIATION.md`
- Modify: `PROJECT_STATUS.md`
- Modify: PR #1 description.

- [x] Run complete repository CI and inspect logs.
- [x] Self-review the branch for silent hold clearing, old/new evidence loss and accidental public writes.
- [x] Document remaining human-review, rights, storage and publication gates.
- [x] Update handoff and PR; keep draft/unmerged.


## Execution record

Implementation began from `aad4c3702dbeb21e21f40ce27447628d13e83da6` on the existing draft feature branch. Tests were written before production code.

- RED #47 (`36579697560`): Node failed because `reconcileEntryReview` did not exist.
- First implementation added the TypeScript reconciliation policy/bridge and Python ledger/CLI event.
- Python integration exposed a real clock-model conflict between legacy baselines and explicit capture-then-review flow. Schema-v2 baselines preserve the new order without weakening v1.
- Author self-review added and observed RED cases for exact schema preservation (#51), latest clean capture with sticky older hold (#53), and preservation of unrelated reviewed baselines (#56). Each was fixed before the next full run.
- Review focus also includes zero/multiple approved excerpt matches, partial source proposal sets, stale source events, rights immutability, exact retries and caller baseline override.

**Full GREEN: Verify pilot #57, run `36582856143`, job `109455297528`, code/test head `8f5034690e58ea766adf2044ee986080988869d0`.** 144 Node + 267 Python + 18 generated-output + 74 Chromium = **503 passing tests**. Astro checked 24 files with zero errors/warnings/hints; production remained 14 HTML pages plus `build.json`.

Artifact ID `11040527008`; CI ZIP SHA-256 `cffb57874750dff951ff6aad5423b195b3e89fa712e20c2248f6e34a275c7cae`.

Review was author self-review because no independent reviewer/subagent tool is available. No real NPS context was approved, no public data was changed, and no merge/deployment occurred.
