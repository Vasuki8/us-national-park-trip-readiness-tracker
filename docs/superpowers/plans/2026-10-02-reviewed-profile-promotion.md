# Reviewed profile promotion implementation

Engineering choices are delegated by the permanent owner policy. Implement the
[design](../specs/2026-10-02-reviewed-profile-promotion-design.md) in this chat.

- [x] Add strict public projection/rights contracts and cross-language tests.
- [x] Add immutable private reviewed bundles, explicit approval and recovery.
- [x] Prepare/check only the paired public-file patch with base/clock bindings.
- [x] Extend existing release gates and CLI with exact profile review/backup inputs.
- [x] Document operator boundaries and update the current handoff.
- [x] Complete relevant/full local verification and independent diff review.
- [ ] Create a PR, verify its exact head in supported CI and merge under standing authorization.

No real collection, key access, public data promotion or deployment is included.

Independent whole-diff review reproduced one conflicting-history issue. New
actual-collector regressions failed for both changed text and replacement IDs,
then passed after requiring the new observation to follow the last successful
public confirmation. Independent verification passed 19 release, 27 checkpoint,
46 readiness Python and 17 Node profile tests, with no remaining actionable issue.

Final local suite: 307 Node + 577 Python + 62 generated-site = 946 passing tests,
zero Astro diagnostics, both 14-page builds, strict changed-file TypeScript and
22 relative documentation links. Supported CI/browser verification is required
before the standing-authorized checked-head merge.
