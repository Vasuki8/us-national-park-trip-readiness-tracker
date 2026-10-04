# Reviewed Activity Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Track steps below.

**Goal:** Add an exact, reviewed minimal public activity contract with explicit withholding while preserving private originals and legacy approvals.

**Architecture:** Version-dispatch the existing paired contract. Pure catalog validation/projection is separate from private approval/promotion; TypeScript mirrors the same build boundary.

**Tech Stack:** Existing Python 3.12+, Node.js 24, TypeScript, Astro, frozen uv/npm dependencies; no new package.

**Spec:** ../specs/2026-10-04-reviewed-activity-catalog-design.md

## Global constraints

- Synthetic source requests only; no real rights decisions, approvals, source data writes or deployment.
- Private output stays in owner-only external POSIX temporary storage; source evidence and clocks stay unchanged.
- Existing v1 contract/recovery stays valid; v2 requires exact disposition/view/rights bindings.
- Shared managed worktree, disjoint file ownership; parent alone handles Git integration.

## Review focus

- Public strings or patch bytes accidentally retain synthetic quotation/contact/tracking markers: task 1/2 exclusion tests.
- Entire feed withheld is confused with empty source: tasks 1/2 source/published/withheld count tests.
- Retained degraded source changes through editorial review: task 2 original hash/observation and success-clock refusal.
- Rehashed altered source/view/rights bypass exact binding: tasks 1/2 independent corruption tests.
- Python/TypeScript Unicode and microsecond clocks diverge: task 3 cross-language fixtures and boundary tests.

### Task 1: Pure catalog and exact public rights

Files: tracker/activity_catalog.py; dispatch-only changes in tracker/activity_public.py; tests/test_activity_catalog.py.
Interfaces: spec's four pure functions; existing ActivityPublicError/canonical_activity_json/activity_digest; project_checkpoint(value, dispositions=None) keeps legacy default.
- [x] Write synthetic behavior tests before implementation and record expected red failures.
- [x] Implement exact private dispositions, narrow public projection, catalog and rights validation per spec.
- [x] Run focused catalog and legacy public/checkpoint tests; self-review and independent task review.

### Task 2: Private lifecycle, source continuity and readiness

Files: tracker/activity_release.py; tracker/release_readiness.py; tests/test_activity_catalog_release.py.
Consumes task 1 projection/validators. Produces optional dispositions arguments, v2 bound bundle regeneration/recovery, source-metadata promotion continuity and separate readiness counts.
- [x] Write failing lifecycle/CLI/CAS/continuity/readiness tests using synthetic v2 fixtures.
- [x] Implement v2 approval/verification with all input-overlap guards and review-clock ordering.
- [x] Adapt promotion source comparison for version transitions/editorial withholding while preserving v1 strict behavior.
- [x] Exercise real private temp verify/restore/paired patch/recheck, and full affected legacy release/readiness tests.

### Task 3: TypeScript parity and build gates

Files: scripts/validate-park-activities.ts; optional focused scripts/validate-activity-catalog.ts; tests/activity-catalog.test.ts; test fixture bridge if needed.
Consumes schema spec, Python outputs and existing canonical/clock/official-url primitives. Produces validatePublicActivities/validateActivityRights version dispatch and a matching exported catalog type.
- [x] Write expected failing v2 public-pair tests, including marker exclusion, rehash tampering, Unicode/clock and incomplete-pair refusal.
- [x] Implement narrow catalog/rights validation without reinterpreting v1 or changing canonical/file guards.
- [x] Run focused parity/legacy activity/build-gate tests and strict TypeScript checks; independent task review.

### Task 4: Whole-change verification and integration

Files: docs/ACTIVITY_PROMOTION.md; docs/DEVELOPMENT.md; README.md; PROJECT_STATUS.md; this plan's completion ledger.
- [x] Review all tasks against spec and record material rulings/fixes.
- [x] Run full Python and Node suites, Astro check, both builds and generated-site suites; inspect all failures.
- [x] Complete independent Python/lifecycle and TypeScript/documentation review; fix findings with regressions.
- [ ] Create/attach PR, inspect exact CI head/base/tree, complete browser suites and artifact evidence.
- [ ] Merge under standing authorization; update handoff through the checked PR path, verify local/remote main, preserve worktree deliverables before native archive.
- [ ] Report actual data, tests, deployment limits, blockers and next concrete real catalog-review task.
