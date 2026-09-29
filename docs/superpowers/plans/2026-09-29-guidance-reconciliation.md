# Approved guidance reconciliation implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

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

- [ ] Write failing Node tests for complete-source proposal selection, unchanged unrelated records/rights, full rule/note validation and safe failures.
- [ ] Run the tests and observe missing bridge behavior.
- [ ] Implement the bridge using `validateEntryReview`, `validateRule` and `validateEntryNotes`.
- [ ] Run targeted Node tests to green.

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

- [ ] Write failing tests for explicit reconciliation, source-event binding, partial/stale proposal refusal, excerpt-in-context validation, replay, and CLI redaction.
- [ ] Run targeted Python tests and observe the missing event/command failures.
- [ ] Implement baseline derivation from the referenced retained extraction, atomic event replay, state updates and CLI command.
- [ ] Make subsequent observations consume stored baselines and reject caller replacement of them.
- [ ] Run targeted Python/Node integration tests to green.

### Task 3: Regression, documentation and handoff

**Files:**
- Modify: `docs/ENTRY_REVIEW_LEDGER.md`
- Create: `docs/GUIDANCE_RECONCILIATION.md`
- Modify: `PROJECT_STATUS.md`
- Modify: PR #1 description.

- [ ] Run complete repository CI and inspect logs.
- [ ] Self-review the branch for silent hold clearing, old/new evidence loss and accidental public writes.
- [ ] Document remaining human-review, rights, storage and publication gates.
- [ ] Update handoff and PR; keep draft/unmerged.
