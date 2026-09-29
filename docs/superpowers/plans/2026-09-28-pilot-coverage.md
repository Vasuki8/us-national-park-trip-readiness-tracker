# Five-park official planning checks implementation plan

> **For agentic workers:** Execute sequentially with superpowers:executing-plans and test-driven-development.

**Goal:** Replace generic coverage-gap links with useful park-specific official planning checks, without turning link review into a conditions determination.
**Architecture:** A strict build-time source-link register covers seven topics for every pilot. One static Astro component renders reviewed destinations and original checklist prompts. Existing alert/rule/coverage inputs remain unchanged.
**Tech stack:** Existing Astro, TypeScript, Node tests and Playwright; no new dependencies.
**Spec:** docs/superpowers/specs/2026-09-28-national-park-trip-readiness-design.md, sections 3, 5, 8, 12; PROJECT_STATUS.md at 1d96363, official-source coverage/acceptance audit fallback.

## Global constraints

No live ingestion, fee totals, activity-permit inference, conditions extraction, forecast generation, source-review timestamp refresh, scheduler, promotion, merge, deployment, indexing, ads or new services. Seven link-only categories: roads, facilities, camping, accessibility, fees, permits, weather. Link review dates describe the destination audit only. Preserve five-park inventory and existing date-check behavior. Use only reviewed park-specific NPS HTML URLs.

## Review focus

- A link review must not inflate stored rule or fresh feed coverage.
- Cross-park, non-HTTPS, credential-bearing, encoded/traversal or lookalike links must fail validation.
- Missing/duplicate categories and future/impossible link-review clocks must fail rather than silently disappear.
- Official pages may mix old/new or undated guidance; do not normalize transient conditions in this task.
- Cards, evidence links and checklist navigation must work without JavaScript, at 360px and at doubled text size.

## Task 1 — source audit and validated register

Files: data/planning-resources.json; scripts/validate-planning-resources.ts; tests/planning-resources.test.ts.
Interface: validatePlanningResources(value: unknown, parkCodes: string[], now: Date = new Date()) -> PlanningResource[]. Each resource contains park_code, category, url, source_title, check_prompt, link_reviewed_at. The envelope is exactly schema_version=1, review_scope=link_target_only, resources. Required category/park pairs appear exactly once; no operational value fields are accepted.
- [x] Read actual NPS destinations, retain canonical redirects and original link-only prompts.
- [x] Write positive/negative tests and observe a failing positive contract before implementation.
- [x] Implement strict validation with sanitized diagnostics and defensive copying; verify 12 unit tests locally.

## Task 2 — useful static cards and acceptance proof

Files: src/components/PlanningResources.astro; src/lib/data.ts; src/pages/parks/[slug].astro; src/components/Checklist.astro; tests/planning.browser.spec.ts; playwright.config.ts.
Interface: PlanningResources accepts parkName and validated resources for one park; uses #official-checks for checklist navigation. Metadata belongs to site snapshot identity, not alert/rule coverage or the date evaluator.
- [ ] Add and run failing browser assertions on existing pages before replacing cards.
- [ ] Render seven cards with Official link only labels, absolute link-review times and no conditions/price/forecast conclusion.
- [ ] Verify source hrefs, no-JavaScript links, checklist anchor, preserved date/alert coverage, 360px layout and doubled base text within the new component.
- [ ] Run full CI, review changed files, record acceptance gaps and update PROJECT_STATUS.md/PR #1.

## Execution ledger

Base 1d963637088077022cfc71ea25b1614aa67105ba; existing main a9d9c19 unchanged. Reran read-only preflight run 36481482091 (job 109224608968) at 2026-09-29T02:13:16Z: not_configured, gate_passed=false, checks=[], no requests/publication. The rerun used original preflight code 0dce38b, not current application head.

Direct container GitHub DNS fails. Use an isolated partial scratch workspace for new pure-Node checks; this is not a full clone. GitHub CI verifies the complete repository. The owner-approved continuation and existing specification supply the scope; no additional setup is needed for link-only development.
Pre-flight: Task 1 register feeds Task 2 component. No new browser data loader or alert/rule schema changes. Author self-review only; no independent reviewer tool is available.

Source review batch: 2026-09-29T02:18:54Z. All 35 selected NPS destinations opened and their topic/title reviewed through web retrieval; this is not a measurement of redirect-free HTTP reachability or live conditions. Unresolved attempted paths were replaced by reviewed actual destinations. No source media or source operational text copied; prompts are original and page titles identify the links.

Local RED: missing-module run, then explicit not_implemented stub caused five intended positive/diagnostic assertions to fail. GREEN: all 12 tests passed after validation implementation, Node 22.16.0. Stub was not committed. Browser RED is pending on this first test commit; no UI is implemented yet.
