# Reviewed profile promotion implementation

Engineering choices are delegated by the permanent owner policy. Implement the
[design](../specs/2026-10-02-reviewed-profile-promotion-design.md) in this chat.

- [x] Add strict public projection/rights contracts and cross-language tests.
- [x] Add immutable private reviewed bundles, explicit approval and recovery.
- [x] Prepare/check only the paired public-file patch with base/clock bindings.
- [x] Extend existing release gates and CLI with exact profile review/backup inputs.
- [x] Document operator boundaries and update the current handoff.
- [x] Complete relevant/full local verification and independent diff review.
- [x] Create a PR, verify its exact head in supported CI and merge under standing authorization.

No real collection, key access, public data promotion or deployment is included.

Independent whole-diff review reproduced one conflicting-history issue. New
actual-collector regressions failed for both changed text and replacement IDs,
then passed after requiring the new observation to follow the last successful
public confirmation. Independent verification passed 19 release, 27 checkpoint,
46 readiness Python and 17 Node profile tests, with no remaining actionable issue.

Final local suite: 307 Node + 577 Python + 62 generated-site = 946 passing tests,
zero Astro diagnostics, both 14-page builds, strict changed-file TypeScript and
22 relative documentation links.

[PR #10](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/10)
checked head `39b3085e647d32ebb409e94a9aa3e0cdafe24d2e` passed
[Verify pilot #212](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37092715042),
job `111116255685`: all 1,068 tests, zero Astro diagnostics, both 14-page builds,
108 root + 14 project-path browser cases and three retained screenshots.
Independent CI audit passed. The standing-authorized merge is
`d7d8e16a157fb8040fb34a933a82264c386f5f59`; its tree matches the checked head.
The current handoff records the unchanged-dependency advisory assessment and
follow-up; no vulnerability fix, real operator work or deployment is claimed.
