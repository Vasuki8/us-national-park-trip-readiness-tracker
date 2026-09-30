# Working on ParkReadiness

Read `PROJECT_STATUS.md` for current progress and next priorities, then
`docs/DEVELOPMENT.md` and the operator contract relevant to your change. Older
implementation notes in the status file are historical; the current handoff
at the top takes precedence.

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

## Product and data contracts

- Preserve the five-park pilot, light theme, free data dependencies and eventual
  AdSense direction. Indexing and ads remain disabled until their gates pass.
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
  ads are deliberate operator actions, separate from ordinary code development.

Update the current handoff when behavior or the next milestone changes. Record
what was verified and what remains pending. Follow the user's instructions for
branch integration and publishing; do not infer authorization from old history.
