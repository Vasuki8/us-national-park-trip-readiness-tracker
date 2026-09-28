# Project status and handoff

Updated: 2026-09-28. Milestone: **M1 foundation and source-coverage continuation CI-verified; full public M1 release incomplete**.

Repository: `Vasuki8/us-national-park-trip-readiness-tracker`.
Branch: `feat/pilot-foundation`. Draft pull request: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/1
The feature is not merged into main. No production deployment is configured.

## Owner-approved direction

AdSense-first eventual public product, light theme, no paid data dependency. Pilot five parks before expanding to 20. Trustworthy displayed data precedes traffic expansion, monetization and production indexing. No safety scores or all-clear claims.

## Implemented

- Static Astro directory and five park pages, search/state filters, responsive light design, source/methodology and disclosure pages: 14 HTML pages plus a build manifest.
- Three official-page-reviewed 2026 entry rules: Yosemite, Rocky Mountain rest-of-park, Rocky Mountain Bear Lake Road. Evidence includes an exact excerpt hash and review time, not a falsely attributed publisher-update time.
- General-entry source observations for Yellowstone, Zion and Grand Canyon, reviewed on 2026-09-28. Their cited statements do not publish effective date ranges, so they remain separate undated notes with null dates, not executable annual rules. All five parks now have stored entry-source evidence; only two have dated rules for the checker.
- One-day first-entry private-vehicle guidance with park-local date/time inputs, area-specific rules, annual bounds, conservative exact-end-time handling, unresolved exceptions, and seven-day review expiration.
- Data-derived homepage/directory coverage: stored reviews, dated rules, and recent successful feed checks are separate. Directory labels recalculate age in the browser. Stale, future, failed, quarantined, duplicate or conflicting metadata cannot appear as a recent successful check.
- Undated source panels work without JavaScript and explicitly warn that the statement is not a determination for the visitor's dates. The date evaluator remains unchanged and never consumes those notes. Notes are validated at the Astro server/build boundary and included in the site snapshot hash.
- Self-reported checklist that resets when trip details change. No persistent storage or booking verification.
- Five explicit never-collected alert snapshots; no live operational condition claims.
- Python/uv collector with bounded paging/retries, private API-key header, redirects disabled, source/park validation, suspicious-drop quarantine, retained last-good values and atomic writes.
- Read-only NPS preflight with bounded five-park requests, safe scalar diagnostics and no site-data writes. First run received no key; live integration is blocked, not verified.
- Read-only PR CI with core/data tests, Python tests, Astro type checking/build, static-output tests, and Chromium interaction/mobile/no-JavaScript checks.

## Verified implementation

Implementation head: `94bb7afdd1f2297f12a9a2f922ee57d5d71b1914`.
GitHub Actions run **36482305462**, Verify pilot #7, completed successfully on 2026-09-28. Job: **109130664677**.
Run: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36482305462

The runner tested GitHub's temporary PR merge ref `bfb3625d56678c3d49bf6bcaa638182d26100319`, combining that feature head with main `a9d9c19e8307828c5bdb6f331e24ca3fe7afffce`. This did not merge the feature into main.

| Check | Verified result |
|---|---|
| Reproducible installation, npm ci | Passed |
| Node core/data/toolchain/source-coverage tests | 50 passed; 0 failed |
| Python collector/transport/preflight tests | 31 passed |
| Astro check | 18 files; 0 errors, 0 warnings, 0 hints |
| Static build | 14 HTML pages and build.json generated |
| Static-output tests | 18 passed; 0 failed |
| Chromium browser tests | 10 passed |
| Total automated tests | 109 passed |

The four new browser cases verify five stored-source parks versus two dated-rule parks, all three undated observations remaining unresolved for a 2027 visit, expiry of directory labels on an already-open page, and useful undated evidence with JavaScript disabled. Existing filtering, annual/stale rules, area/time boundaries, checklist, 360px overflow and no-JavaScript cases remain green. No comprehensive accessibility audit or independent visual inspection is claimed.

