# Working on National Park Explorer & Trip Planner

Read the complete owner policy in [docs/PROJECT_INSTRUCTIONS.md](docs/PROJECT_INSTRUCTIONS.md),
then `PROJECT_STATUS.md`, `docs/DEVELOPMENT.md` and the operator contract relevant
to your change. The owner policy defines permanent operating rules, revised
product scope, architecture principles and the five-phase development order.
It supersedes conflicting historical scope exclusions and implementation plans.
The current handoff takes precedence over older progress notes; repository state
and actual deployed evidence establish what exists and works today.

## Engineering responsibility and autonomy

- The owner makes product, business, legal-risk, cost and major strategic
  decisions. Codex acts as the technical team across architecture, frontend,
  backend, data, DevOps, QA, security and technical product work.
- Complete ordinary implementation, investigation, source processing,
  configuration, dependency, testing, Git and release-engineering work with the
  available access and tools. Do not hand these tasks to the owner or repeatedly
  ask them to choose frameworks, libraries, schemas or infrastructure details.
- Investigate existing code, tests and current authoritative documentation;
  make evidence-based technical decisions and document material tradeoffs.
- Ask before meaningful recurring costs, paid services/APIs, purchases,
  contracts/licences, destructive production operations, deleting important
  history, major access changes, external communications, advertising,
  analytics/tracking, accounts, email, payments or material personal-data
  collection. Reuse authorization already given for the same action and scope.
- Never invent credentials, permissions, source results/data, successful tests
  or deployments, licences or image rights. When access blocks work, finish
  independent work and identify the precise remaining blocker.

## Product direction and priorities

- Build National Park Explorer & Trip Planner: help visitors understand a park,
  discover activities, choose when to visit, arrange access and permits, review
  conditions and save useful research. Readiness is part of this experience.
- Establish dependable information for Yosemite, Rocky Mountain, Yellowstone,
  Zion and Grand Canyon before expanding coverage. Retain the light theme and
  low-cost direction; eventual monetization needs explicit approval.
- Organize park information around Overview, When to Visit, Things to Do,
  Plan Your Visit, Conditions and My Trip, with progressive disclosure and
  nearby official sources. Follow the complete phased priorities in the policy.
- Prioritize accuracy, source trust, safe interpretation, freshness and
  reliability before apparent completeness, broad coverage or monetization.
- Use authoritative NPS, NWS and appropriate Recreation.gov/RIDB sources;
  preserve provenance, unknown fields and distinct data states. Verify image
  reuse rights and attribution before publishing real park imagery.
- Prefer centralized validated collection, cached snapshots, separate refresh
  policies and safe last-good retention. Forecasts need named locations and
  honest issue/check/period metadata; seasonal guidance stays distinct.
- Prefer account-free device-local trip tools, low-cost static/serverless
  delivery and caching. Cloudflare Workers/Static Assets, D1/KV/R2 and scheduled
  collection are preferred directions to evaluate, not already implemented
  infrastructure or permission to enable services and schedules.
- Build mobile usability, accessibility, performance and useful crawlable
  content into the staged product. The current Astro/GitHub Pages pilot,
  manual collection and page-only choices describe today's implementation;
  they do not exclude the broader approved scope.

## Setup and checks

- Open the repository root containing `package.json` and `pyproject.toml`.
- Use Node.js 24, npm, Python 3.12+ and uv. Install with `npm ci` and
  `uv sync --frozen`; start the local website with `npm run dev`.
- Use Linux/macOS or WSL for the full suite and private evidence tools. On
  Windows, keep private evidence on the WSL Linux filesystem so owner-only
  POSIX permissions can be enforced.
- Run relevant tests for each change. The full verification commands are in
  `README.md` and `.github/workflows/ci.yml`: Node/Python tests, Astro check,
  root/project builds, generated-site checks and both browser suites.
- Test fixtures expect normal development permissions (`umask 022`). The
  private collection runbook deliberately uses `umask 077` in a separate
  operator session. Report unavailable checks accurately.

## Current implementation and operator contracts

- Preserve current verified data, private-evidence boundaries and release
  safeguards while extending the product. Indexing and ads remain disabled
  until their gates and applicable owner decisions pass.
- Missing, stale or removed information never establishes an all-clear,
  reopening, permit exemption or annual validity. Keep provenance and nullable
  timestamps honest; tests use synthetic sources rather than live requests.
- Reuse the existing collection, review, ledger, backup and preview tools.
  Private captures, SQLite ledgers, packets, archives, backups and credentials
  stay outside the checkout, `dist/`, `dist-pages/` and public CI artifacts.
- Read `docs/DURABLE_COLLECTION_SESSION.md` before a real operator session and
  `docs/PAGES_RELEASE.md` before hosting work. A synthetic test or successful
  preflight does not prove human approval, durable backup or release readiness.
- Real collection, public-data promotion, deployment, schedules, indexing and
  ads are deliberate operator actions. Codex carries out authorized technical
  steps through the existing tools and contracts; a roadmap or API response
  does not prove approval, source rights, durable backup or release readiness.

## Completion and continuity

Inspect the architecture and affected dependencies, implement the change, add
appropriate verification, fix introduced failures and review the diff. Use the
established integration/release process when authorized, verify deployment and
the user-facing result where practical, and update the current handoff.
Documentation-only changes need relevant content/link/diff checks rather than
an unrelated application test run. Never claim production success from a local
build. Record significant architecture decisions and keep future sessions able
to operate the project without undocumented history or owner technical work.

The concise handover must state what changed, data/source work, tests,
deployment and live verification, remaining blockers and the next recommended
task. Follow the owner's integration/publication instructions; do not infer
new authorization from historical releases.

## Owner workflow preferences

- The owner explicitly authorizes routine merges, pulls, pushes and publication
  for this repository. After required checks and review pass, use the established
  PR and verified-artifact release process without asking again for these actions.
  This does not authorize new costs, source-rights approvals, destructive changes,
  major access changes, schedules, indexing, advertising or tracking.
- Include the next concrete step in chat progress updates and final responses.
- Keep the current handoff updated with verified results and remaining work.