Artifact: `pilot-verification`, ID `10996179659`, retained for seven days. It contains the static build, browser screenshots and package-lock.json.
Artifact: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36482305462/artifacts/10996179659
ZIP SHA-256: `97220df1c1910f4305228418b76f44df52496a696602d97cd771a188ce227363`.

This final handoff/README/plan update changes documentation only. Inspect the CI for later commits; the recorded result proves the implementation above, not future changes.

## Live-data gate: owner action required

The separate **Read-only NPS preflight** ran as run **36481482091**, job **109127917904**, at 2026-09-28T20:45:52Z. It reported `status: not_configured`, `gate_passed: false`, `publication_performed: false`, and `checks: []`. The job received an empty `NPS_API_KEY`. No API requests or snapshot writes occurred. A successful diagnostic workflow is not successful integration validation.

Add an owner-controlled NPS key as a repository Actions secret named **NPS_API_KEY** and rerun the existing read-only preflight. Do not paste the key into chat, a URL, source code or an issue. An empty injected value does not reveal whether a secret is absent, misnamed, environment-only or inaccessible. See `docs/NPS_PREFLIGHT.md` for configuration, bounds and interpretation.

## Review and execution record

New deterministic tests were first observed failing locally, then passing. The staged commit `0dce38b` intentionally included browser contracts before the UI: run 36481488060 passed all existing cases and failed exactly the four missing new browser features. After UI implementation, full run 36482305462 passed all 109 tests. No failing test was removed or weakened to obtain green status.

Author self-review checked type separation, build-time note validation, note-sensitive snapshot hashing, browser-only freshness metadata, safe text rendering, no-JavaScript evidence and secret/report boundaries. Comparison with base `83352bd` confirms no edits to the dated rules, existing evaluator, collector or production alert snapshots. No independent reviewer or field-conditions audit is claimed.

The prior foundation passed 79 tests at `7c39fb3` in run 36479129760 and again after its documentation update at `83352bd` in run 36479734880. Earlier repairs addressed invalid calendar normalization, cross-park URLs, incoherent timestamps, credential-like queries and missing Node types. Dependency locks were generated by real package tooling; no new dependencies were added in this continuation. Action-runtime deprecation and npm install-script warnings remain non-blocking maintenance items.

## Not activated / not verified

No production deployment, scheduled collection, advertising, analytics, accounts or paid service. No live NPS API request verified, retained real-response fixture, weather integration, complete roads/facilities coverage, durable observation/change history, publication/rollback validation or automatic editorial source-change monitoring. All pages remain noindex.

The additional general-entry reviews do not constitute complete readiness, permit or fee audits. Undated notes cannot establish access for a future date. The full source-backed M1 release remains incomplete.

## Next coherent task

Read PR #1, this handoff and the latest CI; preserve newer changes. Once the owner supplies the private Actions secret, rerun the read-only preflight, inspect actual API shapes privately and retain reviewed credential-free fixtures before publishing any collected records.

The next development task that does not need a key is durable evidence and change-history handling: retain accepted observations, distinguish additions/edits/removals, and preserve quarantine/last-good state without interpreting notice removal as reopening. Editorial source-change review must not automatically refresh a human review timestamp. Define and test those contracts before connecting a schedule. Homepage/directory coverage is now data-driven; do not redo that task.

After live compatibility, evidence retention and publication checks pass, validate production hosting and rollback. Indexing and advertising follow data quality, rights and publisher-disclosure gates. The PR remains draft and unmerged.

## Guardrails

Never advance publisher-update or publication timestamps from build/collection clocks. Never infer opening status from a missing/removed notice. Never carry a 2026 rule into 2027 or assign an annual validity range to an undated source. Never generate indexable pages merely to increase page count. Never put private keys into site JSON, generated JavaScript, commit messages or logs. Purchases, hosting-account changes, provider-agreement acceptance and monetization activation are outside this increment.
